from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from functools import wraps
from werkzeug.utils import secure_filename
from config import Config
import os
import uuid
from models.user import User
from models.item import Item
from models.offer import Offer
from services.auth_service import AuthService
from services.item_service import ItemService
from services.offer_service import OfferService

UPLOAD_FOLDER = os.path.join('static', 'uploads', 'items')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app = Flask(__name__, static_folder='static', static_url_path='')
app.config.from_object(Config)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def generate_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = str(uuid.uuid4())
    return session['csrf_token']

def verify_csrf_token(token):
    return 'csrf_token' in session and token == session['csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = AuthService.validate_session(session)
        if not user:
            flash('Пожалуйста, войдите в систему', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(user, *args, **kwargs)

    return decorated_function

def item_owner_required(f):
    @wraps(f)
    def decorated_function(user, item_id, *args, **kwargs):
        item = Item.get_by_id(item_id)
        if not item or item.owner_id != user.id:
            flash('У вас нет прав для этого действия', 'danger')
            return redirect(url_for('items_index'))
        return f(user, item, *args, **kwargs)

    return decorated_function

@app.route('/')
def index():
    user = AuthService.validate_session(session)
    items = ItemService.get_available_items(limit=12)
    return render_template('items/index.html', user=user, items=items)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        print(f"Attempting to login user: {username}")
        user = User.authenticate(username, password)
        
        if user:
            print(f"User {user.username} authenticated successfully")
            session['user_id'] = user.id
            session['username'] = user.username 

            if remember:
                session.permanent = True
            flash('Вы успешно вошли в систему', 'success')
            next_page = request.args.get('next') or url_for('index')
            return redirect(next_page)
            
        else:
            print(f"Authentication failed for user: {username}")
            flash('Неверное имя пользователя или пароль', 'danger')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        errors = []
        if not username or len(username) < 3:
            errors.append('Имя пользователя должно быть не менее 3 символов')
        if not email or '@' not in email:
            errors.append('Введите корректный email')
        if not password or len(password) < 6:
            errors.append('Пароль должен быть не менее 6 символов')
        if password != confirm_password:
            errors.append('Пароли не совпадают')
        
        if not errors:
            try:
                user = User.create(username, email, password)
                flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                errors.append('Ошибка при регистрации. Возможно, пользователь с таким именем или email уже существует.')
        
        for error in errors:
            flash(error, 'danger')
    
    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

@app.route('/items')
@app.route('/')
def items_index():
    category = request.args.get('category')
    items = ItemService.get_available_items(category=category)
    user = AuthService.validate_session(session)
    categories = ['Электроника', 'Одежда', 'Книги', 'Спорт', 'Мебель', 'Другое']

    user_items = []
    if user:
        from models.item import Item
        user_items = Item.get_user_available_items(user.id)
    
    return render_template('items/index.html',
                         user=user,
                         items=items,
                         user_items=user_items,
                         category=category,
                         categories=categories)



@app.route('/items/new', methods=['GET', 'POST'])
@login_required
def create_item(user):
    if request.method == 'POST':
        try:
            if not verify_csrf_token(request.form.get('csrf_token')):
                flash('Ошибка безопасности. Пожалуйста, попробуйте еще раз.', 'danger')
                return redirect(url_for('create_item'))
                
            title = request.form.get('title')
            description = request.form.get('description')
            category = request.form.get('category')
            condition = request.form.get('condition', 'good')
            
            errors = []
            if not title or len(title) < 3:
                errors.append('Название должно быть не менее 3 символов')
            if not description or len(description) < 10:
                errors.append('Описание должно быть не менее 10 символов')
            if not category:
                errors.append('Выберите категорию')
            
            if errors:
                for error in errors:
                    flash(error, 'danger')
                return render_template('items/create.html')
            
            image_urls = []
            
            if 'image_files' in request.files:
                files = request.files.getlist('image_files')
                
                for file in files:
                    if file and file.filename and allowed_file(file.filename):
                        try:
                            
                            original_filename = secure_filename(file.filename)
                            file_extension = os.path.splitext(original_filename)[1].lower()
                            
                            import datetime
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            unique_id = str(uuid.uuid4())[:8]
                            unique_filename = f"{timestamp}_{unique_id}{file_extension}"
                            
                            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                            file.save(filepath)
                            if os.path.exists(filepath):
                                image_url = f"/uploads/items/{unique_filename}"
                                image_urls.append(image_url)
                            else:
                                flash(f'Ошибка при сохранении файла {file.filename}', 'danger')
                                
                        except Exception as e:
                            print(f"Error saving file {file.filename}: {str(e)}")
                            import traceback
                            traceback.print_exc()
                            flash(f'Ошибка при загрузке файла {file.filename}', 'danger')
                    elif file.filename:
                        print(f"File rejected: {file.filename} (not allowed)")
                        flash(f'Файл {file.filename} имеет недопустимый формат', 'danger')
            else:
                print("No 'image_files' in request.files")
                print(f"Available files: {list(request.files.keys())}")

            for i in range(1, 4):
                url = request.form.get(f'image_url_{i}', '').strip()
                if url:
                    image_urls.append(url)

            item = Item.create(
                title=title,
                description=description,
                category=category,
                condition=condition,
                owner_id=user.id,
                image_urls=image_urls)
            
            flash('Товар успешно добавлен!', 'success')
            return redirect(url_for('item_detail', item_id=item.id))
            
        except Exception as e:
            import traceback
            print("Error in create_item:", str(e))
            print(traceback.format_exc())
            flash(f'Произошла ошибка при создании товара: {str(e)}', 'danger')
            return render_template('items/create.html')
    
    return render_template('items/create.html')

@app.route('/uploads/items/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico') if os.path.exists(os.path.join(app.static_folder, 'favicon.ico')) else ('', 204)

@app.context_processor
def inject_user():
    if 'user_id' in session:
        user = User.get_by_id(session['user_id'])
        if user:
            from models.offer import Offer
            pending_offers_count = Offer.count_pending_for_user(user.id)
            return {
                'user': user,
                'pending_offers_count': pending_offers_count
            }
    return {}

@app.route('/items/<int:item_id>')
def item_detail(item_id):
    item = Item.get_by_id(item_id)
    if not item:
        return "Item not found", 404

    user = AuthService.validate_session(session)
    user_items = []

    if user:
        user_items = Item.get_user_items(user.id)

    return render_template(
        'items/detail.html',
        item=item,
        user=user,
        user_items=user_items
    )

@app.route('/items/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
@item_owner_required
def items_edit(user, item):
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        condition = request.form.get('condition')
        status = request.form.get('status')

        updated_item, errors = ItemService.update_item(
            item.id, user.id,
            title=title,
            description=description,
            category=category,
            condition=condition,
            status=status
        )

        if updated_item:
            flash('Товар успешно обновлен', 'success')
            return redirect(url_for('item_detail', item_id=item.id))
        else:
            for error in errors:
                flash(error, 'danger')

    categories = ['Электроника', 'Одежда', 'Книги', 'Спорт', 'Мебель', 'Другое']
    conditions = [
        ('new', 'Новый'),
        ('excellent', 'Отличное'),
        ('good', 'Хорошее'),
        ('satisfactory', 'Удовлетворительное'),
        ('broken', 'Требует ремонта')
    ]
    statuses = [
        ('available', 'Доступен'),
        ('reserved', 'Зарезервирован'),
        ('swapped', 'Обменян')
    ]

    return render_template('items/edit.html',
                           user=user,
                           item=item,
                           categories=categories,
                           conditions=conditions,
                           statuses=statuses)


@app.route('/items/<int:item_id>/delete', methods=['POST'])
@login_required
@item_owner_required
def delete_item(user, item):
    success, errors = ItemService.delete_item(item.id, user.id)
    if success:
        flash('Товар успешно удален', 'success')
        return redirect(url_for('items_index'))
    else:
        for error in errors:
            flash(error, 'danger')
        return redirect(url_for('items_edit', item_id=item.id))


@app.route('/offers', methods=['GET', 'POST'])
@login_required
def offers_index(user):
    if request.method == 'POST':
        receiver_item_id = request.form.get('receiver_item_id')
        sender_item_id = request.form.get('sender_item_id')
        message = request.form.get('message')

        if not receiver_item_id:
            flash('Ошибка: не указан товар для обмена', 'danger')
            return redirect(url_for('items_index'))

        if sender_item_id == 'none':
            sender_item_id = None

        try:
            offer, errors = OfferService.create_offer(
                user.id, receiver_item_id, sender_item_id, message
            )

            if offer:
                flash('Заявка на обмен отправлена', 'success')
                return redirect(url_for('offers_index'))
            else:
                for error in errors:
                    flash(error, 'danger')
        except Exception as e:
            flash(f'Произошла ошибка при создании заявки: {str(e)}', 'danger')

    sent_offers = Offer.get_by_user(user.id, role='sent')
    received_offers = Offer.get_by_user(user.id, role='received')

    return render_template('offers/index.html',
                           user=user,
                           sent_offers=sent_offers,
                           received_offers=received_offers)


@app.route('/offers/<int:offer_id>/respond', methods=['POST'])
@login_required
def offers_respond(user, offer_id):
    action = request.form.get('action')
    
    if action not in ['accept', 'reject']:
        flash('Неверное действие', 'danger')
        return redirect(url_for('offers_index'))

    success, errors = OfferService.respond_to_offer(offer_id, user.id, action)

    if success:
        flash('Заявка успешно обновлена', 'success')
    else:
        for error in errors:
            flash(error, 'danger')

    return redirect(url_for('offers_index'))


@app.route('/profile')
@app.route('/profile/<int:user_id>')
@login_required
def user_profile(user, user_id=None):
    profile_user = User.get_by_id(user_id) if user_id else user

    completed_offers_count = Offer.get_user_completed_offers_count(user.id)
    
    if not profile_user:
        abort(404)
        
    user_items = ItemService.get_user_items(profile_user.id)
    completed_offers_count = Offer.get_user_completed_offers_count(profile_user.id)
    
    return render_template('user/profile.html', 
                         user=user,  
                         profile_user=profile_user,
                         items=user_items,
                         completed_offers_count=completed_offers_count)

@app.route('/api/check_username')
def check_username():
    username = request.args.get('username')
    user = User.get_by_username(username)
    return jsonify({'available': not bool(user)})

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.route('/exchange/create', methods=['POST'])
@login_required
def create_exchange():
    if request.method == 'POST':
        try:
            item_id = request.form.get('item_id')
            offered_item_id = request.form.get('offered_item_id') or None
            message = request.form.get('message', '')

            if not item_id:
                return jsonify({'success': False, 'error': 'Не указан товар для обмена'})

            exchange = Offer(
                requested_item_id=item_id,
                offered_item_id=offered_item_id,
                message=message,
                sender_id=session['user_id'],
                status='pending'
            )
            exchange.save()

            return jsonify({'success': True})

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)