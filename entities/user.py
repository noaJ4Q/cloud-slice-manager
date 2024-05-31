class User:
    def __init__(self, username, password, role):
        self.username = username
        self.password = password
        self.role = role

    def toDBCollection(self):
        return {"username": self.username, "password": self.password, "role": self.role}
