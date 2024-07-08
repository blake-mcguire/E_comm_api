from flask import Flask, jsonify, request #imports flask and allows us to instantiate an app
from flask_sqlalchemy import SQLAlchemy # this is Object Relational Mapper
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session # this is a class that all of our classes will inherit
# provides base functionality for converting python objects to rows of data
from sqlalchemy import select, delete #query our database with a select statement
from flask_marshmallow import Marshmallow # creates our schema to validate incoming and outgoing data
from flask_cors import CORS # Cross Origin Resource Sharing - allows our application to be accessed by 3rd parties
import datetime
from typing import List #tie a one to many relationship back to the one
from marshmallow import ValidationError, fields, validate

#SETUP
app = Flask(__name__)
CORS(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqlconnector://root:#InnaGLEAMG43@localhost/e_comm_db"


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(app, model_class=Base)

ma = Marshmallow(app)

#======================DB MODELS===========================

# Tables needed 
# Customers customer_id name, email, phone, customer_account, orders 
# customerAccount accoutn_id, username, password, customer_id, customer
#product  has product_id, name, price, stock_qt
order_product = db.Table(
    "Order_Product",
    Base.metadata,
    db.Column('order_id', db.ForeignKey("Orders.order_id"), primary_key=True),
    db.Column("product_id", db.ForeignKey("Products.product_id"), primary_key=True)
    )


class Product(Base):
    __tablename__ = 'Products'
    
    product_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(200), nullable=False)
    price: Mapped[float] = mapped_column(db.Float, nullable=False)
    

class ProductSchema(ma.Schema):
    product_id = fields.Integer()
    name = fields.String(required=True)
    price = fields.Float(required=True)
    
    class Meta:
        fields = ("product_id", "name", "price")
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)     
        
class Customer(Base):
    __tablename__ = "Customers"
    
    customer_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255))
    email: Mapped[str] = mapped_column(db.String(320))
    phone: Mapped[str] = mapped_column(db.String(15))
    
    customer_account: Mapped["CustomerAccount"] = db.relationship(back_populates="customer")
    
    orders: Mapped[List["Order"]] = db.relationship(back_populates="customer")
    
class CustomerSchema(ma.Schema):
    customer_id = fields.Integer()
    name = fields.String(required=True)
    email = fields.String(required=True)
    phone = fields.String(required=True)
    

    class Meta:
        fields = ("customer_id", "name", "email", "phone")
customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

        
    
class CustomerAccount(Base):
    __tablename__ = "Customer_Accounts"
    
    account_id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(db.String(255), nullable=False)
    
    customer_id: Mapped[int] = mapped_column(db.ForeignKey('Customers.customer_id'))
    customer: Mapped["Customer"] = db.relationship(back_populates='customer_account')
    
    
class AccountSchema(ma.Schema):
    account_id = fields.Integer()
    username = fields.String(required=True)
    password = fields.String(required=True)
    customer_id = fields.Integer(required = True)
    
    class Meta:
        fields = ('account_id', 'username', 'password', 'customer_id')
account_schema = AccountSchema()
accounts_schema = AccountSchema(many=True)
    
    
class Order(Base):
    __tablename__ = "Orders"
    order_id: Mapped[int] = mapped_column(db.Integer(), primary_key=True)
    date: Mapped[datetime.date] = mapped_column(db.Date, nullable=False)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey('Customers.customer_id'), nullable=False)
    products: Mapped[List["Product"]] = db.relationship(secondary=order_product)
    customer: Mapped["Customer"] = db.relationship(back_populates="orders")

    def make_order(self, product_id):
        self.products.append(product_id)

class OrderSchema(ma.Schema):
    order_id = fields.Integer()
    customer_id = fields.Integer(required=True)
    date = fields.Date(required=True)
    products = fields.List(fields.Integer())
    
    class Meta:
        fields = ("order_id", 'customer_id', 'date', 'product_id')
        
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)


    
    
with app.app_context():
    db.create_all()



# =====================================================CUSTOMER ACCOUNT CRUD===========================================================


@app.post('/customeraccount')

def add_customer_acc():
    try:
        customer_acc_data = account_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    with Session(db.engine) as session:
        with session.begin():
            username=customer_acc_data['username']
            password=customer_acc_data['password']
            customer_id=customer_acc_data['customer_id']
            new_account = CustomerAccount(username=username, password=password, customer_id=customer_id)
            session.add(new_account)
            session.commit()
            
    return jsonify({'message': 'customeraccount succesfully instantiated'}), 201
            
