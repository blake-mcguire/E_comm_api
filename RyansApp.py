# INSTALLS NEEDED 
# pip install flask sqlalchemy flask-sqlalchemy flask-marshmallow marshmallow-sqlalchemy mysql-connector-python (install on the folder that houses evrything)
# push all requirments to a tewxt file - pip freeze > requirements.txt
# enable cross resource communication pip install flask-cors

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




app = Flask(__name__)
CORS(app) #initializes CORS for our application
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqlconnector://root:Buttmuffin3!@localhost/e_commerce_db2"
#  'mysql+mysqlconnector://root:your_password@localhost/e_commerce_db'
#                           user  password                database name

# create a Base class for all of our Models (classes that become tables) to inherit from
# the child classes can then create attributes that become columns inside of tables in our db
# objects from those tables create rows of data in our db
class Base(DeclarativeBase):
    pass

# instantiate our db
db = SQLAlchemy(app, model_class=Base) #tells the db instance that we use the Base class for the model functionality
# model - class that becomes a table in the db
ma = Marshmallow(app) # creating a marshmallow object for the schema creation



# ========================= DB MODELS ==============================
class Customer(Base): #importing the Base class gives this class model functionality
    __tablename__ = "Customers" # sets the name of the table in our database
    # type hinting - column name is an attribute and we're creating a ty
    # variable_name: type <-- type hinting, what is the expected type for this variable    
    customer_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(320), nullable=False)
    phone: Mapped[str] = mapped_column(db.String(15))
    # one-to-one relationship with customer account
    customer_account: Mapped["CustomerAccount"] = db.relationship(back_populates="customer")
    # create a one-to-many relationship with Order
    orders: Mapped[List["Order"]] = db.relationship(back_populates="customer")

# Customer Account with a one to one relationship with the Customer table
class CustomerAccount(Base):
    __tablename__ = "Customer_Accounts"
    # attribute_name: attribute type = any constraints for that column
    account_id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(db.String(255), nullable = False)
    # create the foreign key from the customer table
    customer_id: Mapped[int] = mapped_column(db.ForeignKey('Customers.customer_id'))
    # create the back reference relationship between objects of the classes
    customer: Mapped["Customer"] = db.relationship(back_populates="customer_account")

# associate table between orders and products to manage the many to many relationship
order_product = db.Table(
    "Order_Product", #association table name
    Base.metadata,
    db.Column("order_id", db.ForeignKey("Orders.order_id"), primary_key=True),
    db.Column("product_id", db.ForeignKey("Products.product_id"), primary_key=True)      
)

# creating Orders and a one to many relationship bewtween Customer and Order
class Order(Base):
    __tablename__ = "Orders"

    order_id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime.date] = mapped_column(db.Date, nullable = False)
    # creating relationship with Customer 
    customer_id: Mapped[int] = mapped_column(db.ForeignKey("Customers.customer_id"))
    # Many-to-one relation from order to customer
    customer: Mapped["Customer"] = db.relationship(back_populates="orders")
    # Many to many with product, with no back populates
    products: Mapped[List["Product"]] = db.relationship(secondary=order_product)

    def make_order(self, order_id, product_id):
        self.products.append(product_id)
        # db.session.commit()
        
        
        
class Product(Base):
    __tablename__ = "Products"
    product_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    price: Mapped[float] = mapped_column(db.Float, nullable=False)

# using context manager to create tables in our db
with app.app_context():
    # db.drop_all() drop all tables currently in the database
    db.create_all() #create tables if they dont exist, if they do exist, it does nothing


# Customer Schema
class CustomerSchema(ma.Schema):
    customer_id = fields.Integer()
    name = fields.String(required=True)
    email = fields.String(required=True)
    phone = fields.String(required=True)

    class Meta:
        # fields to expose (what is displayed during a GET request)
        fields = ("customer_id", "email", "name", "phone")

# instantiating our Schemas
customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)


# ======================================== API ROUTES ======================================================
# CUSTOMERS
# get all customers
@app.route("/customers", methods = ["GET"])
def get_customers():
    query = select(Customer) #using the select method from our ORM(SQLAlchemy) 
    # to run a SELECT query == SELECT * FROM Customers
    # uses the python class as representation for the Customers table
    result = db.session.execute(query).scalars() # returns a list of customer objects (instances of the customer class)
    # rather than a list of rows or tuples
    customers = result.all() #fetches all rows of data from the result

    # convert to json through the instance of the CustomerSchema class
    return customers_schema.jsonify(customers)

