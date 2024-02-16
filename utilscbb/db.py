from tinydb import TinyDB, Query
from tinydb.storages import Storage
from constants import constants
import os
import json

LOCAL_PATH = os.path.join(os.getcwd(), constants.LOCAL_PATH)
PYTHON_ANYWHERE_PATH = os.path.join(os.getcwd(), constants.PYTHON_ANYWHERE_PATH)



def get_db_name(fileName, tableName):
    if os.path.exists(LOCAL_PATH):
        filePath = os.path.join(LOCAL_PATH, fileName)
    else:
        filePath = os.path.join(PYTHON_ANYWHERE_PATH, fileName)
    db = TinyDB(filePath)
    teamsTable = db.table(tableName)
    query = Query()
    return query,teamsTable



class Database:
    def __init__(self, filePath, tableName):
        try:
            self.db = TinyDB(filePath)
        except:
            self.db = TinyDB("CollegeBasketballAnalyticsAPI/"+filePath)
        self.table = self.db.table(tableName)
        self.query = Query()
        
    #insert data into the table
    def insert(self, data):
        self.table.insert(data)

    def upsert(self, data, id):
        self.table.upsert(data, self.query.id == id)
    
    def _add_multi_key(self, data, keys):
        def transform(doc):
            key = keys.pop(0)
            if len(keys) == 0:
                doc[key] = data
            else:
                if key in doc:
                    transform(doc[key])
        return transform
    
    def teamsToDict(self):
        teamData = self.table.all()
        teamDict = {}
        for team in teamData:
            teamDict[team['id']] = team
        return teamDict

    def updateByKeys(self, data, id, keys):
        self.table.update(self._add_multi_key(data, keys), self.query.id == id)

    def queryById(self, id):
        items = self.table.search(self.query.id == id)
        if len(items) > 0:
            return items[0]
        else:
            return None