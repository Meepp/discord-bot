import csv

def get_database():
    from pymongo import MongoClient
    import pymongo

    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    CONNECTION_STRING = "mongodb+srv://dtenw:0dZNkL6h8y1CGUNr@cluster0.wvrda.mongodb.net/discord-bot?retryWrites=true&w=majority"

    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    from pymongo import MongoClient
    client = MongoClient(CONNECTION_STRING)

    # Create the database for our example (we will use the same database throughout the tutorial
    return client['discord-bot']

# This is added so that many files can reuse the function get_database()
if __name__ == "__main__":
    # Get the database
    dbname = get_database()

    # tables = ['song', 'triggers']
    # for table_name in tables:
    #     with open(f'D:\Github\discord-bot\{table_name}.csv', newline='', encoding='utf-8') as csvfile:
    #         data = list(csv.reader(csvfile, delimiter=','))
    #         if len(data) != 0:
    #             headers = data[0]
    #             output = []
    #             for row in data[1:]:
    #                 entity = {}
    #                 for i, column in enumerate(row):
    #                     entity[headers[i]] = column
    #                 output.append(entity)
    #             collection = dbname[table_name]
    #             collection.insert_many(output)