# add a customer
@app.route("/customers", methods = ["POST"])
def add_customer():
    try:
        # validate the incoming data from the request
        # making sure it adheres to our schema
        customer_data = customer_schema.load(request.json)
    
    except ValidationError as err:
        return jsonify(err.messages), 400 #Bad Request - insufficient data or mismatched type
    
    # start the db session using the Session import
    # instantiate the Session class with a context manager
    with Session(db.engine) as session: #temporarily instantiates Session to get access to a session object 
        with session.begin(): #Start the db transaction to post data
            name = customer_data['name']
            email = customer_data['email']
            phone = customer_data['phone']

            new_customer = Customer(name=name, email=email, phone=phone) 
            # INSERT INTO Customers (name, email, phone) VALUES(%s, %s, %s)
            # new_customer = (name, email, phone)
            session.add(new_customer)
            session.commit()
    
    return jsonify({"message": "New Customer successfully added!"}), 201 # new resource was created
    
# UPDATE a Customer
@app.route("/customers/<int:id>", methods=["PUT"])
def update_customer(id):
    with Session(db.engine) as session:
        with session.begin():
            # select the customer who's data we'd like to update
            #                         WHERE customer_id = id
            query = select(Customer).filter(Customer.customer_id == id)
            # grabbing the first first result from scalars, returning the object out of the list of results
            result = session.execute(query).scalars().first()
            if result is None:
                return jsonify({"message": "Customer not found"}), 404 # resource not found
            
            # setting a variable to the result
            customer = result

            try: 
                # validate incoming data to update the customer object above
                customer_data = customer_schema.load(request.json)
            except ValidationError as err:
                return jsonify(err.messages), 400 #Bad Request
            
            # update the customer object with the values from the incoming data
            # and then commit the changes
            for field, value in customer_data.items():
                setattr(customer, field, value)

            session.commit() #commits the transaction

    return jsonify({"message": "Customer details updated successfully"}), 200 #Successful request


@app.route("/customers/<int:id>", methods=["DELETE"])
def delete_customer(id):
    # delete_statement = delete(Customer).where(Customer.customer_id == id)
    with Session(db.engine) as session:
        with session.begin():
            query = select(Customer).filter(Customer.customer_id == id)
            result = session.execute(query).scalars().first()
            
            if result is None:
                return jsonify({"error": "Customer not found..."}), 404 #not found
            
            session.delete(result) #delete within the session
            
            # delete_statement = delete(Customer).where(Customer.customer_id == id)

            # result = db.session.execute(delete_statement)
            # print(result)
            # print(result.rowcount)

            # if result.rowcount == 0:
            #     return jsonify({"error": "Customer not found."}), 404

        return jsonify({"message": "Customer removed successfully!"})

#----------------------------------------------------------------------------------
#products 
#we need a schema here (it will have the product_id, name, price)
#product schema with validation rules implemented
class ProductSchema(ma.Schema):
    product_id = fields.Integer(required=False)
    name = fields.String(required=True, validate=validate.Length(min=1)) 
    price = fields.Float(required=True, validate=validate.Range(min=0))

    class Meta:
        fields = ("product_id", "name", "price")

#instance of schema 
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

#routes

#get products
#i need to say "hey python and sql i need everything from products" select * from products

@app.route("/products", methods=["GET"])
def get_products():
    query = select(Product) #SELECT * FROM product
    result = db.session.execute(query).scalars()
    products = result.all()

    return products_schema.jsonify(products) #print it this way 

#what if i wanted to get a product by its name?
@app.route("/products/by-name", methods=["GET"])
def get_products_by_name():
    name = request.json.get("name")
    search = f"%{name}%" # % is like a wildcard in sql 
    # use % with LIKE to find partial matches 
    query = select(Product).where(Product.name.like(search)).order_by(Product.price.asc())
    products = db.session.execute(query).scalars().all()
    print(products)

    return products_schema.jsonify(products)

#create products
#i need a name and price for my product from the user 
#make sure data given is valid

@app.route("/products", methods=["POST"])
def add_product():
    try:
        #validate everything
        product_data = product_schema.load(request.json)
    except ValidationError as err:
        #Hey you messed up, let em know
        return jsonify(err.messages) , 400 # BAD REQUEST - not enough or mismatched data
    # we need our session!
    with Session(db.engine) as session:
        with session.begin():
            #create our product instance!
            new_product = Product(name=product_data['name'],price= product_data['price'])
            session.add(new_product)
            session.commit()
    # return our success message
    return jsonify({"Message": "new product added successfully"}) , 201 #new resource created

