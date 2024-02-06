import requests
import json
import pickle
import numpy as np
def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn


def call_bracketology():
    url = "https://koric2.pythonanywhere.com" + "/bracketology"
    response = requests.request("GET", url).json()
    return response

def get_teams_dict():
    url = "https://koric2.pythonanywhere.com" + "/teamData"
    response = requests.request("GET", url).json()
    teamDict = {}
    for team in response:
        teamDict[team["teamName"]] = team
    return teamDict

def get_schedule(teamID,year,netRankBool):
    url = "https://koric2.pythonanywhere.com" + "/teamSchedule"
    payload = json.dumps({"teamID": teamID, "year": year,"netRankBool": netRankBool})
    headers = {'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload).json()
    return response

def get_team_seed_ratings(teams, teamDict, model, champion):
    ratings = []
    for team in teams:
        teamSchedule = get_schedule(teamDict[team]['id'], 2024, True)
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
        probs = model.predict_proba(input)[0]
        rating = 0
        for p,s in zip(probs,model.classes_):
            rating += p*s
        if champion:
            ratings.append((rating, team, 1))
        else:
            ratings.append((rating, team, 0))
    return ratings

def orderTeams(atLargeLock, champions, lowestAtLarge):
    lowerChamps = []
    for team in champions:
        if team[0] < lowestAtLarge[0]:
            atLargeLock.append(team)
        else:
            lowerChamps.append(team)
    return atLargeLock, lowerChamps

def sortLastFourBye(lastFourBye,best,lowChamp):
    lowestFirstFourBye = lastFourBye[-1][0]
    lowerChamp = []
    for team in lowChamp:
        if team[0] < lowestFirstFourBye:
            best.append(team)
        else:
            lowerChamp.append(team)
    for team in lastFourBye:
        best.append(team)
    return best, lowerChamp


def main():
    bracktology = call_bracketology()
    teamDict = get_teams_dict()
    try:
        with open('models/seedModel.pkl', 'rb') as f:
            model = pickle.load(f)
    except: 
        with open('CollegeBasketballAnalyticsAPI/models/seedModel.pkl', 'rb') as f:
            model = pickle.load(f)

    atLargeLock = bracktology['atLargeTeams'][0:28]
    champions = bracktology['champions']
    lastFourBye = bracktology['firstFourBye'] 
    lastFourIn = bracktology['lastFourIn']


    atLargeLockRatings = get_team_seed_ratings(atLargeLock, teamDict, model, False)
    atLargeLockRatings.sort(key=lambda tup: tup[0])
    lastAtLargeLock = atLargeLockRatings[-1]

    championsRatings = get_team_seed_ratings(champions, teamDict, model, True)
    championsRatings.sort(key=lambda tup: tup[0])

    lastFourByeRatings = get_team_seed_ratings(lastFourBye, teamDict, model, False)
    lastFourByeRatings.sort(key=lambda tup: tup[0])

    best, lowChamp = orderTeams(atLargeLockRatings, championsRatings, lastAtLargeLock)
    best.sort(key=lambda tup: tup[0])

    best, lowerChamp = sortLastFourBye(lastFourByeRatings,best,lowChamp)
    lowerChamp.sort(key=lambda tup: tup[0])


    final = []
    seedCount = 1
    counter = 1
    for team in best:
        if team[2] == 1:
            final.append((seedCount, team[1], 1, 0))
        else:
            final.append((seedCount, team[1], 0, 0))
        counter += 1
        if counter > 4:
            seedCount += 1
            counter = 1
        print(team[0], team[1])

    counterLast = 0
    for team in lastFourIn:
        final.append((seedCount, team,0,1))
        counterLast += 1
        if counterLast == 2:
            counter += 1
            counterLast = 0
        if counter > 4:
            seedCount += 1
            counter = 1
        print(team[0], team[1])

    for team in lowerChamp:
        if seedCount == 16 and counter >= 3:
            final.append((seedCount, team[1],1,1))
        else:
            final.append((seedCount, team[1],1,0))
        counter += 1
        if counter > 4:
            seedCount += 1
            counter = 1
        if seedCount == 16 and counter > 3:
            seedCount = 16
            counter = 3
        print(team[0], team[1])
    
    #output final to txt file
    try:
        with open('data/seed.txt', 'w') as f:
            for team in final:
                f.write(str(team[0]) + "," + team[1] + "," + str(team[2]) + "," + str(team[3]) + "\n")
    except:
        with open('CollegeBasketballAnalyticsAPI/data/seed.txt', 'w') as f:
            for team in final:
                f.write(str(team[0]) + "," + team[1] + "," + str(team[2]) + "," + str(team[3]) + "\n")

if __name__ == "__main__":
    main()

