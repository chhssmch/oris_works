from models.offer import Offer
from models.item import Item


class OfferService:
    @staticmethod
    def create_offer(sender_id, receiver_item_id, sender_item_id=None, message=None):
        errors = []

        receiver_item = Item.get_by_id(receiver_item_id)
        if not receiver_item:
            errors.append("Товар для обмена не найден")

        sender_item = None
        if sender_item_id:
            sender_item = Item.get_by_id(sender_item_id)
            if not sender_item:
                errors.append("Ваш товар не найден")
            elif sender_item.owner_id != sender_id:
                errors.append("Вы не владеете этим товаром")
            elif sender_item.status != 'available':
                errors.append("Ваш товар не доступен для обмена")

        if receiver_item and receiver_item.owner_id == sender_id:
            errors.append("Нельзя предлагать обмен на свой же товар")

        if receiver_item and receiver_item.status != 'available':
            errors.append("Этот товар уже не доступен для обмена")

        if not errors and sender_item:
            query = """
            SELECT id FROM offers 
            WHERE sender_item_id = %s AND receiver_item_id = %s
            """
            from models import Database
            existing = Database.execute_query(query, (sender_item_id, receiver_item_id), fetchone=True)
            if existing:
                errors.append("Вы уже отправляли заявку на обмен с этим товаром")

        if errors:
            return None, errors

        try:
            offer = Offer.create(
                sender_id=sender_id,
                receiver_id=receiver_item.owner_id,
                sender_item_id=sender_item_id,
                receiver_item_id=receiver_item_id,
                message=message
            )
            return offer, []
        except Exception as e:
            return None, [f"Ошибка при создании заявки: {str(e)}"]

    @staticmethod
    def respond_to_offer(offer_id, user_id, action):
        offer = Offer.get_by_id(offer_id)

        if not offer:
            return False, ["Заявка не найдена"]

        if offer.receiver_id != user_id:
            return False, ["Вы не можете отвечать на эту заявку"]

        if offer.status != 'pending':
            return False, ["Заявка уже обработана"]

        try:
            if action == 'accept':
                offer.update_status('accepted')
                return True, ["Заявка принята"]
            elif action == 'reject':
                offer.update_status('rejected')
                return True, ["Заявка отклонена"]
            else:
                return False, ["Неизвестное действие"]
        except Exception as e:
            return False, [f"Ошибка при обработке заявки: {str(e)}"]