import requests
from datetime import datetime
from dateutil import tz
import pytz
import json
import sys, os
from utilscbb.espn import call_espn_schedule_api
from utilscbb.db import get_db, get_cache  
from utilscbb.predict import make_prediction, make_prediction_api
import time


quadMap = {
    "quad1": 1,
    "quad2": 2,
    "quad3": 3,
    "quad4": 4
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

def change_game_type(teamData, opponentData, gameType):
    if gameType == "POST":
        return "POST"
    if opponentData:
        if teamData['conference'] == opponentData['conference']:
            return "CONF"
    return "REG"

def add_odds(espnResponse):
    gameIDs = []
    for game in espnResponse:
        gameIDs.append(game['gameId'])
    
    query, oddsTable = get_cache()
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
        if item['completed']:
            #check if item has opponent data and ranks and rank
            if 'opponentData' in item and item['opponentData'] is not None:
                if 'ranks' in item['opponentData'] and item['opponentData']['ranks'] is not None:
                    if rank in item['opponentData']['ranks']:
                        opponent_rank = item['opponentData']["ranks"][rank]
                        venue = item["venue"]
                        quad = quad_rank(opponent_rank,venue)
                        if item['result'] == 'W':
                            quad_records[quad]['wins'] += 1
                        else:
                            quad_records[quad]['losses'] += 1
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

def calculate_records(data):
    records = {
        "win" : 0,
        "loss": 0,
        "projectedWin":0,
        "projectedLoss":0,
        "confWin" : 0,
        "confLoss": 0,
        "confProjectedWin":0,
        "confProjectedLoss":0
    }
    probs = []
    for game in data:
        if game['completed']:
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
    query, teamsTable = get_db()
    teamsData = teamsTable.all()
    teamsDict = team_data_to_dict(teamsData)
    teamData = teamsDict[teamID]
    for count,game in enumerate(espnResponse):
        opponentData = teamsDict[game['opponentId']] if game['opponentId'] in teamsDict else None
        espnResponse[count]['opponentData'] = opponentData
        if opponentData != None:
            if netRankBool:
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
        espnResponse[count]['gameType'] = change_game_type(teamData, opponentData, game['gameType'])
    espnResponse = add_odds(espnResponse)
    records = calculate_records(espnResponse)
    if netRankBool:
        quad_records = calculate_quad_record(espnResponse,'net_rank')
    else:
        quad_records = calculate_quad_record(espnResponse,'rank')
    response = {
            "teamData": teamData,
            "games": espnResponse,
            "teamID": teamID,
            "year": year,
            "records": records,
            "quadRecords": quad_records,
        }
    return response
