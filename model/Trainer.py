class Trainer:
    def __init__(self, trainer_id, full_name, phone, specialty, availability_schedule,
                 experience_years=0, total_trainees=0, rating=5.0):
        self.trainer_id             = trainer_id
        self.full_name              = full_name
        self.phone                  = phone
        self.specialty              = specialty
        self.availability_schedule  = availability_schedule
        self.experience_years       = int(experience_years)
        self.total_trainees         = int(total_trainees)
        self.rating                 = float(rating)
