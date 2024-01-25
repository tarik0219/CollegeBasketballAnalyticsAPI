from utilscbb.oddsAPI import get_odds_predictions
import csv
import csv
import pandas as pd

def get_best_odds(finalOdds, selectedSportsBooks):
    bestOdds = []
    for game in finalOdds:
        if game['status'] != 'pre':
            continue
        odds = {}
        odds['homeTeamName'] = game['homeTeamName']
        odds['awayTeamName'] = game['awayTeamName']
        odds['prob'] = game['prob']
        odds['gameId'] = game['gameId']
        odds['date'] = game['date']
        homeTeamOdds = 1
        awayTeamOdds = 1
        homeTeamOddsSite = ''
        awayTeamOddsSite = ''
        for sportsBook in game['bookmakers']:
            if sportsBook['key'] not in selectedSportsBooks:
                continue
            if sportsBook['markets'][0]['outcomes'][1]['name'] == game['homeTeamName']:
                if sportsBook['markets'][0]['outcomes'][1]['price'] > homeTeamOdds:
                    homeTeamOdds = sportsBook['markets'][0]['outcomes'][1]['price']
                    homeTeamOddsSite = sportsBook['title']
                if sportsBook['markets'][0]['outcomes'][0]['price'] > awayTeamOdds:
                    awayTeamOdds = sportsBook['markets'][0]['outcomes'][0]['price']
                    awayTeamOddsSite = sportsBook['title']
            else:
                if sportsBook['markets'][0]['outcomes'][0]['price'] > homeTeamOdds:
                    homeTeamOdds = sportsBook['markets'][0]['outcomes'][0]['price']
                    homeTeamOddsSite = sportsBook['title']
                if sportsBook['markets'][0]['outcomes'][1]['price'] > awayTeamOdds:
                    awayTeamOdds = sportsBook['markets'][0]['outcomes'][1]['price']
                    awayTeamOddsSite = sportsBook['title']
        odds['homeTeamOdds'] = homeTeamOdds
        odds['awayTeamOdds'] = awayTeamOdds
        odds['homeTeamOddsSite'] = homeTeamOddsSite
        odds['awayTeamOddsSite'] = awayTeamOddsSite
        odds['homeTeamBet'] = False
        odds['awayTeamBet'] = False
        odds['homeTeamId'] = game['homeTeamId']
        odds['awayTeamId'] = game['awayTeamId']
        homeOdds = 1/homeTeamOdds
        myOdds = game['prob']
        if myOdds + .2 < homeOdds  or myOdds  - .2 > homeOdds:
            continue
        if game['prob'] > 1/homeTeamOdds:
            odds['homeTeamBet'] = True
        if 1 - game['prob'] > 1/awayTeamOdds:
            odds['awayTeamBet'] = True
        if homeTeamOdds != 1 and awayTeamOdds != 1:
            bestOdds.append(odds)
    return bestOdds

def main():
    response = get_odds_predictions()
    bestOdds = get_best_odds(response, ['draftkings', 'fanduel', 'pointsbetus', 'espnbet', 'betmgm', 'betrivers'])
    
    # Read existing data from the CSV file
    try:
        existing_data = pd.read_csv('data/oddsTracker.csv')
        existing_game_ids = set(existing_data['GameID'].tolist())  # Convert to set
    except:
        existing_game_ids = set()
    
    
    # Append bestOdds to csv file in data/oddsTracker.csv
    try:
        with open('data/oddsTracker.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            
            # Write headers if the file is empty
            if f.tell() == 0:
                writer.writerow(['HomeTeamName', 'AwayTeamName', 'Probability', 'HomeTeamOdds', 'AwayTeamOdds', 'HomeTeamOddsSite', 'AwayTeamOddsSite', 'HomeTeamBet', 'AwayTeamBet', 'GameID', 'Date', 'HomeTeamID', 'AwayTeamID'])
            
            for game in bestOdds:
                
                if int(game['gameId']) not in existing_game_ids:
                    writer.writerow([game['homeTeamName'], game['awayTeamName'], game['prob'], game['homeTeamOdds'], game['awayTeamOdds'], game['homeTeamOddsSite'], game['awayTeamOddsSite'], game['homeTeamBet'], game['awayTeamBet'], game['gameId'], game['date'], game['homeTeamId'], game['awayTeamId']])
                else:
                    pass
    except:
        with open('CollegeBasketballAnalyticsAPI/data/oddsTracker.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            
            # Write headers if the file is empty
            if f.tell() == 0:
                writer.writerow(['HomeTeamName', 'AwayTeamName', 'Probability', 'HomeTeamOdds', 'AwayTeamOdds', 'HomeTeamOddsSite', 'AwayTeamOddsSite', 'HomeTeamBet', 'AwayTeamBet', 'GameID', 'Date', 'HomeTeamID', 'AwayTeamID'])
            
            for game in bestOdds:
                
                if int(game['gameId']) not in existing_game_ids:
                    writer.writerow([game['homeTeamName'], game['awayTeamName'], game['prob'], game['homeTeamOdds'], game['awayTeamOdds'], game['homeTeamOddsSite'], game['awayTeamOddsSite'], game['homeTeamBet'], game['awayTeamBet'], game['gameId'], game['date'], game['homeTeamId'], game['awayTeamId']])
                else:
                    pass

if __name__ == "__main__":
    main()