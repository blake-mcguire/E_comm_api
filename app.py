from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import select, delete
from flask_marshmallow import Marshmallow
from flask_cors import CORS
import datetime
import uuid
from typing import List
from marshmallow import ValidationError, fields, validate

app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "http://localhost:5173"}})
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqlconnector://root:#InnaGLEAMG43@localhost/e_comm_db"

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(app, model_class=Base)
ma = Marshmallow(app)

# Models
class CustomerAccount(Base):
    __tablename__ = "customer_accounts"
    account_id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(db.String(320), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(db.String(255), nullable=False)

class AdminAccount(Base):
    __tablename__ = "admin_accounts"
    admin_id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(db.String(320), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(db.String(255), nullable=False)
    role: Mapped[str] = mapped_column(db.String(50), nullable=False, default='admin')


class SupportTicket(Base):
    __tablename__ = "support_tickets"
    ticket_id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey('customer_accounts.account_id'), nullable=True)
    subject: Mapped[str] = mapped_column(db.String(255), nullable=False)
    message: Mapped[str] = mapped_column(db.Text, nullable=False)
    status: Mapped[str] = mapped_column(db.String(50), nullable=False, default='Open')
    created_at: Mapped[datetime.datetime] = mapped_column(db.DateTime, default=datetime.datetime.utcnow)




class SessionTable(Base):
    __tablename__ = "sessions"
    session_id: Mapped[str] = mapped_column(primary_key=True)
    customer_account_id: Mapped[int] = mapped_column(db.ForeignKey('customer_accounts.account_id'), nullable=True)
    admin_account_id: Mapped[int] = mapped_column(db.ForeignKey('admin_accounts.admin_id'), nullable=True)
    user_type: Mapped[str] = mapped_column(db.String(50), nullable=False)
    login_time: Mapped[datetime.datetime] = mapped_column(db.DateTime, nullable=False)
    last_activity: Mapped[datetime.datetime] = mapped_column(db.DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=True)

order_product = db.Table(
    "order_product",
    Base.metadata,
    db.Column("order_id", db.ForeignKey("orders.order_id"), primary_key=True),
    db.Column("product_id", db.ForeignKey("products.product_id"), primary_key=True)      
)

class Order(Base):
    __tablename__ = "orders"
    order_id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime.date] = mapped_column(db.Date, nullable=False)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey("customer_accounts.account_id"))
    products: Mapped[List["Product"]] = db.relationship(secondary=order_product)

class Product(Base):
    __tablename__ = "products"
    product_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    price: Mapped[float] = mapped_column(db.Float, nullable=False)
    image_url: Mapped[str] = mapped_column(db.String(255), nullable=True)
    type: Mapped[str] = mapped_column(db.String(100), nullable=False) 

with app.app_context():
    db.create_all()

# Schemas
class CustomerAccountSchema(ma.Schema):
    account_id = fields.Integer()
    username = fields.String(required=True)
    email = fields.String(required=True, validate=validate.Email())
    password = fields.String(required=True, validate=validate.Length(min=1))

    class Meta:
        fields = ("account_id", "username", "email", "password")

customer_account_schema = CustomerAccountSchema()
customer_accounts_schema = CustomerAccountSchema(many=True)

class AdminAccountSchema(ma.Schema):
    admin_id = fields.Integer()
    username = fields.String(required=True)
    email = fields.String(required=True, validate=validate.Email())
    password = fields.String(required=True, validate=validate.Length(min=1))
    role = fields.String(required=True)

    class Meta:
        fields = ("admin_id", "username", "email", "password", "role")

admin_account_schema = AdminAccountSchema()
admin_accounts_schema = AdminAccountSchema(many=True)

