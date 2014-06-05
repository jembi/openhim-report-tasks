# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from openhimtasks import utils
from contextlib import closing

plain_template = """
ERROR Alert - Transaction Failures

The following transaction(s) have failed on the OpenHIM instance running on %s:
%s
"""
html_template = """
<html>
<head></head>
<body>
<h1>ERROR Alert - Transaction Failures</h1>
<div>
<p>The following transaction(s) have failed on the OpenHIM instance running on <b>%s</b>:</p>
%s
</div>
</body>
</html>
"""

def send_alert(transactions, cursor, conn):
    subject = "ERROR - Transaction Failure"
    transactions_plain = ""
    transactions_html = "<table>"
    webui_url = utils.get_webui_url()
    for transaction in transactions:
        url = webui_url + "/transview/?id=" + str(transaction[0])
        transactions_plain += "%s\n" % (url,)
        transactions_html += "<tr><td><a href='%s'>%s</a></td></tr>\n" % (url, url,)
    plain = plain_template % (utils.get_him_instance(), transactions_plain,)
    html = html_template % (utils.get_him_instance(), transactions_html,)
    utils.send_email(subject, plain, html)
    cursor.execute("insert into alerts(message) values ('" + plain + "')")
    conn.commit()
    utils.log("Updated database")

def run():
    utils.log("Running alerting task")
    conn = utils.get_mysql_conn()
    with closing(conn.cursor()) as cursor:
        cursor.execute("select count(*) as count from alerts where date(sent_date) = curdate()")
        count = cursor.fetchone()
        if count[0] == 0:
            cursor.execute(("select id from transaction_log where date(recieved_timestamp) = curdate() and "
                "status = 3 and request_params not rlike '.*notificationType.*'"))
            transactions = cursor.fetchall()
            if not transactions or len(transactions) == 0:
                utils.log("No errors found for today")
            else:
                utils.log("%s errors found - sending alert" % (len(transactions),))
                send_alert(transactions, cursor, conn)
        else:
            utils.log("Error alerts have already been sent today. Skipping.")
    conn.close()
