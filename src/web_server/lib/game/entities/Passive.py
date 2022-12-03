

class Passive(object):
    def __init__(self, time, callback, name="", args=()):
        self.name = name
        self.total_time = time
        self.time = time
        self.callback = callback
        self.args = args

    def tick(self):
        self.time -= 1
        if self.time == 0:
            self.callback(*self.args)

    def to_json(self):
        """
        Converts the passive to json, maybe for later to display all active passives

        :return:
        """
        return {
            "name": self.name,
            "time": self.time,
            "total_time": self.total_time,
        }
