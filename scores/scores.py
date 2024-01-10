import requests
import requests
import json
from datetime import datetime
from dateutil import tz
from utilscbb.db import get_db, get_cache
from utilscbb.predict import make_prediction_api


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

def get_half(period):
    if period == 1:
        return "1st"
    elif period == 2:
        return "2nd"
    elif period >= 3:
        return f"{period}OT"
    
def get_scores(date):
    # Get ESPN LIVE SCORE DATA
    url = 'http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard'
    response = requests.get(url, params={'limit': '500', 'groups': '50', 'dates': str(date)})
    responseJson = response.json()
    espnScores = {}
    games = responseJson.get('events', {})
    
    if len(games) == 0:
        return espnScores
    
    for game in games:
        competition = game['competitions'][0]
        date = competition['date']
        date, time = convertDateTime(date)

        siteType = competition.get('neutralSite')
        gameId = game['id']
        broadcast = None if len(competition.get('broadcasts',[{}])) == 0 else competition.get('broadcasts',[{}])[0].get('names', [None])[0]

        # Team 1
        team1 = competition['competitors'][0]
        homeTeam = team1['team']['displayName']
        homeTeamId = team1['team']['id']
        homeScore = team1['score']

        # Team 2
        team2 = competition['competitors'][1]
        awayTeam = team2['team']['displayName']
        awayTeamId = team2['team']['id']
        awayScore = team2['score']

        # Game details
        clock = game['status'].get('displayClock')
        period = game['status'].get('period')
        status = game['status']['type'].get('state')

        espnGame = {
            "date": date,
            "time": time,
            "broadcast": broadcast,
            "siteType": siteType,
            "clock": clock,
            "period": period,
            "status": status,
            "homeTeam": homeTeam,
            "homeTeamId": homeTeamId,
            "homeScore": homeScore,
            "awayTeam": awayTeam,
            "awayTeamId": awayTeamId,
            "awayScore": awayScore,
            "half": get_half(period),
            "gameId": gameId
        }
        espnScores[gameId] = espnGame

    return espnScores


def get_team_data(teamID, query, teamsTable):
    query,teamsTable = get_db()
    team = teamsTable.search(query.id == teamID)
    if len(team) > 0:
        return team[0]
    else:
        return {}

def get_prediction(homeData, awayData, neutralSite):
    if (len(homeData) == 0) or (len(awayData) == 0):
        return None, None, None
    homeScore,awayScore,prob = make_prediction_api(homeData['average'], awayData['average'], neutralSite)
    return homeScore,awayScore,prob

def add_line_data(query, oddsTable, gameID):
    odds = oddsTable.search(query.gameID == gameID)
    if len(odds) > 0:
        return odds[0]
    else:
        return {"spread": None, "overUnder": None}


def get_scores_data(date):
    espnScores = get_scores(date)
    query,teamsTable = get_db()
    oddsQuery,oddsTable = get_cache()
    espnScoresList = []
    for gameId,game in espnScores.items():
        homeData = get_team_data(game['homeTeamId'], query, teamsTable)
        awayData = get_team_data(game['awayTeamId'], query, teamsTable)
        if game['status'] == 'post':
            homeScore, awayScore, prob = None, None, None
        else:
            homeScore,awayScore,prob = get_prediction(homeData, awayData, game['siteType'])
        odds = add_line_data(oddsQuery, oddsTable, gameId)
        game.update({
            "homeData": get_team_data(game['homeTeamId'], query, teamsTable),
            "awayData": get_team_data(game['awayTeamId'], query, teamsTable),
            "homeScorePredict": homeScore,
            "awayScorePredict": awayScore,
            "prob": prob,
            "spread": odds['spread'],
            "overUnder": odds['overUnder']
        })
        espnScoresList.append(game)
    return  espnScoresList



