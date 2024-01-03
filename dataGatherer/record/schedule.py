import os
import sys
from tinydb.operations import set
from utilscbb.appsync import get_schedule_data
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))




def add_records_teams(year,teamsTable,query):
    data = teamsTable.all()
    for team in data:
        response = get_schedule_data(team['id'], year, True)
        records = response['scheduleData']['records']
        teamsTable.update(set("record", records), query.id == team['id'])