class SessionTableSchema(ma.Schema):
    session_id = fields.String(required=True)
    customer_account_id = fields.Integer(required=False, allow_none=True)
    admin_account_id = fields.Integer(required=False, allow_none=True)
    user_type = fields.String(required=True, validate=validate.OneOf(["customer", "admin"]))
    login_time = fields.DateTime(required=True)
    last_activity = fields.DateTime(required=True)
    is_active = fields.Boolean(required=True)

    class Meta:
        fields = ("session_id", "customer_account_id", "admin_account_id", "user_type", "login_time", "last_activity", "is_active")

session_table_schema = SessionTableSchema()
session_tables_schema = SessionTableSchema(many=True)

class ProductSchema(ma.Schema):
    product_id = fields.Integer(required=False)
    name = fields.String(required=True, validate=validate.Length(min=1))
    price = fields.Float(required=True, validate=validate.Range(min=0))
    image_url = fields.String(required=False)
    type = fields.String(required=True)  # New type field

    class Meta:
        fields = ("product_id", "name", "price", "image_url", "type")

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

class OrderSchema(ma.Schema):
    order_id = fields.Integer(required=False)
    customer_id = fields.Integer(required=True)
    date = fields.Date(required=True)
    products = fields.List(fields.Nested(ProductSchema))

    class Meta:
        fields = ("order_id", "customer_id", "date", "products")

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)


class SupportTicketSchema(ma.Schema):
    ticket_id = fields.Integer()
    customer_id = fields.Integer(required=False) 
    subject = fields.String(required=True)
    message = fields.String(required=True)
    status = fields.String()
    created_at = fields.DateTime()

    class Meta:
        fields = ("ticket_id", "customer_id", "subject", "message", "status", "created_at")

support_ticket_schema = SupportTicketSchema()
support_tickets_schema = SupportTicketSchema(many=True)





@app.route('/support_tickets', methods=["POST"])
def create_support_ticket():
    data = request.get_json()

    customer_id = data.get('customer_id', None)
    
    new_ticket = SupportTicket(
        customer_id=customer_id, 
        subject=data['subject'],
        message=data['message'],
        status=data.get('status', 'Open')
    )
    
    db.session.add(new_ticket)
    db.session.commit()
    
    return jsonify({"success": True, "ticket_id": new_ticket.ticket_id}), 201


@app.route('/support_tickets', methods=["GET"])
def get_support_tickets():
    tickets = db.session.execute(select(SupportTicket)).scalars().all()
    return support_tickets_schema.jsonify(tickets)


@app.route('/logout', methods=['POST'])
def logout():
    data = request.json
    session_id = data['session_id']

    user_session = db.session.execute(select(SessionTable).where(SessionTable.session_id == session_id)).scalar()

    if user_session:
        user_session.is_active = False
        db.session.commit()

    return jsonify({"message": "Logout successful"}), 200

@app.route('/orders', methods=['GET'])
def get_orders():
    orders = db.session.execute(select(Order)).scalars().all()
    return orders_schema.jsonify(orders)

# Customer CRUD

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    user_type = data.get('user_type')

    if user_type == 'customer':
        account = db.session.execute(select(CustomerAccount).filter_by(email=email, password=password)).scalar_one_or_none()
        account_id_column = 'customer_account_id'
    else:
        account = db.session.execute(select(AdminAccount).filter_by(email=email, password=password)).scalar_one_or_none()
        account_id_column = 'admin_account_id'

    if account:
        session_id = str(uuid.uuid4())
        new_session = SessionTable(
            session_id=session_id,
            **{account_id_column: account.account_id},
            user_type=user_type,
            login_time=datetime.datetime.now(),
            last_activity=datetime.datetime.now(),
            is_active=True
        )
        db.session.add(new_session)
        db.session.commit()
        return jsonify(success=True, session_id=session_id, user_id=account.account_id, user_type=user_type)
    else:
        return jsonify(success=False), 401

