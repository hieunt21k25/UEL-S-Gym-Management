class CheckIn:
    def __init__(self, checkin_id, member_id, timestamp):
        self.checkin_id = checkin_id
        self.member_id  = member_id
        self.timestamp  = timestamp  # ISO 8601: YYYY-MM-DDTHH:MM:SS
