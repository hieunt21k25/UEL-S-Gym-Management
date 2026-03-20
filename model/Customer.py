class Customer:
    def __init__(self, customer_code, customer_name, customer_phone, customer_email, customer_identity):
        self.customer_code = customer_code
        self.customer_name = customer_name
        self.customer_phone = customer_phone
        self.customer_email = customer_email
        self.customer_identity = customer_identity

    def __str__(self):
        return f"{self.customer_code}\t{self.customer_name}\t{self.customer_phone}\t{self.customer_email}\t{self.customer_identity}"
