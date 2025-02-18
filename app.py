from flask import Flask, render_template, request, redirect, session, g, url_for, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

# アプリケーションの設定
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafe_app.db'  # データベースの設定
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'

# SQLAlchemyとFlask-Migrateの初期化
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Blueprintの作成
auth = Blueprint('auth', __name__)
products_blueprint = Blueprint('products', __name__)

# モデル定義
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')  # 'role'カラムを追加

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(255))
    category = db.Column(db.String(80))
    price = db.Column(db.Float)
    inventory = db.relationship('Inventory', backref='product', lazy=True)

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False)
    stock_history = db.relationship('StockHistory', backref='inventory', lazy=True)

class StockHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)  # DateTime型に変更
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# 認証関連ルート
@auth.route('/<action>', methods=['GET', 'POST'])
def auth_action(action):
    error = None
    if action == 'register':
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role')

            if not username or not password:
                return "ユーザー名とパスワードは必須です", 400
            if User.query.filter_by(username=username).first():
                return "このユーザー名は既に使われています", 400

            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password, role=role)
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('auth.auth_action', action='login'))
        return render_template('register.html')

    elif action == 'login':
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                return redirect(url_for('products.products'))  # 商品一覧にリダイレクト
            else:
                error = "ユーザー名またはパスワードが間違っています"
        return render_template('login.html', error=error)

    else:
        return "不正なアクションです", 400

@auth.route('/logout')
def logout():
    session.pop('user_id', None)  # セッションからユーザーIDを削除
    return redirect(url_for('auth.auth_action', action='login'))  # ログインページにリダイレクト

# ログインチェック
@app.before_request
def before_request():
    # ログインしていない場合、ログインページへリダイレクト
    if 'user_id' not in session and request.endpoint not in ['auth.auth_action', 'auth.logout']:
        return redirect(url_for('auth.auth_action', action='login'))
    g.db = db.session

@app.teardown_request
def teardown_request(exception=None):
    db.session.remove()

# トップページ
@app.route('/')
def index():
    return redirect(url_for('products.products'))

# 商品関連ルート
@products_blueprint.route('/products')
def products():
    products = Product.query.all()
    return render_template('products.html', products=products)

@products_blueprint.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['product_name']
        description = request.form['product_description']
        category = request.form['product_category']
        price = request.form['product_price']
        stock_quantity = request.form['stock_quantity']

        if not name or not price.isdigit() or not stock_quantity.isdigit():
            return "Invalid input.", 400

        new_product = Product(name=name, description=description, category=category, price=float(price))
        db.session.add(new_product)
        db.session.commit()

        new_inventory = Inventory(product_id=new_product.id, stock_quantity=int(stock_quantity))
        db.session.add(new_inventory)
        db.session.commit()

        return redirect(url_for('products.products'))

    return render_template('add_product.html')

@products_blueprint.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.name = request.form['product_name']
        product.description = request.form['product_description']
        product.category = request.form['product_category']
        try:
            product.price = float(request.form['product_price'])
        except ValueError:
            return "価格は数値で入力してください", 400
        db.session.commit()
        return redirect(url_for('products.products'))
    return render_template('edit_product.html', product=product)

@products_blueprint.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('products.products'))

@products_blueprint.route('/stock_entry', methods=['GET', 'POST'])
def stock_entry():
    products = Product.query.all()
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        quantity = request.form.get('quantity')
        operation = request.form.get('operation')
        user_id = session.get('user_id')

        if not product_id or not quantity or not product_id.isdigit() or not quantity.isdigit():
            return "Invalid input.", 400

        quantity = int(quantity)
        inventory = Inventory.query.filter_by(product_id=product_id).first()
        if not inventory:
            return "Inventory not found", 404

        if operation == '入庫':
            inventory.stock_quantity += quantity
        elif operation == '出庫':
            if inventory.stock_quantity < quantity:
                return "Insufficient stock", 400
            inventory.stock_quantity -= quantity
        else:
            return "Invalid operation", 400

        db.session.commit()

        timestamp = datetime.now()  # 現在時刻を datetime 型で取得
        new_stock_history = StockHistory(
            inventory_id=inventory.id,
            quantity=quantity if operation == '入庫' else -quantity,
            type=operation,
            timestamp=timestamp,
            user_id=user_id
        )
        db.session.add(new_stock_history)
        db.session.commit()

        return redirect(url_for('products.stock_history'))

    return render_template('stock_entry.html', products=products)

@products_blueprint.route('/stock_history')
def stock_history():
    yesterday = datetime.now() - timedelta(days=1)  # 昨日の日付を取得

    stock_history_data = db.session.query(
        StockHistory.id,
        Product.name.label('product_name'),
        StockHistory.quantity,
        StockHistory.type,
        StockHistory.timestamp,
        User.username
    ).join(Inventory, StockHistory.inventory_id == Inventory.id) \
     .join(Product, Inventory.product_id == Product.id) \
     .join(User, StockHistory.user_id == User.id) \
     .filter(StockHistory.timestamp >= yesterday) \
     .all()

    return render_template('stock_history.html', stock_history_data=stock_history_data)

@products_blueprint.route('/delete_stock_history/<int:history_id>', methods=['POST'])
def delete_stock_history(history_id):
    stock_history = StockHistory.query.get_or_404(history_id)
    db.session.delete(stock_history)
    db.session.commit()
    return redirect(url_for('products.stock_history'))

# アプリケーションの実行
app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(products_blueprint, url_prefix='/products')

if __name__ == '__main__':
    app.run(debug=True)
