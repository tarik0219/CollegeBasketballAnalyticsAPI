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




# class S3Storage(Storage):
#     def __init__(self, bucket, file):
#         self.bucket = bucket
#         self.file = file
#         self.client = boto3.resource('s3', aws_access_key_id="", aws_secret_access_key="")
#     def read(self):
#         obj = self.client.Object(self.bucket, self.file)
#         data = obj.get()

#         return json.loads(data['Body'].read())
#     def write(self, data):
#         self.client.Object(self.bucket, self.file).put(Body=json.dumps(data))
#     def close(self):
#         pass

# def get_db_s3():
#     db = TinyDB(bucket='cbbwebdb', file='cbbweb.json', storage=S3Storage)
#     query = Query()
#     teamsTable = db.table('teams')
#     return query,teamsTable

# def get_cache_s3():
#     db = TinyDB(bucket='cbbwebdb', file='oddsCache.json', storage=S3Storage)
#     query = Query()
#     cacheTable = db.table('cache')
#     return query,cacheTable

# def get_cs_s3():
#     db = TinyDB(bucket='cbbwebdb', file='conferenceStandings.json', storage=S3Storage)
#     query = Query()
#     cacheTable = db.table('cs')
#     return query,cacheTable 