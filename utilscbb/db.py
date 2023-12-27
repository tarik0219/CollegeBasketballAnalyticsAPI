from tinydb import TinyDB, Query
from constants import constants
import os


dbfile = os.path.join(os.getcwd(), constants.dbFileName)
pafile = os.path.join(os.getcwd(), constants.paFileName)

def get_db():
    db = TinyDB(dbfile)
    query = Query()
    teamsTable = db.table('teams')
    return query,teamsTable

def get_db_pa():
    db = TinyDB(dbfile)
    query = Query()
    teamsTable = db.table('teams')
    return query,teamsTable