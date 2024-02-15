import requests
from datetime import datetime
from dateutil import tz
import pytz
import json
import sys, os
from utilscbb.espn import call_espn_schedule_api
from utilscbb.db import get_db_name
from constants import constants
from utilscbb.predict import make_prediction_api
import time
import random
import copy
import json

# Specify the file path


quadMap = {
    "quad1": 1,
    "quad2": 2,
    "quad3": 3,
    "quad4": 4
}

mapQuad = {
    1:"quad1",
    2:"quad2",
    3:"quad3",
    4:"quad4"
}

def quad_rank(opponent_rank,venue):
    if (opponent_rank <= 30 and venue == 'H') or (opponent_rank <= 50 and venue == 'N') or (opponent_rank <= 75 and venue == '@'):
        quad = "quad1"
    elif (opponent_rank <= 75 and venue == 'H') or (opponent_rank <= 100 and venue == 'N') or (opponent_rank <= 135 and venue == '@'):
        quad = "quad2"
    elif (opponent_rank <= 160 and venue == 'H') or (opponent_rank <= 200 and venue == 'N') or (opponent_rank <= 240 and venue == '@'):
        quad = "quad3"
    else:
        quad = "quad4"
    return quad

def team_data_to_dict(teamData):
    teamDict = {}
    for team in teamData:
        teamDict[team['id']] = team
    return teamDict

def change_game_type(teamData, opponentData, gameType, date, notes):
    if gameType == "POST":
        return "POST"
    if opponentData:
        if teamData['conference'] == opponentData['conference']:
            if len(notes) == 0:
                return "CONF"
            else:
                return "CONFTOUR"
    return "REG"

def add_odds(espnResponse):
    gameIDs = []
    for game in espnResponse:
        gameIDs.append(game['gameId'])
    query, oddsTable = get_db_name(constants.ODDS_CACHE_FILE, constants.ODDS_TABLE_NAME)
    odds = oddsTable.search(query.gameID.one_of(gameIDs))
    oddsMap = {}
    for odd in odds:
        oddsMap[odd['gameID']] = {
            "spread": odd['spread'],
            "overUnder": odd['overUnder']
        }
    for count,game in enumerate(espnResponse):
        if game['gameId'] in oddsMap:
            espnResponse[count]['odds'] = oddsMap[game['gameId']]
        else:
            espnResponse[count]['odds'] = {
            "spread": None,
            "overUnder": None
        }
    return espnResponse

def calculate_quad_record(data,rank):
    quad_records = {
    "quad1": {'wins': 0, 'losses': 0},
    "quad2": {'wins': 0, 'losses': 0},
    "quad3": {'wins': 0, 'losses': 0},
    "quad4": {'wins': 0, 'losses': 0} 
    }
    for item in data:
        if item['completed'] and 'opponentData' in item and item['opponentData'] is not None:
            quad = item['quad']
            if quad == 0:
                continue
            quad = mapQuad[quad]
            if item['result'] == 'W':
                quad_records[quad]['wins'] += 1
            else:
                quad_records[quad]['losses'] += 1
    return quad_records


def get_random_number():
    return random.random()

def calculate_projected_quad_record(data,rank,quad_records):
    for game in data:
        if not game['completed'] and 'opponentData' in game and game['opponentData'] is not None:
            quad = game['quad']
            if quad == 0:
                continue
            quad = mapQuad[quad]
            quad_records[quad]['wins'] += game['winProbability']
            quad_records[quad]['losses'] +=  1 - game['winProbability']

    #round each quad record
    for quad in quad_records:
        quad_records[quad]['wins'] = round(quad_records[quad]['wins'])
        quad_records[quad]['losses'] = round(quad_records[quad]['losses'])
    return quad_records



def simulate(probs):
    games = len(probs)
    wins = 0
    confGames = len(list(filter(lambda x: x[1] == "CONF", probs)))
    confWin = 0
    for prob in probs:
        if prob[3] != '-1':
            wins = prob[0] + wins
            if prob[1] == "CONF": 
                confWin = prob[0] + confWin
    wins = round(wins)
    loss = games - wins
    confWin = round(confWin)
    confLoss = confGames - confWin
    return wins,loss,confWin,confLoss


def calculateATS(data, teamID):
    spread = data['odds']['spread']
    teamScoreSpread = int(data['score']) - int(data['opponentScore'])
    if data['homeTeamId'] == teamID:
        if teamScoreSpread > spread * -1:
            return "W"
        elif teamScoreSpread < spread * -1:
            return "L"
        else:
            return "P"
    else:
        if teamScoreSpread > spread:
            return "W"
        elif teamScoreSpread < spread:
            return "L"
        else:
            return "P"


