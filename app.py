from flask import Flask, jsonify, request
from utilscbb.db import get_db
from utilscbb.predict import make_prediction_api
from requestModel.requestModel import PredictModel,PredictModelList
app = Flask(__name__)


@app.route('/', methods=['GET'])
def home():
    return 'College Basketball API'

#Get Team Data by ID
@app.route('/teamData/<teamID>', methods=['GET'])
def get_team_data(teamID):
    query,teamsTable = get_db()
    team = teamsTable.search(query.id == teamID)
    if len(team) > 0:
        return jsonify(team[0])
    else:
        return jsonify({"error":"Team not found"}), 404
    

#Get Team Data by Name
@app.route('/teamData/teamName/<teamName>', methods=['GET'])
def get_team_data_by_name(teamName):
    query,teamsTable = get_db()
    team = teamsTable.search(query.teamName == teamName)
    if len(team) > 0:
        return jsonify(team[0])
    else:
        return jsonify({"error":"Team not found"}), 404

#Get All Team Data
@app.route('/teamData', methods=['GET'])
def get_all_team_data():
    query,teamsTable = get_db()
    teams = teamsTable.all()
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

if __name__ == '__main__':
    app.run() 