from datetime import datetime
from . import Database

class Item:
    def __init__(self, id=None, title=None, description=None, category=None,
                 condition=None, status=None, owner_id=None, created_at=None,
                 updated_at=None, owner_username=None, images=None):
        self.id = id
        self.title = title
        self.description = description
        self.category = category
        self.condition = condition
        self.status = status or 'available'
        self.owner_id = owner_id
        self.created_at = created_at
        self.updated_at = updated_at
        self.owner_username = owner_username
        self.images = images or []
        
    def condition_display(self):
        condition_map = {
            'new': 'Новый',
            'excellent': 'Отличное',
            'good': 'Хорошее',
            'satisfactory': 'Удовлетворительное',
            'broken': 'Требует ремонта'
        }
        return condition_map.get(self.condition, self.condition)

    @classmethod
    def create(cls, title, description, category, condition, owner_id, image_urls=None):
        query = """
        INSERT INTO items (title, description, category, `condition`, owner_id)
        VALUES (%s, %s, %s, %s, %s)
        """

        item_id = Database.execute_query(
            query,
            (title, description, category, condition, owner_id)
        )

        if image_urls:
            for i, url in enumerate(image_urls):
                is_main = (i == 0)
                cls.add_image(item_id, url, is_main)

        return cls.get_by_id(item_id)

    @classmethod
    def get_item_images(cls, item_id):
        query = """
        SELECT id, image_url, is_main
        FROM item_images
        WHERE item_id = %s
        ORDER BY is_main DESC, id
        """
        return Database.execute_query(query, (item_id,), fetchall=True)

    @classmethod
    def get_user_available_items(cls, user_id):
        query = """
        SELECT i.*, u.username as owner_username
        FROM items i
        JOIN users u ON i.owner_id = u.id
        WHERE i.owner_id = %s 
        AND i.status = 'available'
        ORDER BY i.created_at DESC
        """
        
        results = Database.execute_query(query, (user_id,), fetchall=True)
        items = []
        for result in results:
            item = cls(**result)
            image_rows = cls.get_item_images(item.id)
            item.images = [img['image_url'] for img in image_rows] if image_rows else []
            items.append(item)
        return items

    @classmethod
    def get_by_id(cls, item_id):
        query = """
        SELECT i.*, u.username as owner_username
        FROM items i
        JOIN users u ON i.owner_id = u.id
        WHERE i.id = %s
        """

        result = Database.execute_query(query, (item_id,), fetchone=True)
        if not result:
            return None

        item = cls(**result)
        image_rows = cls.get_images(item_id)
        item.images = [img['image_url'] for img in image_rows] if image_rows else []
        return item

    @classmethod
    def get_all(cls, category=None, status=None, limit=50, offset=0):
        query = """
            SELECT i.*, u.username as owner_username
            FROM items i
            JOIN users u ON i.owner_id = u.id
            WHERE 1=1
        """
        params = []
        if category:
            query += " AND i.category = %s"
            params.append(category)
        if status:
            query += " AND i.status = %s"
            params.append(status)
        query += " ORDER BY i.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        results = Database.execute_query(query, tuple(params), fetchall=True)
        items = []
        for result in results:
            item = cls(**result)
            image_rows = cls.get_images(item.id)
            item.images = [img['image_url'] for img in image_rows] if image_rows else []
            items.append(item)
            
        return items

    @classmethod
    def get_by_owner(cls, owner_id):
        query = """
        SELECT i.*, u.username as owner_username
        FROM items i
        JOIN users u ON i.owner_id = u.id
        WHERE i.owner_id = %s
        ORDER BY i.created_at DESC
        """

        results = Database.execute_query(query, (owner_id,), fetchall=True)

        items = []
        for result in results:
            item = cls(**result)
            image_rows = cls.get_images(item.id)
            item.images = [img['image_url'] for img in image_rows] if image_rows else []
            items.append(item)

        return items

    @staticmethod
    def add_image(item_id, image_url, is_main=False):
        if is_main:
            query = "UPDATE item_images SET is_main = FALSE WHERE item_id = %s"
            Database.execute_query(query, (item_id,))

        query = """
        INSERT INTO item_images (item_id, image_url, is_main)
        VALUES (%s, %s, %s)
        """
        Database.execute_query(query, (item_id, image_url, is_main))

    @staticmethod
    def get_images(item_id):
        query = """
        SELECT * FROM item_images 
        WHERE item_id = %s 
        ORDER BY is_main DESC, created_at
        """
        return Database.execute_query(query, (item_id,), fetchall=True)

    def update(self, title=None, description=None, category=None,
               condition=None, status=None):
        query = """
        UPDATE items 
        SET title = COALESCE(%s, title),
            description = COALESCE(%s, description),
            category = COALESCE(%s, category),
            `condition` = COALESCE(%s, `condition`),
            status = COALESCE(%s, status),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """

        Database.execute_query(
            query,
            (title, description, category, condition, status, self.id)
        )

        if title: self.title = title
        if description: self.description = description
        if category: self.category = category
        if condition: self.condition = condition
        if status: self.status = status

    def delete(self):
        query = "DELETE FROM items WHERE id = %s"
        Database.execute_query(query, (self.id,))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'condition': self.condition,
            'status': self.status,
            'owner_id': self.owner_id,
            'owner_username': self.owner_username,
            'created_at': self.created_at,
            'images': self.images
        }
        
    @classmethod
    def get_user_items(cls, user_id, status='available'):
        """
        Get all items belonging to a specific user
        
        Args:
            user_id (int): The ID of the user
            status (str): Filter by item status (default: 'available')
            
        Returns:
            list: List of Item objects belonging to the user
        """
        query = """
        SELECT i.*, u.username as owner_username
        FROM items i
        JOIN users u ON i.owner_id = u.id
        WHERE i.owner_id = %s AND i.status = %s
        ORDER BY i.created_at DESC
        """

        results = Database.execute_query(query, (user_id, status), fetchall=True)

        items = []
        for result in results:
            item = cls(**result)
            image_rows = cls.get_images(item.id)
            item.images = [img['image_url'] for img in image_rows] if image_rows else []
            items.append(item)

        return items