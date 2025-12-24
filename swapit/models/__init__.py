import mysql.connector
from config import Config

class Database:
    @classmethod
    def get_connection(cls):
        return mysql.connector.connect(
            host=Config.DATABASE_HOST,
            user=Config.DATABASE_USER,
            password=Config.DATABASE_PASSWORD,
            database=Config.DATABASE_NAME
        )

    @classmethod
    def execute_query(cls, query, params=None, fetchone=False, fetchall=False, commit=True):
        connection = cls.get_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute(query, params or ())

            if fetchone:
                result = cursor.fetchone()
            elif fetchall:
                result = cursor.fetchall()
            else:
                result = cursor.lastrowid

            if commit:
                connection.commit()

            return result
        except Exception as e:
            print(f"SQL Error: {e}")

            if 'connection' in locals() and connection.is_connected():
                connection.rollback()
            raise e
            
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'connection' in locals() and connection.is_connected():
                connection.close()
