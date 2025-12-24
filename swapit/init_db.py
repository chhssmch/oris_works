import mysql.connector
from config import Config
import os

def init_database():
    with open('database/schema.sql', 'r', encoding='utf-8') as f:
        sql_script = f.read()

    connection = mysql.connector.connect(
        host=Config.DATABASE_HOST,
        user=Config.DATABASE_USER,
        password=Config.DATABASE_PASSWORD
    )

    cursor = connection.cursor()

    try:
        cursor.execute("DROP DATABASE IF EXISTS swapit_db")
        cursor.execute("CREATE DATABASE swapit_db")
        cursor.execute("USE swapit_db")

        for statement in sql_script.split(';'):
            if statement.strip() and not statement.strip().lower().startswith(('create database', 'use ')):
                cursor.execute(statement)

        connection.commit()
        print("База данных успешно инициализирована")

        add_test_data()

    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()


def add_test_data():
    from models.user import User
    from models.item import Item

    test_users = [
        ('alexey123', 'alexey@example.com', 'password123', 'Алексей Иванов', '+79161234567', 'Москва'),
        ('maria_meow', 'maria@example.com', 'password123', 'Мария Петрова', '+79162345678', 'Санкт-Петербург'),
        ('dmitry_roblox', 'dmitry@example.com', 'password123', 'Дмитрий Сидоров', '+79163456789', 'Казань')
    ]

    for username, email, password, full_name, phone, city in test_users:
        if not User.get_by_username(username):
            User.create(username, email, password, full_name, phone, city)
            print(f"Создан пользователь: {username}")

    test_items = [
        ('iPhone 12 Pro', 'Айфон в отличном состоянии, аккумулятор 96%', 'Электроника', 'excellent', 'alexey123', ['iphone.jpg', 'iphone2.jpg']),
        ('Ноутбук Dell XPS 13', 'Рабочий ноутбук, 16 ГБ ОЗУ', 'Электроника', 'good', 'alexey123', ['laptop.jpg']),
        ('Куртка зимняя женская', 'Теплая куртка, размер M ', 'Одежда', 'good', 'maria_meow', ['jacket.jpg']),
        ('Книга "Мастер и Маргарита"', 'Издание 2015 года, открывалась дважды', 'Книги', 'excellent', 'maria_meow', ['book.jpg']),
        ('Велосипед горный', 'Пишите за подробностями, состояние хорошее, нужно смазать цепь', 'Спорт', 'satisfactory', 'dmitry_roblox', ['bike.jpg']),
        ('Настольная лампа', 'Светодиодная, с регулировкой яркости, теплый и холодный свет', 'Другое', 'new', 'dmitry_roblox', ['lamp.jpg'])
    ]

    for item_data in test_items:
        title, description, category, condition, owner_username, image_filenames = item_data    
        owner = User.get_by_username(owner_username)
        if owner:
            from models import Database
            query = "SELECT id FROM items WHERE title = %s AND owner_id = %s"
            existing = Database.execute_query(query, (title, owner.id), fetchone=True)

            if not existing:
                image_urls = []
                for filename in image_filenames:
                    image_urls.append(f"uploads/items/{filename}")

                Item.create(
                    title=title,
                    description=description,
                    category=category,
                    condition=condition,
                    owner_id=owner.id,
                    image_urls=image_urls
                )
                print(f"Создан товар: {title} с изображениями: {image_filenames}")


if __name__ == '__main__':
    print("Инициализация базы данных SwapIt...")
    init_database()