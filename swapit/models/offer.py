from datetime import datetime
from . import Database

class Offer:
    def __init__(self, id=None, sender_id=None, receiver_id=None,
                 sender_item_id=None, receiver_item_id=None, status=None,
                 message=None, created_at=None, updated_at=None,
                 sender_username=None, receiver_username=None,
                 sender_item_title=None, receiver_item_title=None):
        self.id = id
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.sender_item_id = sender_item_id
        self.receiver_item_id = receiver_item_id
        self.status = status or 'pending'
        self.message = message
        self.created_at = created_at
        self.updated_at = updated_at
        self.sender_username = sender_username
        self.receiver_username = receiver_username
        self.sender_item_title = sender_item_title
        self.receiver_item_title = receiver_item_title

    @classmethod
    def create(cls, sender_id, receiver_id, sender_item_id, receiver_item_id, message=None):
        query = """
        INSERT INTO offers (sender_id, receiver_id, sender_item_id, receiver_item_id, message)
        VALUES (%s, %s, %s, %s, %s)
        """

        offer_id = Database.execute_query(
            query,
            (sender_id, receiver_id, sender_item_id, receiver_item_id, message)
        )

        return cls.get_by_id(offer_id)

    @classmethod
    def get_by_id(cls, offer_id):
        query = """
        SELECT o.*, 
               s.username as sender_username,
               r.username as receiver_username,
               si.title as sender_item_title,
               ri.title as receiver_item_title
        FROM offers o
        JOIN users s ON o.sender_id = s.id
        JOIN users r ON o.receiver_id = r.id
        JOIN items si ON o.sender_item_id = si.id
        JOIN items ri ON o.receiver_item_id = ri.id
        WHERE o.id = %s
        """

        result = Database.execute_query(query, (offer_id,), fetchone=True)
        return cls(**result) if result else None

    @classmethod
    def get_by_user(cls, user_id, role='all'):
        query = """
        SELECT o.*, 
               s.username as sender_username,
               r.username as receiver_username,
               si.title as sender_item_title,
               ri.title as receiver_item_title
        FROM offers o
        JOIN users s ON o.sender_id = s.id
        JOIN users r ON o.receiver_id = r.id
        JOIN items si ON o.sender_item_id = si.id
        JOIN items ri ON o.receiver_item_id = ri.id
        WHERE 1=1
        """

        params = []

        if role == 'sent':
            query += " AND o.sender_id = %s"
            params.append(user_id)
        elif role == 'received':
            query += " AND o.receiver_id = %s"
            params.append(user_id)
        else:
            query += " AND (o.sender_id = %s OR o.receiver_id = %s)"
            params.extend([user_id, user_id])

        query += " ORDER BY o.created_at DESC"

        results = Database.execute_query(query, tuple(params), fetchall=True)
        return [cls(**result) for result in results] if results else []

    @classmethod
    def get_user_completed_offers_count(cls, user_id):
        query = """
        SELECT COUNT(*) as count
        FROM offers 
        WHERE (sender_id = %s OR receiver_id = %s) 
        AND status = 'completed'
        """
        
        result = Database.execute_query(query, (user_id, user_id), fetchone=True)
        return result['count'] if result else 0

    def update_status(self, status):
        query = "UPDATE offers SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        Database.execute_query(query, (status, self.id), commit=True)
        self.status = status
        self.updated_at = datetime.now()

        if status == 'accepted':
            query = "UPDATE items SET status = 'reserved' WHERE id IN (%s, %s)"
            Database.execute_query(query, (self.sender_item_id, self.receiver_item_id), commit=True)

    def add_message(self, user_id, message):
        query = """
        INSERT INTO offer_messages (offer_id, user_id, message)
        VALUES (%s, %s, %s)
        """

        Database.execute_query(query, (self.id, user_id, message))

    @staticmethod
    def get_messages(offer_id):
        query = """
        SELECT om.*, u.username
        FROM offer_messages om
        JOIN users u ON om.user_id = u.id
        WHERE offer_id = %s
        ORDER BY om.created_at
        """

        return Database.execute_query(query, (offer_id,), fetchall=True)

    @classmethod
    def count_pending_for_user(cls, user_id):
        query = """
        SELECT COUNT(*) as count 
        FROM offers 
        WHERE receiver_id = %s AND status = 'pending'
        """
        result = Database.execute_query(query, (user_id,), fetchone=True)
        return result['count'] if result else 0

    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'sender_item_id': self.sender_item_id,
            'receiver_item_id': self.receiver_item_id,
            'status': self.status,
            'message': self.message,
            'created_at': self.created_at,
            'sender_username': self.sender_username,
            'receiver_username': self.receiver_username,
            'sender_item_title': self.sender_item_title,
            'receiver_item_title': self.receiver_item_title
        }