import requests
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from net import net


def calc_average(stat, statNames, data):
    sum = 0
    count = 0
    for name in statNames:
        sum += data[name][stat]
        count += 1
    return sum/count

def addAverage(data):
    for count,team in enumerate(data):
        team['average'] = {
            "offRating":calc_average('offRating', ["barttorvik","kenpom"], team),
            "defRating":calc_average('defRating', ["barttorvik","kenpom"], team),
            "TempoRating":calc_average('TempoRating', ["barttorvik","kenpom"], team),
        }
        netRanking = team['ranks']['net_rank']
        apRank = team['ranks']['ap_rank']
        team['ranks'] = {
            'stat_rank': None,
            "rank": None,
            "rankOff": None,
            "rankDef": None,
            "rankTempo": None,
            "net_rank": netRanking,
            "ap_rank": apRank,
        }
        data[count] = team
    return data

def addStatRank(data):
    data.sort(key=lambda x: x["barttorvik"]["offRating"] - x["barttorvik"]["defRating"] + x["kenpom"]["offRating"] - x["barttorvik"]["defRating"], reverse=True)
    for count,team in enumerate(data):
        team['ranks']['stat_rank'] = count + 1
        data[count] = team
    return data

def addApRank(data):
    url = "https://site.web.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/rankings"
    payload={}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)

    ranks = response.json()['rankings'][0]['ranks']
    others = response.json()['rankings'][0]['others']

    ap_ranks = {}
    for count,team in enumerate(ranks):
        ap_ranks[team['team']['id']] = count + 1
        
    for count,team in enumerate(others):
        ap_ranks[team['team']['id']] = count + 26

    length_rank = len(ap_ranks)
    for count,team in enumerate(data):
        if team['id'] in ap_ranks:
            team['ranks']['ap_rank'] = ap_ranks[team['id']]
        else:
            if team['ranks']['stat_rank'] < length_rank:
                team['ranks']['ap_rank'] = length_rank + 1
            else:
                team['ranks']['ap_rank'] = team['ranks']['stat_rank']
        data[count] = team
    return data

def addNetRank(data):
    try:
        netRanks = net.net_rankings_to_dict()
        dataMap = {}
        for team in data:
            dataMap[team['id']] = team

        for teamId,rank in netRanks.items():
            try:
                teamData = dataMap[teamId]
                teamData['ranks']["net_rank"] = rank
                dataMap[teamId] = teamData
            except Exception as e:
                print("Unable to calculate Net Rankings for team: ", e, "TeamId: ", teamId)
                pass
        data = list(dataMap.values())
        return data
    except Exception as e:
        print("Unable to calculate Net Rankings Error: ", e)
        return data

def addRank(data):
    data.sort(key=lambda x: x['ranks']["stat_rank"] * .25  + x['ranks']["ap_rank"] * .50 +x['ranks']["net_rank"] * .25, reverse=False)
    for count,team in enumerate(data):
        team['ranks']['rank'] = count + 1
        data[count] = team
    return data

def addOff(data):
    data.sort(key=lambda x: x["barttorvik"]["offRating"]  + x["kenpom"]["offRating"] , reverse=True)
    for count,team in enumerate(data):
        team['ranks']['rankOff'] = count + 1
        data[count] = team
    return data

def addDef(data):
    data.sort(key=lambda x: x["barttorvik"]["defRating"]  + x["kenpom"]["defRating"] , reverse=False)
    for count,team in enumerate(data):
        team['ranks']['rankDef'] = count + 1
        data[count] = team
    return data

def addTempo(data):
    data.sort(key=lambda x: x["barttorvik"]["TempoRating"]  + x["kenpom"]["TempoRating"] , reverse=True)
    for count,team in enumerate(data):
        team['ranks']['rankTempo'] = count + 1
        data[count] = team
    return data

def updateStats(query,teamsTable):
    data = teamsTable.all()
    print('Calculating Average')
    data = addAverage(data)
    print('Calculating Stats Rank')
    data = addStatRank(data)
    print('Calculating Net Rank')
    data = addNetRank(data)
    print('Calculating AP Rank')
    data = addApRank(data)
    print('Calculating Average Rank')
    data = addRank(data)
    print('Calculating OFF Rank')
    data = addOff(data)
    print('Calculating DEF Rank')
    data = addDef(data)
    print('Calculating TEMPO Rank')
    data = addTempo(data)
    print('Done Caclculating')
    send = []
    for team in data:
        send.append((team, query.id == team['id']))
    teamsTable.update_multiple(send)