# put to update the username
@app.put('/customeraccount/<int:id>') 
def update_account(id):
    with Session(db.engine) as session:
        with session.begin():
            
            query = select(CustomerAccount).filter(CustomerAccount.account_id == id)
            result = session.execute(query).scalars().first()
            
            if result is None:
                return jsonify({"message":"account not found!"}), 404
            account = result
            
            try:
                account_data = account_schema.load(request.json)
            except ValidationError as e:
                return jsonify({e.messages}), 400
            
            for key, value in account_data.items():
                setattr(account, key, value)
                
            session.commit()
            return jsonify({"message": "account succesfully updated"}), 200

# Route to get customer accounts plural

@app.get("/customeraccount")
def get_accounts():
    query = select(CustomerAccount)
    result = db.session.execute(query).scalars().all()
    accounts = []
    for account in result:
        account_dict = {
            'account_id': account.account_id,
            'customer_id': account.customer_id,
            'username': account.username,
            'password': account.password
        }
        accounts.append(account_dict)
    return jsonify(accounts), 200

@app.get("/customeraccount/<int:id>")
def get_account_by_id(id):
    with Session(db.engine) as session:
        account = session.execute(select(CustomerAccount).filter_by(account_id=id)).scalar()
        if account:
            return jsonify(account_schema.dump(account)), 200
        else:
            return jsonify({'message': 'account not found'}), 404

#Route to delete customer accounts
@app.delete("/customeraccount/<int:id>")
def delete_account(id):
    delete_statement = delete(CustomerAccount).where(CustomerAccount.account_id == id) 
    with db.session.begin():
        result = db.session.execute(delete_statement)
        if result.rowcount == 0:
            return jsonify({"error": f"Customer Account with the id {id} doesnt exist"})    
        return jsonify({'message': 'customer account succesfully deleted'}), 200    


# =================================Customer Crud Operations==========================
#CREATE A CUSTOMER
@app.post('/customers')
def add_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    with Session(db.engine) as session:
        with session.begin():
            name = customer_data['name']
            email = customer_data['email']
            phone = customer_data['phone']
            
            new_customer = Customer(name=name, email=email, phone=phone) 
            session.add(new_customer)
            session.commit()
    return jsonify({'message': 'New Customer Created!'}), 201


#DELETE A CUSTOMER
@app.delete('/customers/<int:id>')
def delete_customer(id):
    with Session(db.engine) as session:
        with session.begin():
            query = select(Customer).filter(Customer.customer_id == id)
            result = session.execute(query).scalars().first()
            
            if result is None:
                return jsonify({"message": "Customer not found!"}), 404
            session.delete(result)
            session.commit()
            return jsonify({'message': f'Customer with id {id} was deleted'}), 200

# UPDATE A CUSTOMER
@app.put('/customer/<int:id>')
def update_customer(id):
    with Session(db.engine) as session:
        with session.begin():
            query = select(Customer).filter(Customer.customer_id == id)
            result = session.execute(query).scalars().first()
            if result is None:
                return jsonify({'error': 'Customer Not found!'}), 404
            customer = result
            try:
                customer_data = customer_schema.load(request.json)
            except ValidationError as err:
                return jsonify(err.messages)
            
            for field, value in customer_data.items():
                setattr(Product, field, value)
            
            session.commit()
            return jsonify({"message": f"customer with id of {id} succesfully updated"})
        
            
@app.get('/customers') 
def view_customers():
    query = select(Customer)
    result = db.session.execute(query).scalars().all()
    customers = []
    for customer in result:
        customer_dict = {
            'customer_id': customer.customer_id,
            'name': customer.name,
            'email': customer.email,
            'phone': customer.phone
        }         
        customers.append(customer_dict)
    return jsonify(customers)   

@app.get('/customers/<int:id>')
def get_customer_by_id(id):
    with Session(db.engine) as session:
        customer = session.execute(select(Customer).filter_by(customer_id=id)).scalar()
        if customer:
            return jsonify(customer_schema.dump(customer)), 200
        else:
            return jsonify({'message': 'customer not found'}), 404
            
# =========================Orders CRUD Operations==============================

