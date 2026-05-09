class Product:
    def __init__(self, id, name, description, price, category, image_url, stock):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.category = category
        self.image_url = image_url
        self.stock = stock

class Order:
    def __init__(self, id, customer_name, customer_email, customer_phone, 
                 customer_address, total_amount, status, created_at):
        self.id = id
        self.customer_name = customer_name
        self.customer_email = customer_email
        self.customer_phone = customer_phone
        self.customer_address = customer_address
        self.total_amount = total_amount
        self.status = status
        self.created_at = created_at

class OrderItem:
    def __init__(self, id, order_id, product_id, quantity, price):
        self.id = id
        self.order_id = order_id
        self.product_id = product_id
        self.quantity = quantity
        self.price = price