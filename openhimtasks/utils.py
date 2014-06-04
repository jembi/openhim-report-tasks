# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import smtplib
import ConfigParser
import MySQLdb
from datetime import datetime

def log(message):
    print "[" + datetime.now().__str__() + "] " + message

def send_email(subject, message):
    config = ConfigParser.RawConfigParser();
    config.read('/etc/openhim-report-tasks.conf')

    to = config.get('Email Targets', 'target_address')
    host =  config.get('SMTP','smtp_host')
    port = int(config.get('SMTP','smtp_port'))
    user = config.get('SMTP','smtp_user')
    pwd = config.get('SMTP','smtp_passwd')

    header = "From: %s\nTo: %s\nSubject: %s\n\n" % (user, to, subject,)

    smtpserver = smtplib.SMTP(host, port)
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo
    smtpserver.login(user, pwd)
    smtpserver.sendmail(user, to, header + message)
    smtpserver.close()
    log("Sent email to '%s' using '%s' on port %s" % (to, host, port,))

def get_mysql_conn():
    config = ConfigParser.RawConfigParser();
    config.read('/etc/openhim-report-tasks.conf')

    dbhost = config.get('Database', 'db_host')
    dbport = int(config.get('Database', 'db_port'))
    dbuser =  config.get('Database', 'db_user')
    dbpasswd = config.get('Database', 'db_passwd')
    dbname = config.get('Database', 'db_name')

    return MySQLdb.connect(host=dbhost, port=dbport, user=dbuser, passwd=dbpasswd, db=dbname, use_unicode=True)

def get_him_instance():
    config = ConfigParser.RawConfigParser();
    config.read('/etc/openhim-report-tasks.conf')
    return config.get('HIM', 'him_instance')

def get_webui_url():
    config = ConfigParser.RawConfigParser();
    config.read('/etc/openhim-report-tasks.conf')
    return config.get('HIM', 'webui_url')
