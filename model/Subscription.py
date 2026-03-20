class Subscription:
    def __init__(self, sub_id, member_id, package_id, start_date, end_date, status):
        self.sub_id     = sub_id
        self.member_id  = member_id
        self.package_id = package_id
        self.start_date = start_date  # YYYY-MM-DD
        self.end_date   = end_date    # YYYY-MM-DD
        self.status     = status      # active | expired | cancelled
