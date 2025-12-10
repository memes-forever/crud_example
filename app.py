# app.py (обновленный с пагинацией для items и users)
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime  # Для полей created_at и updated_at
from sqlalchemy.orm import joinedload

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Замените на реальный секретный ключ
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Модель пользователя для аутентификации
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=True)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='user')  # Роли: 'user', 'editor' или 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Дата создания
    last_activity = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Дата последней активности

    items = db.relationship('Item', backref='creator', lazy=True)


# Модель для данных таблицы (пример: простая таблица с задачами)
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Дата создания
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)  # Новое поле: дата обновления


# Создание базы данных (запустите один раз)
with app.app_context():
    db.create_all()
    # Добавьте тестового администратора, если нужно
    if not User.query.filter_by(username='admin').first():
        hashed_password = generate_password_hash('password', method='pbkdf2:sha256')
        new_user = User(username='admin', password=hashed_password, role='admin')
        db.session.add(new_user)
        db.session.commit()


# Главная страница с таблицей (требует аутентификации)
@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    current_user = User.query.get(session['user_id'])
    is_admin = current_user.role == 'admin'
    can_edit = current_user.role in ['admin', 'editor']

    page = request.args.get('page', 1, type=int)
    per_page = 10

    if is_admin:
        items_query = Item.query.options(joinedload(Item.creator))
    else:
        items_query = Item.query.filter_by(creator_id=current_user.id).options(joinedload(Item.creator))

    pagination = items_query.order_by(Item.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    items = pagination.items

    if request.method == 'POST':
        if not can_edit:
            flash('У вас нет прав на редактирование.', 'danger')
            return redirect(url_for('index'))

        action = request.form.get('action')

        if action == 'add':
            name = request.form['name']
            description = request.form['description']
            new_item = Item(name=name, description=description, creator_id=current_user.id)
            db.session.add(new_item)
            db.session.commit()
            flash('Элемент добавлен!', 'success')

        elif action == 'edit':
            item_id = int(request.form['item_id'])
            item = Item.query.get(item_id)
            if item:
                item.name = request.form['name']
                item.description = request.form['description']
                item.updated_at = datetime.utcnow()  # Ручное обновление, если onupdate не срабатывает
                db.session.commit()
                flash('Элемент обновлен!', 'success')

        elif action == 'delete':
            item_id = int(request.form['item_id'])
            item = Item.query.get(item_id)
            if item:
                db.session.delete(item)
                db.session.commit()
                flash('Элемент удален!', 'danger')

        return redirect(url_for('index'))

    return render_template('index.html',
                           items=items,
                           pagination=pagination,
                           is_admin=is_admin,
                           can_edit=can_edit,
                           current_role=current_user.role,
                           current_user=current_user)


# Страница управления пользователями (только для админов)
@app.route('/users', methods=['GET', 'POST'])
def users():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    current_user = User.query.get(session['user_id'])
    is_admin = current_user.role == 'admin'
    if current_user.role != 'admin':
        flash('Доступ запрещён.', 'danger')
        return redirect(url_for('index'))

    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    all_users = pagination.items

    if request.method == 'POST':
        action = request.form.get('action')
        user_id = int(request.form['user_id'])
        user = User.query.get(user_id)

        if not user:
            flash('Пользователь не найден.', 'danger')
            return redirect(url_for('users'))

        if action == 'edit_role':
            new_role = request.form['role']
            if new_role in ['user', 'editor', 'admin']:
                user.role = new_role
                db.session.commit()
                flash(f'Роль пользователя {user.username} обновлена.', 'success')
            else:
                flash('Неверная роль.', 'danger')

        elif action == 'edit_name':
            new_name = request.form.get('name', '').strip()
            user.name = new_name if new_name else None
            db.session.commit()
            flash(f'Имя пользователя {user.username} обновлено.', 'success')

        elif action == 'change_password':
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']
            if new_password == confirm_password:
                hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
                user.password = hashed_password
                db.session.commit()
                flash(f'Пароль пользователя {user.username} изменен.', 'success')
            else:
                flash('Пароли не совпадают.', 'danger')

        elif action == 'delete':
            if user_id == current_user.id:
                flash('Нельзя удалить самого себя.', 'danger')
            elif user.role == 'admin':
                flash('Нельзя удалить администратора.', 'danger')
            else:
                db.session.delete(user)
                db.session.commit()
                flash(f'Пользователь {user.username} удален.', 'danger')

        return redirect(url_for('users'))

    return render_template('users.html', users=all_users, pagination=pagination, current_user=current_user, is_admin=is_admin)


# Страница логина
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            user.last_activity = datetime.utcnow()  # Обновляем дату последней активности
            db.session.commit()
            session['user_id'] = user.id
            flash('Вы успешно вошли!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль', 'danger')
    return render_template('login.html')


# Страница регистрации (регистрируются как 'user')
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Пароли не совпадают', 'danger')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('Имя пользователя уже существует', 'danger')
            return render_template('register.html')

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password, role='user')
        db.session.add(new_user)
        db.session.commit()
        flash('Регистрация успешна! Теперь войдите.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# Выход
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True, port=5001)

# if __name__ == "__main__":
#     from waitress import serve
#     serve(app, host="0.0.0.0", port=8080)
