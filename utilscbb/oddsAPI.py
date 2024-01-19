import requests
import random
from config.config import oddsApiKeys
from constants import constants
from utilscbb.db import get_db_name
from utilscbb.scores import get_scores_data
from thefuzz import process
import datetime
import pytz

#randomly choose an api key from the list
def get_api_key(apiKeys):
    randomApiKey = random.choice(apiKeys)
    return randomApiKey
    
def call_odds_api(apiKey):
    url = f"https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds/?apiKey={apiKey}&regions=us,us2&oddsFormat=decimal"
    response = requests.request("GET", url).json()
    return response

def get_team_names():
    query,teamsTable = get_db_name(constants.TEAMS_DATA_FILE, constants.TEAMS_TABLE_NAME)
    teams = teamsTable.all()
    teamNames = []
    for team in teams:
        teamNames.append(team['teamName'])
    return teamNames

def get_odds_team_names():
    response = call_odds_api(get_api_key(oddsApiKeys))
    teamNames = get_team_names()
    odds = []
    for game in response:
        newHomeTeam = process.extractOne(game['home_team'], teamNames)
        newAwayTeam = process.extractOne(game['away_team'], teamNames)
        if newHomeTeam[1] > 80 and newAwayTeam[1] > 80:
            homeTeamName = newHomeTeam[0]
            awayTeamName = newAwayTeam[0]
        else:
            continue
        # Remove home_team and away_team keys
        game.pop('home_team')
        game.pop('away_team')
        
        game['homeTeamName'] = homeTeamName
        game['awayTeamName'] = awayTeamName
        odds.append(game)
    return odds

def get_odds_predictions():
    # Get the current time in Pacific Timezone
    pacific_tz = pytz.timezone('US/Pacific')
    current_time = datetime.datetime.now(pacific_tz)

    todayDate = current_time.date()
    today = todayDate.strftime("%Y%m%d")
    tmrw = todayDate + datetime.timedelta(days=1)
    tmrw = tmrw.strftime("%Y%m%d")
    
    games = []
    todayGames = get_scores_data(today)
    tmrwGames = get_scores_data(tmrw)
    games.extend(todayGames)
    games.extend(tmrwGames)

    gamesDict = {}
    for game in games:
        gamesDict[game['homeTeam'] + game['awayTeam']] = game

    odds = get_odds_team_names()
    finalOdds = []

    for game in odds:
        if game['homeTeamName'] + game['awayTeamName'] in gamesDict:
            game['siteType'] = gamesDict[game['homeTeamName'] + game['awayTeamName']]['siteType']
            game["prob"] = gamesDict[game['homeTeamName'] + game['awayTeamName']]['prob']
            game['homeScorePredict'] = gamesDict[game['homeTeamName'] + game['awayTeamName']]['homeScorePredict'] 
            game['awayScorePredict'] = gamesDict[game['homeTeamName'] + game['awayTeamName']]['awayScorePredict']
            game['status'] = gamesDict[game['homeTeamName'] + game['awayTeamName']]['status']
            game['gameId'] = gamesDict[game['homeTeamName'] + game['awayTeamName']]['gameId']
            game['date'] = gamesDict[game['homeTeamName'] + game['awayTeamName']]['date']
            game['homeTeamId'] = gamesDict[game['homeTeamName'] + game['awayTeamName']]['homeTeamId']
            game['awayTeamId'] = gamesDict[game['homeTeamName'] + game['awayTeamName']]['awayTeamId']
            finalOdds.append(game)
        if game['awayTeamName'] + game['homeTeamName'] in gamesDict:
            game['siteType'] = gamesDict[game['awayTeamName'] + game['homeTeamName']]['siteType']
            game['homeTeamName'], game['awayTeamName'] = game['awayTeamName'], game['homeTeamName']
            game["prob"] = gamesDict[game['awayTeamName'] + game['homeTeamName']]['prob']
            game['homeScorePredict'] = gamesDict[game['awayTeamName'] + game['homeTeamName']]['homeScorePredict']
            game['awayScorePredict'] = gamesDict[game['awayTeamName'] + game['homeTeamName']]['awayScorePredict']
            game['status'] = gamesDict[game['awayTeamName'] + game['homeTeamName']]['status']
            game['gameId'] = gamesDict[game['awayTeamName'] + game['homeTeamName']]['gameId']
            game['date'] = gamesDict[game['awayTeamName'] + game['homeTeamName']]['date']
            game['homeTeamId'] = gamesDict[game['awayTeamName'] + game['homeTeamName']]['homeTeamId']
            game['awayTeamId'] = gamesDict[game['awayTeamName'] + game['homeTeamName']]['awayTeamId']
            finalOdds.append(game)
    return finalOdds
