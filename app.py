from flask import Flask, jsonify, request
from utilscbb.db import get_db_name
from utilscbb.predict import make_prediction_api
from requestModel.requestModel import PredictModel,PredictModelList
from utilscbb.scores import get_scores_data
from utilscbb.schedule import get_team_schedule
from constants import constants
from utilscbb.espn import call_espn_team_standings_api, get_all_odds_by_date
from tinydb.operations import set
from utilscbb.oddsAPI import get_odds_predictions
app = Flask(__name__)


@app.route('/', methods=['GET'])
def home():
    return 'College Basketball API'

#Get Team Data by ID
@app.route('/teamData/<teamID>', methods=['GET'])
def get_team_data(teamID):
    query,teamsTable = query,teamsTable = get_db_name(constants.TEAMS_DATA_FILE, constants.TEAMS_TABLE_NAME)
    team = teamsTable.search(query.id == teamID)
    if len(team) > 0:
        return jsonify(team[0])
    else:
        return jsonify({"error":"Team not found"}), 404
    

#Get Team Data by Name
@app.route('/teamData/teamName/<teamName>', methods=['GET'])
def get_team_data_by_name(teamName):
    query,teamsTable = query,teamsTable = get_db_name(constants.TEAMS_DATA_FILE, constants.TEAMS_TABLE_NAME)
    team = teamsTable.search(query.teamName == teamName)
    if len(team) > 0:
        return jsonify(team[0])
    else:
        return jsonify({"error":"Team not found"}), 404

#Get All Team Data
@app.route('/teamData', methods=['GET'])
def get_all_team_data():
    query,teamsTable = query,teamsTable = get_db_name(constants.TEAMS_DATA_FILE, constants.TEAMS_TABLE_NAME)
    teams = teamsTable.all()
    teamRecords = call_espn_team_standings_api(constants.YEAR)
    for count,team in enumerate(teams):
        teamRecord = team['record']
        newTeamRecord = teamRecords[team['id']]
        if teamRecord['win'] + teamRecord['loss'] != newTeamRecord['win'] + newTeamRecord['loss']:
            scheduleRecordData = get_team_schedule(team['id'],constants.YEAR, constants.NET_RANK_BOOL)['records']
            del scheduleRecordData["probs"]
            teamsTable.update(set("record", scheduleRecordData),query.id == team['id'])
            scheduleRecordData.update(newTeamRecord)
            teams[count]['record'] = scheduleRecordData
        else:
            team['record'].update(newTeamRecord)
            teams[count]['record'] = team['record']
    return jsonify(teams)

#Predict Game
@app.route('/predict', methods=['POST'])
def predict_game():
    try:
        PredictModel(**request.get_json())
        data = request.get_json()
        homeScore,awayScore,prob = make_prediction_api(data['homeData'],data['awayData'],data['neutralSite'])
        return jsonify({'homeScore':homeScore,'awayScore':awayScore,'prob':prob})
    except:
        return jsonify({"error":"Invalid JSON"}), 400

#Predict Games
@app.route('/predictList', methods=['POST'])
def predict_games():
    try:
        PredictModelList(**request.get_json())
        data = request.get_json()
        response = []
        for game in data['games']:
            homeScore,awayScore,prob = make_prediction_api(game['homeData'],game['awayData'],game['neutralSite'])
            response.append({'homeScore':homeScore,'awayScore':awayScore,'prob':prob})
        return jsonify(response)
    except Exception as e:
        return jsonify({"error":"Invalid JSON"}), 400
    
@app.route('/getOdds/<gameID>', methods=['GET'])
def get_odds(gameID):
    query,teamsTable = get_db_name(constants.ODDS_CACHE_FILE, constants.ODDS_TABLE_NAME)
    game = teamsTable.search(query.gameID == gameID)
    if len(game) > 0:
        return jsonify(game[0])
    else:
        return jsonify({"error":"Game not found"}), 404


@app.route('/getOddsList', methods=['POST'])
def get_odds_list():
    data = request.get_json()
    gameIDs = data['gameIDs']
    query,cacheTable = get_db_name(constants.ODDS_CACHE_FILE, constants.ODDS_TABLE_NAME)
    response = cacheTable.search(query.gameID.one_of(gameIDs))
    return jsonify({"games":response})

@app.route('/getConferenceStandings/<conference>', methods=['GET'])
def get_conference_standings(conference):
    query,teamsTable = get_db_name(constants.CONFERENCE_STANDINGS_FILE, constants.CS_TABLE_NAME)
    standings = teamsTable.search(query.conference == conference)
    if len(standings) > 0:
        return jsonify(standings)
    else:
        return jsonify({"error":"Conference not found"}), 404

@app.route('/scores/<date>', methods=['GET'])
def get_scores(date):
    return jsonify({"scores": get_scores_data(date)})


@app.route('/teamSchedule', methods=['POST'])
def get_schedule():
    requestData = request.get_json()
    data = get_team_schedule(requestData['teamID'],requestData['year'],requestData['netRankBool'])
    return jsonify(data)

@app.route('/odds/date/<date>', methods=['GET'])
def get_odds_by_date(date):
    return jsonify({"allOdds": get_all_odds_by_date(date)})

@app.route('/odds/oddsAPI', methods=['GET'])
def get_odds_oddsAPI():
    return jsonify(get_odds_predictions())


@app.route('/bracketology', methods=['GET'])
def get_bracketology():
    with open('data/atLarge.txt', 'r') as file:
        lines = file.readlines()
        atLarge = [line.strip() for line in lines]
    with open('data/champions.txt', 'r') as file:
        lines = file.readlines()
        champions = [line.strip() for line in lines]
    
    firstFourBye = atLarge[28:32]
    lastFourIn = atLarge[32:36]
    firstFourOut = atLarge[36:40]
    nextFourOut = atLarge[40:44]
    atLargeTeams = atLarge[:36]
    bubble = atLarge[44:54]

    data = {
        "firstFourBye": firstFourBye,
        "lastFourIn": lastFourIn,
        "firstFourOut": firstFourOut,
        "nextFourOut": nextFourOut,
        "atLargeTeams": atLargeTeams,
        "bubble": bubble,
        "champions": champions
    }
    return data

@app.route('/seed', methods=['GET'])
def get_seed():
    with open('data/seed.txt', 'r') as file:
        lines = file.readlines()
        seed_data = [line.strip().split(',') for line in lines]
    return jsonify(seed_data)

if __name__ == '__main__':
    app.run()