@app.post('/orders')
def add_order():
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    product_ids = order_data.get('product_id', [])
    
    new_order = Order(
        customer_id=order_data['customer_id'],
        date=order_data['date']
    )
    
    with Session(db.engine) as session:
        with session.begin():
            
            for product_id in product_ids:
                product = session.query(Product).filter(Product.product_id == product_id).first()
                if not product:
                    session.rollback()  # Rollback if any product is not found
                    return jsonify({'message': f'Product with ID {product_id} not found'}), 404
                new_order.make_order(product)           
                return jsonify({'message': 'new order created'})
        session.add(new_order)
        session.commit()
        
        
@app.put('/orders/<int:id>')
def update_order_date(id):
    with Session(db.engine) as session:
        with session.begin():
            
            query = select(Order).filter(Order.order_id == id)
            result = session.execute(query).scalar()
            if result is None:
                return jsonify({'message': 'order not found'}), 404
            order = result 
            try:
                order_data = order_schema.load(request.json)
            except ValidationError as err:
                return jsonify(err.messages), 400
            order.customer_id = order_data.get('customer_id', order.customer_id)
            order.date = order_data.get('date', order.date)

            # update products
            product_ids = order_data.get('product_id', [])
            order.products.clear()  # clear it out so we can start from scratch

            for product_id in product_ids:
                product = session.query(Product).get(product_id)
                if product:
                    order.products.append(product)
            #save to order table
            session.commit()
            return jsonify({"message":f"Order with the id {id} has been updated!"}), 200

@app.get('/orders')
def view_orders():
    query = select(Order)
    result = db.session.execute(query).scalars().all()
    orders_with_products = []
    for order in result:
        order_dict = {
            'order_id': order.order_id,
            'customer_id' : order.customer_id,
            'date': order.date,
            'product': [product.product_id for product in order.products]
        }         
        orders_with_products.append(order_dict)
    return jsonify(orders_with_products)   

@app.get('/orders/<int:id>')
def get_order_by_id(id):
    with Session(db.engine) as session:
        order = session.execute(select(Order).filter_by(order_id=id)).scalar()
        if order:
            return jsonify(order_schema.dump(order)), 200
        else:
            return jsonify({'message': 'order not found'}), 404
    
@app.delete('/orders/<int:id>')
def delete_order(id):
    delete_statement = delete(Order).where(Order.order_id == id)
    with db.session.begin():
        result = db.session.execute(delete_statement)
        if result.rowcount == 0:
            return jsonify({"error":f"order with id {id} doesnt exist"}), 404
        return jsonify({'message':"its outta here"}), 200                 
    
# =====================Product CRUD Operations==========================

@app.post('/products')
def create_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    new_product = Product(
        name=product_data['name'],
        price=product_data['price'],
    )
    
    with Session(db.engine) as session:
        with session.begin():
            session.add(new_product)
            session.commit()
        return jsonify({'message': 'New product succesfully created'}), 201
    
@app.put('/products/<int:id>')
def update_product(id):
     with Session(db.engine) as session:
        with session.begin():
            
            query = select(Product).filter(Product.product_id == id)
            result = session.execute(query).scalar()
            if result is None:
                return jsonify({'message': 'product not found'}), 404
            product = result 
            try:
                product_data = product_schema.load(request.json)
            except ValidationError as err:
                return jsonify(err.messages), 400
            for field, value in product_data.items():
                setattr(product, field, value)
                
            session.commit()
            return jsonify({'message': 'Succesfully Updated'})
        
@app.get('/products/<int:id>')
def get_product_by_id(id):
    with Session(db.engine) as session:
        product = session.execute(select(Product).filter_by(product_id=id)).scalar()
        if product:
            return jsonify(product_schema.dump(product)), 200
        else:
            return jsonify({'message': 'Product not found'}), 404
        
        
        
@app.get('/products')
def get_all_products():
    query = select(Product)
    result = db.session.execute(query).scalars()
    products = result.all()
    
    return products_schema.jsonify(products)


@app.delete('/products/<int:id>')
def delete_product(id):
    delete_statement = delete(Product).where(Product.product_id == id)
    with db.session.begin():
        result = db.session.execute(delete_statement)
        if result.rowcount == 0:
            return jsonify({"error": "product does not exist"}), 404
        return jsonify({'message': 'Product Succesfully deleted'}), 200
if __name__ == "__main__":
    



    app.run(debug=True, port=5000)