# Known issues

1. CQ data isn't completely accurate because it is only pulled for a certain
   time frame.
2. TTR is less accurate when filtering by cause on Jenkins Interactive
   dashboard (for this reason, a new "Pipeline Availability" dashboard has been
   created with TTR graphs).
3. In interest of performance, TTR metrics are calculated on a
   schedule (every hour, 15 minutes past the hour). When PIVT is installed,
   TTR metrics will be blank due to the file not being generated yet.
