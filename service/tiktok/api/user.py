

class User:
    def __init__(self, data) -> None:
        self.id = data["id"]
        self.unique_name = data["uniqueId"].replace('<', '\\<').replace('>', '\\>')
        self.name = data["nickname"]

        self.avatart = data["avatarLarger"]
        self.signature = data["signature"].replace('<', '\\<').replace('>', '\\>')
        self.verified = data["verified"]
