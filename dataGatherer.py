from dataGatherer.kenpom import kenpom
from dataGatherer.barttorvik import barttorvik
from dataGatherer.calculate import calculate
from tinydb.operations import set
from utilscbb import db
from dataGatherer.net import net
import datetime
import warnings
from dataGatherer.record import schedule
from dataGatherer.espn.getOdds import get_odds_by_date
from utilscbb.constants import conferenceMap
from constants import constants
from dataGatherer.conferenceStandings import conferenceStandings


# Ignore all warnings
warnings.filterwarnings("ignore")


#Get Current Date
current_date = datetime.datetime.now()
date_string = current_date.strftime("%Y%m%d")
previous_date = current_date - datetime.timedelta(days=1)
previous_date = previous_date.strftime("%Y%m%d")


try:
    query,teamsTable = db.get_db()
    cacheQuery,cacheTable = db.get_cache()
    standingsQuery,standingsTable = db.get_cs()
except:
    query,teamsTable = db.get_db_pa()
    cacheQuery,cacheTable = db.get_cache_pa()
    standingsQuery,standingsTable = db.get_cs_pa()

print('Getting Kenpom Data')
kenpomTeams = kenpom.UpdateKenpom()
print('Retrieved Kenpom Data')

print('Getting Barttorvik Data')
barttorvikTeams = barttorvik.UpdateBart()
print('Retrieved Barttorvik Data')



#Update Kenpom Stats
print('Updating Kenpom Data in DB')
send = []
for team in kenpomTeams:
    try:
        send.append((set("kenpom", team), query.id == team['id']))
    except:
        if bool(team):
            print(team)
teamsTable.update_multiple(send)
print('Kenpom Data Updated')

#Update Bart Stats
print('Updating Barttorvik Data in DB')
send = []
for team in barttorvikTeams:
    try:
        send.append((set("barttorvik", team), query.id == team['id']))
    except Exception as e:
        print(e)
        if bool(team):
            print(team)
teamsTable.update_multiple(send)
print('Bart Data Updated')


#Update Stats
print('Updating Stats')
#calculate averages
try:
    calculate.updateStats(query,teamsTable)
    print("Stats Calculated")
except Exception as e:
    print("Unable to calculate Stats Error: ", e)



#calculate records
print("Calculating Records")
try:
    schedule.add_records_teams(teamsTable, query)
    print("Records Calculated")
except Exception as e:
    print("Unable to calculate records Error: ", e)


#Add Odds
print("Adding Odds")
try:
    todayDate = datetime.datetime.now().strftime("%Y%m%d")
    oddsResponseMap, oddsResponseList = get_odds_by_date(todayDate)
    cacheTable.insert_multiple(oddsResponseList)
    print("Calculated Odds")
except Exception as e:
    print("Unable to add odds:", e)


    
#Update Conference Standings
print("Updating Conference Standings")
try:
    standings = conferenceStandings.get_conference_standings_odds()
    send = []
    for key,team in standings.items():
        team['conference'] = key
        send.append((team, standingsQuery.conference == key))
    standingsTable.update_multiple(send)
    print("Conference Standings Updated")
except Exception as e:
    print("Unable to update conference standings:", e)