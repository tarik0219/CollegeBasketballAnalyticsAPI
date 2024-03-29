import os
import sys
from tinydb.operations import set
from constants import constants
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import concurrent.futures
from utilscbb.schedule import get_team_schedule

def load_url(team):
    response = get_team_schedule(team['id'], constants.YEAR, constants.NET_RANK_BOOL)
    return response

def get_schedule_data_concurrent(data):
    teamData = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
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
        records = response['records']
        send.append((set("record", records), query.id == team['id']))
    teamsTable.update_multiple(send)
