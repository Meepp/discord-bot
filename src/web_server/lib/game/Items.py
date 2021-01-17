class Item:
    def __init__(self):
        self.name = ""


    def to_json(self):
        return {
            "name": self.name
        }


class TestItem(Item):
    def __init__(self):
        super().__init__()
        self.name = "TestItem"

