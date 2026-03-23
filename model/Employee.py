class Employee:
    def __init__(self, EmployeeId, EmployeeRole, UserName, Password):
        self.EmployeeId = EmployeeId
        self.EmployeeRole = EmployeeRole
        self.UserName = UserName
        self.Password = Password

    def __str__(self):
        return f"{self.EmployeeId}\t{self.EmployeeRole}\t{self.UserName}\t{self.Password}"
