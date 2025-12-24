import hashlib
import secrets
from datetime import datetime
from . import Database

class User:
    def __init__(self, id=None, username=None, email=None, password_hash=None,
                 full_name=None, phone=None, city=None, created_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.full_name = full_name
        self.phone = phone
        self.city = city
        self.created_at = created_at

    @staticmethod
    def hash_password(password, salt=None):
        if salt is None:
            salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256()
        hash_obj.update(f"{salt}{password}".encode('utf-8'))
        return f"{salt}${hash_obj.hexdigest()}"

    @staticmethod
    def verify_password(stored_hash, password):
        try:
            if not stored_hash or not password:
                return False
                
            parts = stored_hash.split('$')
            if len(parts) != 2:
                return False
                
            salt, _ = parts
            new_hash = User.hash_password(password, salt)
            return stored_hash == new_hash
            
        except Exception:
            return False

    @classmethod
    def create(cls, username, email, password, full_name=None, phone=None, city=None):
        password_hash = cls.hash_password(password)

        query = """
        INSERT INTO users (username, email, password_hash, full_name, phone, city)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        user_id = Database.execute_query(
            query,
            (username, email, password_hash, full_name, phone, city)
        )

        return cls.get_by_id(user_id)
        
    @classmethod
    def authenticate(cls, username_or_email, password):
        is_email = '@' in username_or_email
        
        query = """
        SELECT id, username, email, password_hash, full_name, phone, city, created_at 
        FROM users 
        WHERE {} = %s
        """.format('email' if is_email else 'username')
        
        result = Database.execute_query(
            query,
            (username_or_email,),
            fetchone=True
        )
        
        if not result:
            return None
            
        user = cls(**result)
        
        if not user or not user.password_hash:
            return None
            
        if cls.verify_password(user.password_hash, password):
            return user
            
        return None

    @classmethod
    def get_by_id(cls, user_id):
        query = "SELECT id, username, email, password_hash, full_name, phone, city, created_at FROM users WHERE id = %s"
        result = Database.execute_query(query, (user_id,), fetchone=True)
        return cls(**result) if result else None

    @classmethod
    def get_by_username(cls, username):
        query = "SELECT id, username, email, password_hash, full_name, phone, city, created_at FROM users WHERE username = %s"
        result = Database.execute_query(query, (username,), fetchone=True)
        return cls(**result) if result else None

    @classmethod
    def get_by_email(cls, email):
        query = "SELECT id, username, email, password_hash, full_name, phone, city, created_at FROM users WHERE email = %s"
        result = Database.execute_query(query, (email,), fetchone=True)
        return cls(**result) if result else None

    def update(self, full_name=None, phone=None, city=None):
        query = """
        UPDATE users 
        SET full_name = COALESCE(%s, full_name),
            phone = COALESCE(%s, phone),
            city = COALESCE(%s, city),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """

        Database.execute_query(
            query,
            (full_name, phone, city, self.id)
        )

        if full_name: self.full_name = full_name
        if phone: self.phone = phone
        if city: self.city = city

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'city': self.city,
            'created_at': self.created_at
        }