def calculate_records(data, teamID):
    records = {
        "win" : 0,
        "loss": 0,
        "projectedWin":0,
        "projectedLoss":0,
        "confWin" : 0,
        "confLoss": 0,
        "confProjectedWin":0,
        "confProjectedLoss":0,
        "atsWin": 0,
        "atsLoss": 0,
        "atsPush": 0
    }
    probs = []
    for game in data:
        if game['completed']:
            if game['odds']['spread']:
                atsResult = calculateATS(game, teamID)
                if atsResult == "W":
                    records['atsWin'] += 1
                elif atsResult == "L":
                    records['atsLoss'] += 1
                else:
                    records['atsPush'] += 1
            if game['gameType'] == 'CONF':
                if game['result'] == 'W':
                    records['win'] += 1
                    records['confWin'] += 1
                if game['result'] == 'L':
                    records['loss'] += 1
                    records['confLoss'] += 1
            else:
                if game['result'] == 'W':
                    records['win'] += 1
                if game['result'] == 'L':
                    records['loss'] += 1
        else:
            probs.append((game['winProbability'], game['gameType'], game['opponentName'], game['opponentId']))
    wins,loss,confWin,confLoss = simulate(probs)
    records['projectedWin'] = wins + records['win']
    records['projectedLoss'] = loss + records['loss']
    records['confProjectedWin'] = confWin + records['confWin']
    records['confProjectedLoss'] = confLoss + records['confLoss']
    records['probs'] = probs
    return records

def get_team_schedule(teamID, year, netRankBool):
    espnResponse = call_espn_schedule_api(teamID, year)
    query, teamsTable = query,teamsTable = get_db_name(constants.TEAMS_DATA_FILE, constants.TEAMS_TABLE_NAME)
    teamsData = teamsTable.all()
    teamsDict = team_data_to_dict(teamsData)
    teamData = teamsDict[teamID]
    for count,game in enumerate(espnResponse):
        opponentData = teamsDict[game['opponentId']] if game['opponentId'] in teamsDict else None
        espnResponse[count]['opponentData'] = opponentData
        gameType = change_game_type(teamData, opponentData, game['gameType'], game['date'], game['notes'])
        espnResponse[count]['gameType'] = gameType
        if opponentData != None:
            if gameType != "REG" and gameType != "CONF":
                espnResponse[count]['quad'] = 0
            elif netRankBool:
                espnResponse[count]['quad'] = quadMap[quad_rank(opponentData['ranks']['net_rank'], game['venue'])]
            else:
                espnResponse[count]['quad'] = quadMap[quad_rank(opponentData['ranks']['rank'], game['venue'])]
        if opponentData and not game['completed']:
            if game['venue'] == "@":
                awayScore,homeScore,prob = make_prediction_api(opponentData['average'],teamData['average'],False) 
                prob = 1-prob
            elif game['venue'] == "H":
                homeScore,awayScore,prob = make_prediction_api(teamData['average'],opponentData['average'],False)
            else:
                homeScore,awayScore,prob = make_prediction_api(teamData['average'],opponentData['average'],True)
        elif opponentData == None:
            homeScore,awayScore,prob = None,None,.99
        else:
            homeScore,awayScore,prob = None,None,None
        espnResponse[count]['scorePrediction'] = homeScore
        espnResponse[count]['opponentScorePrediction'] = awayScore
        espnResponse[count]['winProbability'] = prob
    espnResponse = add_odds(espnResponse)
    records = calculate_records(espnResponse, teamID)
    if netRankBool:
        quad_records = calculate_quad_record(espnResponse,'net_rank')
        # make deep copy of quad_records
        quad_records_copy = copy.deepcopy(quad_records)
        projected_quad_records = calculate_projected_quad_record(espnResponse,'net_rank',copy.deepcopy(quad_records))
    else:
        quad_records = calculate_quad_record(espnResponse,'rank')
        projected_quad_records = calculate_projected_quad_record(espnResponse,'rank',copy.deepcopy(quad_records))
    response = {
            "teamData": teamData,
            "games": espnResponse,
            "teamID": teamID,
            "year": year,
            "records": records,
            "quadRecords": quad_records,
            "projectedQuadRecords": projected_quad_records
        }
    return response
