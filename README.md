OpenHIM Report and Alerting Tasks
=================================

Tasks to generate reports and error alerts for the OpenHIM. Daily summary reports will be emailed as well alerts whenever a transaction error occurs (only on the first error for a day). 

Setup
-----
Checkout the code from GitHub, update the database and run setup.py:
```
$ git clone https://github.com/jembi/openhim-report-tasks.git
$ cd openhim-report-tasks
$ mysql interoperability_layer -uroot -p < resources/update_database.sql
$ sudo python setup.py install
```

Next setup the configuration in `/etc/openhim-report-tasks.conf`.
