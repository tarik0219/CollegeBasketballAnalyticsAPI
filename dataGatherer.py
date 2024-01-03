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
except:
    query,teamsTable = db.get_db_pa()
    cacheQuery,cacheTable = db.get_cache_pa()

print('Getting Kenpom Data')
kenpomTeams = kenpom.UpdateKenpom()
print('Retrieved Kenpom Data')

print('Getting Barttorvik Data')
barttorvikTeams = barttorvik.UpdateBart()
print('Retrieved Barttorvik Data')



#Update Kenpom Stats
print('Updating Kenpom Data in DB')
for team in kenpomTeams:
    try:
        teamsTable.update(set("kenpom", team), query.id == team['id'])
        teamsTable.update(set("conference", conferenceMap[team['conference']]), query.id == team['id'])
    except:
        if bool(team):
            print(team)
        pass
print('Updated Kenpom Data')

#Update Bart Stats
print('Updating Barttorvik Data in DB')
for team in barttorvikTeams:
    try:
        teamsTable.update(set("barttorvik", team), query.id == team['id'])
    except:
        if bool(team):
            print(team)
        pass
print('Updated Bart Data')

#calculate averages
try:
    calculate.updateStats(query,teamsTable)
except Exception as e:
    print("Unable to calculate Stats Error: ", e)



#calculate records
print("Calculating Records")
try:
    schedule.add_records_teams(constants.year,teamsTable,query)
    print("Calculated Records")
except Exception as e:
    print("Unable to calculate records Error: ", e)

#Add Odds
print("Adding Odds")
try:
    todayDate = datetime.datetime.now().strftime("%Y%m%d")
    oddsResponseMap, oddsResponseList = get_odds_by_date(todayDate)
    cacheTable.insert_multiple(oddsResponseList)
except Exception as e:
    print("Unable to add odds:", e)


    
