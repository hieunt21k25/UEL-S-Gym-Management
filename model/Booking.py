class Booking:
    def __init__(self, customer_code, room_code, start_date, end_date):
        self.customer_code = customer_code
        self.room_code = room_code
        self.start_date = start_date
        self.end_date = end_date

    def __str__(self):
        return f"{self.customer_code}\t{self.room_code}\t{self.start_date}\t{self.end_date}"
