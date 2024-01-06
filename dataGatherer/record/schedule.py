import os
import sys
from tinydb.operations import set
from utilscbb.appsync import get_schedule_data
from constants.constants import year
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import concurrent.futures

def load_url(team):
    response = get_schedule_data(team['id'], year, True)
    return response

def get_schedule_data_concurrent(data):
    teamData = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        future_to_url = {executor.submit(load_url, team): team for team in data}
        for future in concurrent.futures.as_completed(future_to_url):
            team = future_to_url[future]
            try:
                test = future.result()
                teamData[team['id']] = test
            except Exception as exc:
                print('error running concurrently: ' + str(exc))
    return teamData




def add_records_teams(teamsTable, query):
    data = teamsTable.all()
    teamData = get_schedule_data_concurrent(data)
    send = []
    for team in data:
        response = teamData[team['id']]
        records = response['scheduleData']['records']
        send.append((set("record", records), query.id == team['id']))
    teamsTable.update_multiple(send)
