class Music:
    def __init__(self, data) -> None:
        self.id = data["id"]
        self.author = data["authorName"]
        self.title = data["title"]
        self.link = data["playUrl"]
        self.cover = data["coverLarge"]
        self.duration = data["duration"]
        
