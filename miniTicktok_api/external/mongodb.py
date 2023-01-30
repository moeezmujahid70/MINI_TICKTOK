import pymongo
from pymongo import MongoClient
from pymongo.database import Database


class MongodbDatabase:
    client: MongoClient
    database: Database

    def __init__(self, uri, database: str):
        self.client = pymongo.MongoClient(f"mongodb://{uri}")
        self.database = self.client.get_database(database)
