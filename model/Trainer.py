class Trainer:
    def __init__(self, trainer_id, full_name, phone, specialty, availability_schedule):
        self.trainer_id             = trainer_id
        self.full_name              = full_name
        self.phone                  = phone
        self.specialty              = specialty
        self.availability_schedule  = availability_schedule  # free text or JSON string
