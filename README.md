# E-Commerce API README

## Overview

This project is an e-commerce API built using Flask. It provides endpoints to manage customers, customer accounts, products, and orders. The application leverages SQLAlchemy for ORM (Object-Relational Mapping) and Marshmallow for data serialization and validation.

## Setup

### Prerequisites

- Python 3.x
- MySQL database
- Flask and its dependencies

### Installation

1. Clone the repository:
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2. Create a virtual environment and activate it:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

4. Configure the database URI in the `app.config`:
    ```python
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqlconnector://root:<password>@localhost/e_comm_db"
    ```

### Database Initialization

Run the following command to create the database tables:
```bash
flask db upgrade

# Running the Application

1. Start the Flask application:

- Run this code:
"flask run"

By default, the application runs on http://localhost:5000.

## API Endpoints
###  Customer Account Endpoints
1. Create a Customer Account
- URL: /customeraccount
- Method: POST
- Payload:
{
    "username": "example",
    "password": "password123",
    "customer_id": 1
}

- Response:

{
    "message": "customeraccount successfully instantiated"
}

2.Update a Customer Account
- URL: /customeraccount/<int:id>
- Method: PUT
-Payload:
{
    "username": "newusername",
    "password": "newpassword"
}

- Response:

{
    "message": "account successfully updated"
}
3. Get All Customer Accounts
- URL: /customeraccount
- Method: GET

- Response:

[
    {
        "account_id": 1,
        "customer_id": 1,
        "username": "example",
        "password": "password123"
    }
]

4. Get a Customer Account by ID
- URL: /customeraccount/<int:id>
- Method: GET
- Response:

{
    "account_id": 1,
    "customer_id": 1,
    "username": "example",
    "password": "password123"
}
5. Delete a Customer Account
- URL: /customeraccount/<int:id>
- Method: DELETE

- Response:

{
    "message": "customer account successfully deleted"
}

#Customer Endpoints

1. Create a Customer
- URL: /customers
- Method: POST
- Payload:

{
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "1234567890"
}

- Response:

{
    "message": "New Customer Created!"
}

2. Delete a Customer
- URL: /customers/<int:id>
- Method: DELETE

- Response:

{
    "message": "Customer with id <id> was deleted"
}

3. Update a Customer
- URL: /customers/<int:id>
- Method: PUT
- Payload:

{
    "name": "John Smith",
    "email": "john.smith@example.com",
    "phone": "0987654321"
}

- Response:

{
    "message": "customer with id <id> successfully updated"
}
3. Get All Customers
- URL: /customers
- Method: GET

- Response:

[
    {
        "customer_id": 1,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "1234567890"
    }
]

4. Get a Customer by ID
- URL: /customers/<int:id>
- Method: GET

- Response:

{
    "customer_id": 1,
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "1234567890"
}
# Order Endpoints
1. Create an Order
- URL: /orders
- Method: POST
- Payload:

{
    "customer_id": 1,
    "date": "2023-01-01",
    "product_id": [1, 2]
}

- Response:

{
    "message": "new order created"
}
2. Update an Order
- URL: /orders/<int:id>
- Method: PUT
- Payload:

{
    "customer_id": 1,
    "date": "2023-01-02",
    "product_id": [2, 3]
}

- Response:

{
    "message": "Order with the id <id> has been updated!"
}
3. Get All Orders
- URL: /orders
- Method: GET

- Response:

[
    {
        "order_id": 1,
        "customer_id" : 1,
        "date": "2023-01-01",
        "product": [1, 2]
    }
]

4. Get an Order by ID
- URL: /orders/<int:id>
- Method: GET
- Response:

{
    "order_id": 1,
    "customer_id": 1,
    "date": "2023-01-01",
    "product": [1, 2]
}

5. Delete an Order
- URL: /orders/<int:id>
- Method: DELETE

- Response:

{
    "message": "its outta here"
}

# Product Endpoints
1. Create a Product
- URL: /products
- Method: POST
- Payload:

{
    "name": "Product 1",
    "price": 9.99
}

- Response:

{
    "message": "New product successfully created"
}
2. Update a Product
- URL: /products/<int:id>
- Method: PUT
- Payload:

{
    "name": "Updated Product",
    "price": 19.99
}

- Response:

{
    "message": "Successfully Updated"
}
3. Get a Product by ID
- URL: /products/<int:id>
- Method: GET

- Response:

{
    "product_id": 1,
    "name": "Product 1",
    "price": 9.99
}
4. Get All Products
- URL: /products
- Method: GET

- Response:

[
    {
        "product_id": 1,
        "name": "Product 1",
        "price": 9.99
    }
]

5. Delete a Product
- URL: /products/<int:id>
- Method: DELETE

- Response:

{
    "message": "Product successfully deleted"
}
##Models
1. Customer
Attributes:
- customer_id: Integer, primary key
- name: String, required
- email: String, required
- phone: String, required

2. Customer Account
Attributes:
- account_id: Integer, primary key
- username: String, unique, required
- password: String, required
- customer_id: Integer, foreign key

3. Order
Attributes:
- order_id: Integer, primary key
- date: Date, required
- customer_id: Integer, foreign key
- products: List of products, many-to-many relationship

4. Product
Attributes:
- product_id: Integer, primary key
- name: String, required
- price: Float, required

### Error Handling
400: Bad Request - Returned when the request payload validation fails.
404: Not Found - Returned when the requested resource does not exist.
500: Internal Server Error - Returned for any other server errors.

### Cross-Origin Resource Sharing (CORS)
CORS is enabled to allow the application to be accessed by third-party clients.