@app.route('/admin_login', methods=['POST'])
def admin_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    admin_account = db.session.execute(select(AdminAccount).filter_by(email=email, password=password)).scalar_one_or_none()
    if admin_account:
        session_id = str(uuid.uuid4())
        new_session = SessionTable(
            session_id=session_id,
            admin_account_id=admin_account.admin_id,
            user_type='admin',
            login_time=datetime.datetime.now(),
            last_activity=datetime.datetime.now(),
            is_active=True
        )
        db.session.add(new_session)
        db.session.commit()
        return jsonify(success=True, session_id=session_id, user_id=admin_account.admin_id, user_type='admin')
    else:
        return jsonify(success=False, message="Invalid email or password"), 401
    
@app.route("/customer_accounts", methods=["POST"])
def create_customer_account():
    data = request.get_json()
    new_account = CustomerAccount(
        username=data['username'],
        email=data['email'],
        password=data['password']
    )
    db.session.add(new_account)
    db.session.commit()
    return jsonify(success=True, account_id=new_account.account_id)

@app.route('/admin_accounts', methods=['POST'])
def create_admin_account():
    data = request.get_json()
    new_admin = AdminAccount(
        username=data['username'],
        email=data['email'],
        password=data['password'],
        role='admin'
    )
    db.session.add(new_admin)
    db.session.commit()
    return jsonify(success=True, admin_id=new_admin.admin_id)

# New Routes for Managing Customer Accounts

# Fetch all customer accounts
@app.route('/customer_accounts', methods=['GET'])
def get_customer_accounts():
    customer_accounts = db.session.execute(select(CustomerAccount)).scalars().all()
    return jsonify(customer_accounts_schema.dump(customer_accounts))

# Update a customer account
@app.route('/customer_accounts/<int:account_id>', methods=['PUT'])
def update_customer_account(account_id):
    data = request.get_json()
    customer_account = db.session.execute(select(CustomerAccount).filter_by(account_id=account_id)).scalar_one_or_none()
    if customer_account is None:
        return jsonify({"error": "Customer account not found"}), 404

    customer_account.username = data.get('username', customer_account.username)
    customer_account.email = data.get('email', customer_account.email)
    customer_account.password = data.get('password', customer_account.password)

    db.session.commit()
    return jsonify({"success": True})


@app.route('/customer_accounts/<int:account_id>', methods=['DELETE'])
def delete_customer_account(account_id):
    try:
        # Delete related sessions
        sessions = db.session.execute(select(SessionTable).filter_by(customer_account_id=account_id)).scalars().all()
        if sessions:
            for session in sessions:
                db.session.delete(session)
            db.session.commit()

        # Delete related orders and order_product entries
        orders = db.session.execute(select(Order).filter_by(customer_id=account_id)).scalars().all()
        if orders:
            for order in orders:
                db.session.execute(delete(order_product).where(order_product.c.order_id == order.order_id))
                db.session.delete(order)
            db.session.commit()

        # Delete the customer account
        customer_account = db.session.execute(select(CustomerAccount).filter_by(account_id=account_id)).scalar_one_or_none()
        if customer_account is None:
            return jsonify({"error": "Customer account not found"}), 404

        db.session.delete(customer_account)
        db.session.commit()

        return jsonify({"success": True})

    except Exception as e:
        # Log the error
        app.logger.error(f"Error deleting customer account: {e}")
        db.session.rollback()
        return jsonify({"error": "An error occurred while deleting the customer account"}), 500


