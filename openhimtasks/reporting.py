# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from openhimtasks import utils
from contextlib import closing
import time

plain_template = "OpenHIM Transaction Daily Transaction Summary for %s"

html_template = """
<html>
<head>
<style>
table,td
{
    border:1px solid #dddddd;
    border-collapse:collapse;
    border-radius:4px;
}
td
{
    padding:10px;
}
</style>
</head>
<body>
<h1>OpenHIM Transaction Daily Transaction Summary for %s</h1>
<div>
<table>
<tr><td><b>Transaction</b></td><td><b>Avg Response</b></td><td><b>Max Response</b></td><td><b>Min Response</b></td>
  <td><b>Processing</b></td><td><b>Completed</b></td><td><b>Error'd</b></td></tr>
%s
%s
</table>
<p><small>Generated on %s</small></p>
</div>
</body>
</html>
"""

# Copy-paste coding :/
# Adapted straight from https://github.com/jembi/openhim-webui/blob/e4f0a1080364c2fa491e28d3bf25663c85d18c99/openhim-webui/errorui.py#L248
#
# TODO retrieve data from the WebUI using a web service
endpoints = {
    'savePatientEncounter': ('Save Patient Encounter', "path RLIKE 'ws/rest/v1/patient/.*/encounters' AND http_method='POST'"),
    'queryForPreviousPatientEncounters': ('Query for Previous Patient Encounters', "path RLIKE 'ws/rest/v1/patient/.*/encounters' AND http_method='GET'"),
    'getPatientEncounter': ('Get Patient Encounter', "path RLIKE 'ws/rest/v1/patient/.*/encounter/.*' AND http_method='GET'"),
    'registerNewClient': ('Register New Client', "path RLIKE 'ws/rest/v1/patients' AND http_method='POST'"),
    'queryForClient': ('Query for Clients', "path RLIKE 'ws/rest/v1/patients' AND http_method='GET'"),
    'getClient': ('Get Client', "path RLIKE 'ws/rest/v1/patient/.*' AND path NOT RLIKE '.*encounters' AND http_method='GET'"),
    'updateClientRecord': ('Update Client Record', "path RLIKE 'ws/rest/v1/patient/.*' AND http_method='PUT'"),
    'queryForHCFacilities': ('Query for HC Facilities', "path RLIKE 'ws/rest/v1/facilities' AND http_method='GET'"),
    'getHCFacility': ('Get HC Facility', "path RLIKE 'ws/rest/v1/facility/.*' AND http_method='GET'"),
    'postAlert': ('Post Alert', "path RLIKE 'ws/rest/v1/alerts' AND http_method='POST'")
}
monitoring_num_days = 1

class Monitor(object):
    def calculateStats(self, extraWhereClause=""):
        conn = utils.get_mysql_conn()
        with closing(conn.cursor()) as cursor:
            stats = {}
            
            receivedClause = "recieved_timestamp > subdate(curdate(), interval " + str(monitoring_num_days) + " day)"
            noRerunClause = "rerun IS NOT true"
            
            processingSql = "SELECT COUNT(*) FROM `transaction_log` WHERE " + receivedClause + " AND status=1 AND " + noRerunClause
            completedSql = "SELECT COUNT(*) FROM `transaction_log` WHERE " + receivedClause + " AND status=2 AND " + noRerunClause
            errorSql = "SELECT COUNT(*) FROM `transaction_log` WHERE " + receivedClause + " AND status=3 AND " + noRerunClause
            
            avgSql = "SELECT AVG(responded_timestamp - recieved_timestamp) FROM `transaction_log` WHERE " + receivedClause + " AND " + noRerunClause
            maxSql = "SELECT MAX(responded_timestamp - recieved_timestamp) FROM `transaction_log` WHERE " + receivedClause + " AND " + noRerunClause
            minSql = "SELECT MIN(responded_timestamp - recieved_timestamp) FROM `transaction_log` WHERE " + receivedClause + " AND " + noRerunClause
            
            if extraWhereClause != "":
                processingSql += " AND " + extraWhereClause + ";"
                completedSql += " AND " + extraWhereClause + ";"
                errorSql += " AND " + extraWhereClause + ";"
                avgSql += " AND " + extraWhereClause + ";"
                maxSql += " AND " + extraWhereClause + ";"
                minSql += " AND " + extraWhereClause + ";"
            else:
                processingSql += ";"
                completedSql += ";"
                errorSql += ";"
                avgSql += ";"
                maxSql += ";"
                minSql += ";"
                
            cursor.execute(processingSql)
            stats["processing"] = cursor.fetchone()[0]
            cursor.execute(completedSql)
            stats["completed"] = cursor.fetchone()[0]
            cursor.execute(errorSql)
            stats["error"] = cursor.fetchone()[0]
            cursor.execute(avgSql)
            stats["avg"] = cursor.fetchone()[0]
            cursor.execute(maxSql)
            stats["max"] = cursor.fetchone()[0]
            cursor.execute(minSql)
            stats["min"] = cursor.fetchone()[0]
        conn.close()
        return stats
    
    def get_stats(self):
        totalStats = self.calculateStats();
        totalStats['description'] = 'TOTAL'
        stats = []
        for endpoint in endpoints.values():
            stat = self.calculateStats(endpoint[1])
            stat['description'] = endpoint[0]
            stats.append(stat)

        return (totalStats, stats)


def run():
    utils.log("Running reporting task")

    today = time.strftime('%Y-%m-%d')
    generated = time.strftime('%Y-%m-%d %H:%M:%S')

    total_stats, stats = Monitor().get_stats()

    check_none = lambda x: x if x else ''
    format_stat = lambda stat: "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
        check_none(stat['description']), check_none(stat['avg']), check_none(stat['max']), check_none(stat['min']),
        check_none(stat['processing']), check_none(stat['completed']), check_none(stat['error'])
    )
    stats_html = reduce(lambda a, b: a + b, map(format_stat, stats))

    total_html = "<tr><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td></tr>" % (
        total_stats['description'], total_stats['avg'], total_stats['max'], total_stats['min'], total_stats['processing'], total_stats['completed'], total_stats['error']
    )

    header = "Daily Transaction Report"
    plain = plain_template % (today,)
    html = html_template % (today, stats_html, total_html, generated,)

    utils.send_email(header, plain, html)
    utils.log("Daily transaction report sent")
