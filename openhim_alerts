#!/bin/bash
source_dir=`cat /etc/openhim-report-tasks.source`
python $source_dir/run_alerting_task.py >> $source_dir/logs/alerting-task-`date +%Y-%m-%d`.log 2>&1 &
