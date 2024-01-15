import requests
from datetime import datetime
from dateutil import tz
import json



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

def get_venue(homeAway, neutralSite):
    if neutralSite:
        return "N"
    elif homeAway == "home":
        return "H"
    else:
        return "Away"


def call_espn_team_standings_api(year):
    url = f"http://site.api.espn.com/apis/v2/sports/basketball/mens-college-basketball/standings?season={year}"
    response = requests.request("GET", url).json()
    teams = {}
    for conference in response['children']:
        teamsData = conference['standings']['entries']
        for team in teamsData:
            teams[team['team']['id']] ={
                "gamesBehind": team['stats'][67]['value'],
                "conferenceStanding": int(team['stats'][5]['value']),
                "win": int(team['stats'][12]['displayValue'].split("-")[0]),
                "loss": int(team['stats'][12]['displayValue'].split("-")[1]),
                "confWin": int(team['stats'][77]['displayValue'].split("-")[0]),
                "confLoss": int(team['stats'][77]['displayValue'].split("-")[1])
            }
    return teams

def call_espn_schedule_api(teamID, year):
    url = f'https://site.web.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams/{teamID}/schedule'
    season_count = 2
    data = []
    while season_count < 4:
        response = requests.get(url,params={'season':year,'seasontype':str(season_count)}).json()
        games = response['events']
        for game in games:
            gameData = {}
            competitionData = game['competitions'][0]
            gameData['date'], gameData['time'] = convertDateTime(game["date"])
            gameData['dateString'] = gameData['date'].replace('-', '')
            gameData['gameId'] = game["id"]
            gameData['neutralSite'] = competitionData.get('neutralSite', False)
            gameData['gameType'] = "REG" if season_count == 2 else "POST"
            gameData['completed'] = competitionData['status']['type']['completed']
            if competitionData['competitors'][0]["id"] == teamID:
                if gameData['neutralSite']:
                    gameData['venue'] = "N"
                elif competitionData['competitors'][0]["homeAway"] == "home":
                    gameData['venue'] = "H"
                else:
                    gameData['venue'] = "@"
                gameData['score'] = competitionData['competitors'][0].get("score",{}).get("displayValue")
                gameData['opponentScore'] = competitionData['competitors'][1].get("score",{}).get("displayValue")
                gameData['opponentId'] = competitionData['competitors'][1]["id"]
                gameData['opponentName'] = competitionData['competitors'][1]['team']["displayName"]
                if competitionData['competitors'][0]['homeAway'] == "home":
                    gameData['homeTeamId'] = teamID
                else:
                    gameData['homeTeamId'] = competitionData['competitors'][1]["id"]
            else:
                if gameData['neutralSite']:
                    gameData['venue'] = "N"
                elif competitionData['competitors'][0]["homeAway"] == "home":
                    gameData['venue'] = "@"
                else:
                    gameData['venue'] = "H"
                gameData['score'] = competitionData['competitors'][1].get("score",{}).get("displayValue")
                gameData['opponentScore'] = competitionData['competitors'][0].get("score",{}).get("displayValue")
                gameData['opponentId'] = competitionData['competitors'][0]["id"]
                gameData['opponentName'] = competitionData['competitors'][0]["team"]["displayName"]
                if competitionData['competitors'][0]['homeAway'] == "home":
                    gameData['homeTeamId'] = competitionData['competitors'][0]["id"]
                else:
                    gameData['homeTeamId'] = teamID
            if gameData['completed']:
                if int(gameData['opponentScore']) > int(gameData['score']):
                    gameData['result'] = "L"
                elif int(gameData['opponentScore']) < int(gameData['score']):
                    gameData['result'] = "W"
                else:
                    gameData['result'] = None
            else:
                gameData['result'] = None
            data.append(gameData)
        season_count += 1
    return data
    
def get_odds_by_game_id(gameID):
    url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/events/{gameID}/competitions/{gameID}/odds?="
    response = requests.request("GET", url).json()
    return response


def get_odds_by_date(date):
    url = 'http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard'
    response = requests.get(url,params={'limit':'500','groups':'50','dates': str(date)}).json()
    oddsResponseMap = {}
    oddsResponseList = []
    for game in response['events']:
        oddsResponse = get_odds_by_game_id(game['id'])
        if len(oddsResponse['items']) > 0:
            try:
                oddsResponseMap[game['id']] = {
                    "spread":oddsResponse['items'][0]['spread'],
                    "overUnder":oddsResponse['items'][0]['overUnder']
                }
                oddsResponseList.append({
                    "gameID":game['id'],
                    "spread":oddsResponse['items'][0]['spread'],
                    "overUnder":oddsResponse['items'][0]['overUnder']
                })
            except:
                print("Error getting odds for game: ", game['id'])
    return oddsResponseMap, oddsResponseList

def get_half(period):
    if period == 1:
        return "1st"
    elif period == 2:
        return "2nd"
    elif period >= 3:
        return f"{period}OT"

def call_espn_scores_api(date):
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
    