class Member:
    def __init__(self, member_id, full_name, phone, email, dob, gender, join_date, status):
        self.member_id = member_id
        self.full_name = full_name
        self.phone     = phone
        self.email     = email
        self.dob       = dob        # YYYY-MM-DD
        self.gender    = gender     # Male | Female | Other
        self.join_date = join_date  # YYYY-MM-DD
        self.status    = status     # active | inactive
