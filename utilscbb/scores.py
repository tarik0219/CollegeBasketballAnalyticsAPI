import requests
import requests
import json
from datetime import datetime
from dateutil import tz
from utilscbb.db import get_db_name
from constants import constants
from utilscbb.predict import make_prediction_api
from utilscbb.espn import call_espn_scores_api
import time


def convertDateTime(dateTime):
    from_zone = tz.gettz("Africa/Accra")
    to_zone = tz.gettz('America/New_York')
    test = dateTime
    test = test.split("T")[0] + " " + test.split("T")[1].split("Z")[0]
    utc = datetime.strptime(test, "%Y-%m-%d %H:%M")
    utc = utc.replace(tzinfo=from_zone)
    eastern = str(utc.astimezone(to_zone))
    date = eastern.split(" ")[0]
    time = eastern.split(" ")[1].split("-")[0]
    return date, time


def get_team_data(teamID, teamsData):
    if teamID in teamsData:
        return teamsData[teamID]
    else:
        return {}

def get_prediction(homeData, awayData, neutralSite):
    if (len(homeData) == 0) or (len(awayData) == 0):
        return None, None, None
    homeScore,awayScore,prob = make_prediction_api(homeData['average'], awayData['average'], neutralSite)
    return homeScore,awayScore,prob

def add_line_data(oddsData, gameID):
    if gameID in oddsData:
        game = oddsData[gameID]
        return game
    else:
        return {"spread": None, "overUnder": None}
                
def get_teams_data_dict(teamsTable):
    teamsData = teamsTable.all()
    teamsDataDict = {}
    for team in teamsData:
        teamsDataDict[team['id']] = team
    return teamsDataDict

def get_odds_data_dict(query, oddsTable, espnScores):
    gameIds = list(espnScores.keys())
    oddsData = oddsTable.search(query.gameID.one_of(gameIds))
    oddsDataDict = {}
    for game in oddsData:
        oddsDataDict[game['gameID']] = game
    return oddsDataDict

def get_scores_data(date):
    espnScores = call_espn_scores_api(date)
    query,teamsTable = query,teamsTable = get_db_name(constants.TEAMS_DATA_FILE, constants.TEAMS_TABLE_NAME)
    teamsData = get_teams_data_dict(teamsTable)
    espnScoresList = []
    oddsQuery,oddsTable = get_db_name(constants.ODDS_CACHE_FILE, constants.ODDS_TABLE_NAME)
    oddsData = get_odds_data_dict(oddsQuery, oddsTable, espnScores)
    for gameId,game in espnScores.items():
        homeData = get_team_data(game['homeTeamId'], teamsData)
        awayData = get_team_data(game['awayTeamId'], teamsData)
        if game['status'] == 'post':
            homeScore, awayScore, prob = None, None, None
        else:
            homeScore,awayScore,prob = get_prediction(homeData, awayData, game['siteType'])
        odds = add_line_data(oddsData, gameId)
        game.update({
            "homeData": homeData,
            "awayData": awayData,
            "homeScorePredict": homeScore,
            "awayScorePredict": awayScore,
            "prob": prob,
            "spread": odds['spread'],
            "overUnder": odds['overUnder']
        })
        espnScoresList.append(game)
    return  espnScoresList



