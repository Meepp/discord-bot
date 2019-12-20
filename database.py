import sqlite3


class DataBase():
    def __init__(self, name):
        self.conn = sqlite3.connect(name)
        self._create_table()

    def _create_table(self):
        c = self.conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS triggers (trigger text UNIQUE, response text, creator text)")
        self.conn.commit()

    def execute(self, query):
        c = self.conn.cursor()
        c.execute(query)

        self.conn.commit()

    def delete_trigger(self, trigger):
        c = self.conn.cursor()
        c.execute("DELETE FROM triggers WHERE trigger = '" + trigger + "'")

        self.conn.commit()

    def select_all(self):
        c = self.conn.cursor()
        return c.execute("SELECT * FROM triggers")

    def select(self, query):
        c = self.conn.cursor()
        return c.execute(query)
        
    def finalize(self):
        self.conn.close()