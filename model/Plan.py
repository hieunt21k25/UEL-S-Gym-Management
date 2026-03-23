class Plan:
    def __init__(self, plan_id, member_id, trainer_id, goal, weekly_schedule_json, notes):
        self.plan_id              = plan_id
        self.member_id            = member_id
        self.trainer_id           = trainer_id
        self.goal                 = goal
        self.weekly_schedule_json = weekly_schedule_json  # JSON string
        self.notes                = notes
