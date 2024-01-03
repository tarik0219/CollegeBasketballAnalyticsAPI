from tinydb import TinyDB, Query
from constants import constants
import os


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