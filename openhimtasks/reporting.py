# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from openhimtasks import utils
from contextlib import closing
from datetime import date, timedelta
import time

plain_template = "OpenHIM Daily Transaction Report for %s"

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
<h1>OpenHIM Daily Transaction Report</h1>
<h2>Summary of transactions for the OpenHIM instance running on <b>%s</b> for the date %s</h2>
<div>
<table>
<tr><td><b>Transaction</b></td><td><b>Avg Response</b></td><td><b>Max Response</b></td><td><b>Min Response</b></td>
  <td><b>Processing</b></td><td><b>Completed</b></td><td><b>Error'd</b></td></tr>
%s
%s
</table>
<br/><br/>
<p><i>Note that RapidSMS transactions are not included in the summary</i></p>
<br/>
<p><small>Generated on %s</small></p>
</div>
</body>
</html>
"""

# Adapted from https://github.com/jembi/openhim-webui/blob/e4f0a1080364c2fa491e28d3bf25663c85d18c99/openhim-webui/errorui.py#L248
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

stat_fields = ['processing', 'completed', 'error', 'avg', 'max', 'min']
monitoring_num_days = 1

class Monitor(object):
    def calculateStats(self, extraWhereClause=""):
        conn = utils.get_mysql_conn()
        date_from = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d") + " 00:00"
        date_to = date.today().strftime("%Y-%m-%d") + " 00:00"

        with closing(conn.cursor()) as cursor:
            stats = {}
            
            receivedClause = "recieved_timestamp >= '%s' AND recieved_timestamp < '%s'" % (date_from, date_to)
            noRerunClause = "rerun IS NOT true"
            rapidSMSClause = "request_params NOT RLIKE '.*notificationType.*'"
            
            processingSql = "SELECT COUNT(*) FROM `transaction_log` WHERE " + receivedClause + " AND status=1 AND " + noRerunClause + " AND " + rapidSMSClause
            completedSql = "SELECT COUNT(*) FROM `transaction_log` WHERE " + receivedClause + " AND status=2 AND " + noRerunClause + " AND " + rapidSMSClause
            errorSql = "SELECT COUNT(*) FROM `transaction_log` WHERE " + receivedClause + " AND status=3 AND " + noRerunClause + " AND " + rapidSMSClause
            
            avgSql = "SELECT AVG(responded_timestamp - recieved_timestamp) FROM `transaction_log` WHERE " + receivedClause + " AND " + noRerunClause + " AND " + rapidSMSClause
            maxSql = "SELECT MAX(responded_timestamp - recieved_timestamp) FROM `transaction_log` WHERE " + receivedClause + " AND " + noRerunClause + " AND " + rapidSMSClause
            minSql = "SELECT MIN(responded_timestamp - recieved_timestamp) FROM `transaction_log` WHERE " + receivedClause + " AND " + noRerunClause + " AND " + rapidSMSClause
            
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
        totalStats = {};
        for field in stat_fields:
            totalStats[field] = 0
        totalStats['description'] = 'TOTAL'
        stats = []
        for endpoint in endpoints.values():
            stat = self.calculateStats(endpoint[1])
            stat['description'] = endpoint[0]
            stats.append(stat)
            for field in stat_fields:
                if stat[field]: totalStats[field] += stat[field]

        return (totalStats, stats)


def run():
    utils.log("Running reporting task")

    report_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    generated = time.strftime('%Y-%m-%d %H:%M:%S')

    total_stats, stats = Monitor().get_stats()

    check_none = lambda x: x if x is not None else ''
    check_and_format = lambda x: ("%.2fs" % x) if x is not None else ''

    format_stat = lambda stat: "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
        check_none(stat['description']), check_and_format(stat['avg']), check_and_format(stat['max']), check_and_format(stat['min']),
        check_none(stat['processing']), check_none(stat['completed']), check_none(stat['error'])
    )
    stats_html = reduce(lambda a, b: a + b, map(format_stat, stats))

    total_html = "<tr><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td><td><b>%s</b></td></tr>" % (
        total_stats['description'], check_and_format(total_stats['avg']), check_and_format(total_stats['max']), check_and_format(total_stats['min']),
        total_stats['processing'], total_stats['completed'], total_stats['error']
    )

    header = "OpenHIM Daily Transaction Report " + report_date
    plain = plain_template % (report_date)
    html = html_template % (utils.get_him_instance(), report_date, stats_html, total_html, generated)

    utils.send_email(header, plain, html)
    utils.log("Daily transaction report sent")
