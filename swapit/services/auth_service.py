import secrets
from models.user import User

class AuthService:
    @staticmethod
    def register_user(username, email, password, confirm_password, **kwargs):
        errors = []

        if not username or len(username) < 3:
            errors.append("Имя пользователя должно быть не менее 3 символов")

        if not email or '@' not in email:
            errors.append("Введите корректный email")

        if not password or len(password) < 6:
            errors.append("Пароль должен быть не менее 6 символов")

        if password != confirm_password:
            errors.append("Пароли не совпадают")

        if User.get_by_username(username):
            errors.append("Имя пользователя уже занято")

        if User.get_by_email(email):
            errors.append("Email уже зарегистрирован")

        if errors:
            return None, errors

        try:
            user = User.create(username, email, password, **kwargs)
            return user, []
        except Exception as e:
            return None, [f"Ошибка при регистрации: {str(e)}"]

    @staticmethod
    def login_user(username, password):
        user = User.get_by_username(username)

        if not user and '@' in username:
            user = User.get_by_email(username)

        if not user or not User.verify_password(user.password_hash, password):
            return None, "Неверное имя пользователя или пароль"

        return user, None
        
    @staticmethod
    def validate_session(session_data):
        if 'user_id' not in session_data:
            return None

        user = User.get_by_id(session_data['user_id'])
        return user