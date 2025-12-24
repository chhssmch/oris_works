from models.item import Item

class ItemService:
    @staticmethod
    def create_item(user_id, title, description, category, condition, image_urls=None):
        errors = []

        if not title or len(title.strip()) < 3:
            errors.append("Название должно быть не менее 3 символов")

        if not description or len(description.strip()) < 10:
            errors.append("Описание должно быть не менее 10 символов")

        if not category:
            errors.append("Укажите категорию")

        if not condition:
            errors.append("Укажите состояние товара")

        if errors:
            return None, errors

        try:
            item = Item.create(title, description, category, condition, user_id, image_urls)
            return item, []
        except Exception as e:
            return None, [f"Ошибка при создании товара: {str(e)}"]

    @staticmethod
    def update_item(item_id, user_id, **kwargs):
        item = Item.get_by_id(item_id)

        if not item:
            return None, ["Товар не найден"]

        if item.owner_id != user_id:
            return None, ["Вы не можете редактировать этот товар"]

        if item.status != 'available':
            return None, ["Нельзя редактировать товар, который не доступен для обмена"]

        try:
            item.update(**kwargs)
            return item, []
        except Exception as e:
            return None, [f"Ошибка при обновлении товара: {str(e)}"]

    @staticmethod
    def delete_item(item_id, user_id):
        item = Item.get_by_id(item_id)

        if not item:
            return False, ["Товар не найден"]

        if item.owner_id != user_id:
            return False, ["Вы не можете удалить этот товар"]

        try:
            item.delete()
            return True, []
        except Exception as e:
            return False, [f"Ошибка при удалении товара: {str(e)}"]

    @staticmethod
    def get_available_items(category=None, limit=50, offset=0):
        return Item.get_all(category=category, status='available', limit=limit, offset=offset)

    @staticmethod
    def get_user_items(user_id):
        return Item.get_by_owner(user_id)