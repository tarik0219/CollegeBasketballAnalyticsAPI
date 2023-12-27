from flask import Flask, jsonify
from utilscbb.db import get_db

app = Flask(__name__)


@app.route('/', methods=['GET'])
def home():
    return 'College Basketball API'

#Get Team Data by ID
@app.route('/teamData/<teamID>', methods=['GET'])
def get_team_data(teamID):
    query,teamsTable = get_db()
    team = teamsTable.search(query.id == teamID)[0]
    if len(team) > 0:
        return jsonify(team)
    else:
        return jsonify({"error":"Team not found"}), 404

#Get All Team Data
@app.route('/teamData', methods=['GET'])
def get_all_team_data():
    query,teamsTable = get_db()
    teams = teamsTable.all()
    return jsonify(teams)

if __name__ == '__main__':
    app.run() 