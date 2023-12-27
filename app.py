from flask import Flask, jsonify, request
from utilscbb.db import get_db
from utilscbb.predict import make_prediction_api
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
    data = request.get_json()
    homeScore,awayScore,prob = make_prediction_api(data['homeData'],data['awayData'],data['neutralSite'])
    return jsonify({'homeScore':homeScore,'awayScore':awayScore,'prob':prob})


if __name__ == '__main__':
    app.run() 