#update products by ID
#need an id for the product we want to update (slug)
@app.route("/products/<int:product_id>", methods =["PUT"])
def update_product(product_id):
    with Session(db.engine) as session:
        with session.begin():
            #then we have to find the product in the db
            query = select(Product).filter(Product.product_id == product_id)
            result = session.execute(query).scalar() # this is the same as scalars().first() - first result
            print(result)
            if result is None:
                #no product found
                return jsonify({"error": "Product not found"}), 404 # not found
            product = result
            try:
                product_data = product_schema.load(request.json)
            except ValidationError as err:
                #always let em know when they mess it up
                return jsonify(err.messages), 400 # Bad request
            
            #once we have the product and valid data, we can update!
            for field, value in product_data.items():
                setattr(product,field, value)
            #save to db
            session.commit()
            return jsonify({"Message":f"Product with id of {product_id} updated successfully"}), 200 # update successful
#delete products
#i need an id to do so.
@app.delete("/products/<int:product_id>")
def delete_product(product_id):
    #find product
    delete_statment = delete(Product).where(Product.product_id == product_id)
    with db.session.begin():
        result = db.session.execute(delete_statment)
        if result.rowcount == 0:
        #if product isnt there, let em know
            return jsonify({"error":f"Product with id of {product_id} doesn't exist!"}), 404
    #if it is, we can chuck it!
        return jsonify({"message":"Product is gone, probably"}), 200


#----------------------------------------------------------------------------------------------

#orders 
#need a schema (order_id,customer_id,date, product_id)
class OrderSchema(ma.Schema):
    order_id = fields.Integer(required= False)
    customer_id = fields.Integer(required = True)
    date = fields.Date(required=True) #"2024-07-05"
    product_id = fields.List(fields.Integer(), required= False)

    class Meta:
        fields = ("order_id","customer_id","date","product_id")
    

#Instance of schemas
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

#routes 


#get orders
#select * from orders
@app.get("/orders")
def get_orders():
    query = select(Order) #select * from order
    result = db.session.execute(query).scalars().all()
    orders_with_products = []
    orders = result
    for order in orders:
        order_dict = {
            "order_id": order.order_id,
            "customer_id": order.customer_id,
            "date": order.date,
            "products": [product.product_id for product in order.products]
        }
        orders_with_products.append(order_dict)

    return jsonify(orders_with_products)

# def get_orders():
#     query = select(Order) #select * from order
#     result = db.session.execute(query).scalars().all()
#     return orders_schema.jsonify(result)



#create orders
@app.post("/orders")
def add_order():
    # i need to have my data from the user (request)
    try:
        #i need to validate the data
        order_data = order_schema.load(request.json)
    except ValidationError as err:    
        #if not valid then throw error
        return jsonify(err.messages), 400
    product_ids = order_data.get('product_id', [])

    # Create new order instance
    new_order = Order(
        customer_id=order_data['customer_id'],
        date=order_data['date']
    )

    # Retrieve products within the session context
    with Session(db.engine) as session:
        with session.begin():
            # Associate products with the order
            for product_id in product_ids:
                new_order.make_order(product_id)
                # product = session.query(Product).get(product_id)
                # if product:
                #     new_order.products.append(product)

            # Save order and associated products to the database
            session.add(new_order)
            session.commit()

    return jsonify({"message": "Order added successfully"}), 201




#update orders by ID
@app.put("/orders/<int:order_id>")
def update_orders(order_id):
    with Session(db.engine) as session:
        with session.begin():
            # i need the id of the order i want to update
            query = select(Order).filter(Order.order_id == order_id)
            result = session.execute(query).scalar() #this is going to get the first object back to me
            #check and see if that order exists
            if result is None:
                #if doesnt, let  em know
                return jsonify({"message":"Order not found!"})
            order = result
            #if it does, validate new order data
            try:
                order_data = order_schema.load(request.json)
            except ValidationError as err:
                return jsonify(err.messages), 400
            #we can now update our order
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
            return jsonify({"message":f"Order with the id if {order_id} has been updated!"}), 200
    

#del orders ( im gonna need an id)
@app.delete("/orders/<int:order_id>")
def delete_order(order_id):
    delete_statement = delete(Order).where(Order.order_id == order_id)
    with db.session.begin():
        result = db.session.execute(delete_statement)
        if result.rowcount == 0:
            return jsonify({"Error":f"Order with id {order_id} doesnt exist"})
        return jsonify({"message":"Its outta here! "})



