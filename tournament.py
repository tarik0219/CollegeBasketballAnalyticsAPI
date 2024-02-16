import os
import pickle
import numpy as np
import concurrent.futures
from constants import constants
from utilscbb.db import get_db_name
from utilscbb.schedule import get_team_schedule
from utilscbb.espn import call_espn_team_standings_api

def warn(*args, **kwargs):
    pass

import warnings
warnings.warn = warn

# Load the tournament model
try:
    tournamentFile = os.path.join(os.getcwd(), "models/tournamentModel.pkl")
    with open(tournamentFile, 'rb') as f:
        model = pickle.load(f)
except:
    tournamentFile = os.path.join(os.getcwd(), "CollegeBasketballAnalyticsAPI/models/tournamentModel.pkl")
    with open(tournamentFile, 'rb') as f:
        model = pickle.load(f)

# Get all team data
def get_all_team_data():
    query, teamsTable = get_db_name(constants.TEAMS_DATA_FILE, constants.TEAMS_TABLE_NAME)
    teams = teamsTable.all()
    teamRecords = call_espn_team_standings_api(constants.YEAR)
    for count, team in enumerate(teams):
        newTeamRecord = teamRecords[team['id']]
        team['record'].update(newTeamRecord)
        teams[count]['record'] = team['record']
    return teams

allTeamData = get_all_team_data()

#open conferenceWinners.txt and save each line into a set
conferenceWinners = set()
try:
    with open('data/conferenceWinners.txt', 'r') as f:
        for line in f:
            conferenceWinners.add(line.strip())
except:
    with open('CollegeBasketballAnalyticsAPI/data/conferenceWinners.txt', 'r') as f:
        for line in f:
            conferenceWinners.add(line.strip())


# Get conference champions
conferenceChampions = {}
championTeams = set()
for team in allTeamData:
    if team['teamName'] in conferenceWinners:
        conferenceChampions[team['conference']] = team['teamName']
        championTeams.add(team['teamName'])
    elif team['record']['conferenceStanding'] == 1 and team['conference'] != "IND" and team['conference'] not in conferenceChampions:
        conferenceChampions[team['conference']] = team['teamName']
        championTeams.add(team['teamName'])

# Save conference champions to a text file
try:
    with open('data/champions.txt', 'w') as f:
        for team in championTeams:
            f.write(team + '\n')
except:
    with open('CollegeBasketballAnalyticsAPI/data/champions.txt', 'w') as f:
        for team in championTeams:
            f.write(team + '\n')

# Calculate tournament odds for each team
tournamentTeamOdds = []
def calculate_odds(team):
    if team['teamName'] not in championTeams:
        teamSchedule = get_team_schedule(team['id'], 2024, True)
        win = teamSchedule['records']['projectedWin']
        loss = teamSchedule['records']['projectedLoss']
        q1w = teamSchedule['projectedQuadRecords']['quad1']['wins']
        q1l = teamSchedule['projectedQuadRecords']['quad1']['losses']
        q2w = teamSchedule['projectedQuadRecords']['quad2']['wins']
        q2l = teamSchedule['projectedQuadRecords']['quad2']['losses']
        q3w = teamSchedule['projectedQuadRecords']['quad3']['wins']
        q3l = teamSchedule['projectedQuadRecords']['quad3']['losses']
        q4w = teamSchedule['projectedQuadRecords']['quad4']['wins']
        q4l = teamSchedule['projectedQuadRecords']['quad4']['losses']
        rank = teamSchedule['teamData']['ranks']['net_rank']
        input = np.array([[win, loss, q1w, q1l, q2w, q2l, q3w, q3l, q4w, q4l, rank]])
        odds = model.predict_proba(input)[0][1]
        tournamentTeamOdds.append((team['teamName'], odds))

with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(calculate_odds, allTeamData)

# Sort tournament team odds
sorted_tournamentTeamOdds = sorted(tournamentTeamOdds, key=lambda x: x[1], reverse=True)

# Save tournament odds teams to a text file
try:
    with open('data/atLarge.txt', 'w') as f:
        for team in sorted_tournamentTeamOdds:
            f.write(team[0] + '\n')
except:
    with open('CollegeBasketballAnalyticsAPI/data/atLarge.txt', 'w') as f:
        for team in sorted_tournamentTeamOdds:
            f.write(team[0] + '\n')