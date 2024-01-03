


def get_schedule_query():
    stringQuery = """
        query ($teamID: String!, $year: Int!, $netRank: Boolean!) {
          scheduleData(teamID: $teamID, year: $year, netRank: $netRank) {
            records {
                    projectedWin
                    confLoss
                    confProjectedLoss
                    confProjectedWin
                    confWin
                    loss
                    projectedLoss
                    win
                }
            }
        }
        """
    return stringQuery