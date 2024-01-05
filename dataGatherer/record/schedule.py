import os
import sys
from tinydb.operations import set
from utilscbb.appsync import get_schedule_data
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))




def add_records_teams(year,teamsTable,query):
    data = teamsTable.all()
    send = []
    for count,team in enumerate(data):
        response = get_schedule_data(team['id'], year, True)
        records = response['scheduleData']['records']
        send.append((set("record", records), query.id == team['id']))
    teamsTable.update_multiple(send)
