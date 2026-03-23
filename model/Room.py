class Room:
    def __init__(self, room_code, room_name, capacity, description):
        self.room_code = room_code
        self.room_name = room_name
        self.capacity = capacity
        self.description = description

    def __str__(self):
        return f"{self.room_code}\t{self.room_name}\t{self.capacity}\t{self.description}"
