from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from utilscbb.config import apiKey
from constants import constants
from utilscbb.query import get_schedule_query


def get_schedule_data(teamID, year, netRank):
    params = {
        "teamID": teamID,
        "year": year,
        "netRank": netRank
    }
    query = gql(get_schedule_query())
    transport = AIOHTTPTransport(url=constants.APP_SYNC_URL, headers={'x-api-key': apiKey})
    client = Client(transport=transport)
    result = client.execute(query, variable_values=params)
    return result