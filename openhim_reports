#!/bin/bash
source_dir=`cat /etc/openhim-report-tasks.source`
python $source_dir/run_reporting_task.py >> $source_dir/logs/reporting-task-`date +%Y-%m`.log 2>&1 &
