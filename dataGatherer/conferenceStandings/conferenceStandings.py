import requests
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
import random
import copy
from utilscbb.config import apiKey
import concurrent.futures
from utilscbb.schedule import get_team_schedule
from constants.constants import year, netRankBool

def call_team_data():
    url = "https://koric2.pythonanywhere.com/teamData"
    payload={}
    response = requests.request("GET", url, data=payload).json()
    return response

def get_schedule_query():
    stringQuery = """
        query ($teamID: String!, $year: Int!, $netRank: Boolean!) {
          scheduleData(teamID: $teamID, year: $year, netRank: $netRank) {
            teamID
            games {
                  completed
                  winProbability
                  opponentId
                  homeTeamId
                  gameType
                }
    
            records {
              confLoss
              confWin
            }
                }
        }
        """
    return stringQuery

def get_standings_games(conference, teamData):
    teamIds = []
    for team in teamData:
        if team['conference'] == conference:
            teamIds.append(team['id'])

    conferenceGames = []
    standings = {}
    for team in teamIds:
        response = get_team_schedule(team,year,netRankBool)
        standings[response['teamID']] = response['records']
        for game in response['games']:
            if game['gameType'] == 'CONF' and game['completed'] == False and game['homeTeamId'] == response['teamID']:
                conferenceGames.append(
                    {
                        'homeTeamId': response['teamID'],
                        'awayTeamId': game['opponentId'],
                        'proobability': game['winProbability']
                    }
                )
    return conferenceGames, standings

def get_random_number():
    return random.random()


def simulate_standings(conferenceGames, standings):
    for game in conferenceGames:
        if game['proobability'] > get_random_number():
            standings[game['homeTeamId']]['confWin'] += 1
            standings[game['awayTeamId']]['confLoss'] += 1
        else:
            standings[game['homeTeamId']]['confLoss'] += 1
            standings[game['awayTeamId']]['confWin'] += 1
    return standings

def order_standings(standings):
    orderedStandings = []
    for team in standings:
        orderedStandings.append(
            {
            'teamID': team,
            'confWin': standings[team]['confWin'],
            'confLoss': standings[team]['confLoss'],
            'randomFactor': random.random()  # Add a random factor for each team
        }
        )
    orderedStandings.sort(key=lambda x: (x['confWin'], x['randomFactor']), reverse=True)
    return orderedStandings


def get_simulated_standings(conference, teamData):
    print(conference)
    teams = {}
    n = 1000
    conferenceGames, standings = get_standings_games(conference, teamData)
    for i in range(n):
        standingsCopy = copy.deepcopy(standings)
        newStandings = simulate_standings(conferenceGames, standingsCopy)
        orderedStandings = order_standings(newStandings)
        for count,team in enumerate(orderedStandings):
            if team['teamID'] not in teams:
                teams[team['teamID']] = {}
                for i in range(1,len(orderedStandings)+1):
                    teams[team['teamID']][i] = 0    
            teams[team['teamID']][count + 1] += 1

    for team in teams:
        for place in teams[team]:
            teams[team][place] = round(teams[team][place] / n * 100,2)
    return teams

def get_all_unique_conferences():
    response = call_team_data()
    conferences = []
    for team in response:
        if team['conference'] not in conferences and team['conference'] != "IND":
            conferences.append(team['conference'])
    return conferences, response



def get_conference_standings_odds():
    conferenceStandingsMap = {}
    conferences, teamData = get_all_unique_conferences()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(get_simulated_standings, conference, teamData): conference for conference in conferences}
        for future in concurrent.futures.as_completed(future_to_url):
            conferenceData = future_to_url[future]
            try:
                conferenceStandingsMap[conferenceData] = future.result()
            except Exception as exc:
                print('error running concurrently: ' + str(exc))    
    return conferenceStandingsMap