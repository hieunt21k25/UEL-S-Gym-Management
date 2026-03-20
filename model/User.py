class User:
    def __init__(self, user_id, username, email, password, role):
        self.user_id  = user_id
        self.username = username
        self.email    = email
        self.password = password   # plaintext for local JSON storage
        self.role     = role       # "admin" | "staff"
