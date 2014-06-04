# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from setuptools import setup
import os

setup(
    name='openhim-report-tasks',
    version='0.1.0',
    author='Jembi Health Systems NPC',
    packages=['openhimtasks'],
    description='OpenHIM Report and Alerting Tasks',
    long_description=open('README.md').read(),
    install_requires=[
        "mysql-python",
    ],
    data_files=[('/etc/cron.daily', ['openhim_reports.sh']),
        ('/etc/cron.hourly', ['openhim_alerts.sh']),
        ('/etc', ['openhim-report-tasks.conf']),
    ],
)

# Setup /etc source conf files
with open('/etc/openhim-report-tasks.source', 'w') as src:
    src.write(os.getcwd())