# Product CRUD
@app.route('/products', methods=["POST"])
def add_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    new_product = Product(
        name=product_data['name'],
        price=product_data['price'],
        image_url=product_data.get('image_url')
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify({"Message": "New product successfully added!"}), 201

@app.route('/products', methods=["GET"])
def get_products():
    product_type = request.args.get('type')
    query = select(Product)
    if product_type:
        query = query.filter_by(type=product_type)
    products = db.session.execute(query).scalars().all()
    return products_schema.jsonify(products)

@app.route("/products/<int:product_id>", methods=["GET"])
def get_product_by_id(product_id):
    product = db.session.execute(select(Product).filter(Product.product_id == product_id)).scalar()
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    return product_schema.jsonify(product)

@app.route("/products/by-name", methods=["GET"])
def get_product_by_name():
    name = request.args.get("name")
    search = f"%{name}%"
    products = db.session.execute(select(Product).where(Product.name.like(search)).order_by(Product.price.asc())).scalars().all()
    return products_schema.jsonify(products)

@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    product = db.session.execute(select(Product).filter(Product.product_id == product_id)).scalar()
    if product is None:
        return jsonify({"error": "Product not found!"}), 404

    try:
        product_data = product_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    for field, value in product_data.items():
        setattr(product, field, value)
    db.session.commit()
    return jsonify({"message": "Product details successfully updated!"}), 200

@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    product = db.session.execute(select(Product).filter(Product.product_id == product_id)).scalar()
    if product is None:
        return jsonify({"error": "Product not found"}), 404

    if db.session.execute(select(order_product).filter(order_product.c.product_id == product_id)).first():
        return jsonify({"error": "Product cannot be deleted as it is part of an order"}), 400

    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product successfully deleted!"}), 200

# Order CRUD
@app.route("/orders", methods=["POST"])
def add_order():
    try:
        json_order = request.json
        products = json_order.pop('products', [])
        if not products:
            return jsonify({"Error": "Cannot place an order without products"}), 400

        order_data = order_schema.load(json_order)
    except ValidationError as err:
        return jsonify(err.messages), 400

    new_order = Order(customer_id=order_data['customer_id'], date=order_data['date'])

    # Create a set to track added products and prevent duplicates
    added_products = set()

    for product_id in products:
        if product_id not in added_products:
            product = db.session.execute(select(Product).filter(Product.product_id == product_id)).scalar()
            if product:
                new_order.products.append(product)
                added_products.add(product_id)
            else:
                return jsonify({"Error": f"Product with ID {product_id} not found"}), 404

    db.session.add(new_order)
    db.session.commit()
    return jsonify({"message": "New order successfully added!"}), 201

@app.route("/orders/<int:order_id>", methods=["GET"])
def get_orders_by_id(order_id):
    order = db.session.execute(select(Order).filter(Order.order_id == order_id)).scalar()
    if order is None:
        return jsonify({"message": "Order Not Found"}), 404
    return order_schema.jsonify(order)

@app.route('/orders/<int:order_id>', methods=["PUT"])
def update_order(order_id):
    order = db.session.execute(select(Order).filter(Order.order_id == order_id)).scalar()
    if order is None:
        return jsonify({"message": "Order Not Found"}), 404

    try:
        order_data = order_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    for field, value in order_data.items():
        setattr(order, field, value)
    db.session.commit()
    return jsonify({"Message": "Order was successfully updated! "}), 200

@app.route("/orders/<int:order_id>", methods=["DELETE"])
def delete_order(order_id):
    # Delete related order_product entries first
    db.session.execute(order_product.delete().where(order_product.c.order_id == order_id))
    
    order = db.session.execute(select(Order).filter(Order.order_id == order_id)).scalar()
    if order is None:
        return jsonify({"error": "Order not found" }), 404

    db.session.delete(order)
    db.session.commit()
    return jsonify({"message": "Order removed successfully"}), 200

@app.route('/orders/customer/<int:customer_id>', methods=['GET'])
def get_customer_orders(customer_id):
    customer_orders = db.session.execute(select(Order).filter_by(customer_id=customer_id)).scalars().all()
    return orders_schema.jsonify(customer_orders)

@app.route('/check_account', methods=['POST'])
def check_account():
    data = request.json
    email = data.get('email')
    user_type = data.get('user_type')  # 'customer' or 'admin'

    if not email or not user_type:
        return jsonify({"error": "Email and user type are required"}), 400

    table = CustomerAccount if user_type == 'customer' else AdminAccount

    user = db.session.execute(select(table).where(table.email == email)).scalar()

    if user:
        return jsonify({"exists": True}), 200
    else:
        return jsonify({"exists": False}), 404

if __name__ == '__main__':
    app.run(debug=True)
