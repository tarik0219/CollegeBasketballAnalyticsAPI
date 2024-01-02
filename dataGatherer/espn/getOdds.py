import requests




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
    