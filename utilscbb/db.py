from tinydb import TinyDB, Query
from tinydb.storages import Storage
from constants import constants
import os
import boto3
import json

dbfile = os.path.join(os.getcwd(), constants.dbFileName)
pafile = os.path.join(os.getcwd(), constants.paFileName)

cacheFile = os.path.join(os.getcwd(), constants.cacheFileName)
paCacheFile = os.path.join(os.getcwd(), constants.paCacheFileName)

csFile = os.path.join(os.getcwd(), constants.csFileName)
paCsFile = os.path.join(os.getcwd(), constants.paCsFileName)

def get_db():
    db = TinyDB(dbfile)
    query = Query()
    teamsTable = db.table('teams')
    return query,teamsTable

def get_db_pa():
    db = TinyDB(pafile)
    query = Query()
    teamsTable = db.table('teams')
    return query,teamsTable


def get_cache():
    db = TinyDB(cacheFile)
    query = Query()
    cacheTable = db.table('cache')
    return query,cacheTable

def get_cache_pa():
    db = TinyDB(paCacheFile)
    query = Query()
    cacheTable = db.table('cache')
    return query,cacheTable

def get_cs():
    db = TinyDB(csFile)
    query = Query()
    cacheTable = db.table('cs')
    return query,cacheTable

def get_cs_pa():
    db = TinyDB(paCsFile)
    query = Query()
    cacheTable = db.table('cs')
    return query,cacheTable





class S3Storage(Storage):
    def __init__(self, bucket, file):
        self.bucket = bucket
        self.file = file
        self.client = boto3.resource('s3', aws_access_key_id="", aws_secret_access_key="")
    def read(self):
        obj = self.client.Object(self.bucket, self.file)
        data = obj.get()

        return json.loads(data['Body'].read())
    def write(self, data):
        self.client.Object(self.bucket, self.file).put(Body=json.dumps(data))
    def close(self):
        pass

def get_db_s3():
    db = TinyDB(bucket='cbbwebdb', file='cbbweb.json', storage=S3Storage)
    query = Query()
    teamsTable = db.table('teams')
    return query,teamsTable

def get_cache_s3():
    db = TinyDB(bucket='cbbwebdb', file='oddsCache.json', storage=S3Storage)
    query = Query()
    cacheTable = db.table('cache')
    return query,cacheTable

def get_cs_s3():
    db = TinyDB(bucket='cbbwebdb', file='conferenceStandings.json', storage=S3Storage)
    query = Query()
    cacheTable = db.table('cs')
    return query,cacheTable 