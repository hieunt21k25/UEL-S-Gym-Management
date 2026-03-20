class Payment:
    def __init__(self, payment_id, member_id, amount, method, date, note, related_subscription_id):
        self.payment_id              = payment_id
        self.member_id               = member_id
        self.amount                  = amount    # float
        self.method                  = method    # cash | bank | card
        self.date                    = date      # YYYY-MM-DD
        self.note                    = note
        self.related_subscription_id = related_subscription_id  # or ""
