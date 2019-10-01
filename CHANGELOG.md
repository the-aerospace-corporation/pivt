# Changelog
All notable changes to PIVT will be documented in this file

## 0.1.2.19.1 - 2019-09-23

- Added FT (BETA) dashboard
- Changed name of RCR dashboard to Release Closure Review (BETA)

## 0.1.2.19 - 2019-09-12

- Changed CQ discovery rate graph to stacked area line chart
- Added DMS_BUILD_VERSION to RCR table
- Fixed RCR dashboard, ensuring EIS runs have an EIS_BUILD_VERSION
- Added build_passed column to RCR dashboard table
- Added new CQ fields to aggregate by list on CQ dashboard
- Added discovery rate pie chart to CQ dashboard
- Added pipeline run inspector dashboard
- Moved pipeline run tagging feature from RCR dashboard to pipeline run inspector
- Added drilldown capability to RCR dashboard for digging into pipeline runs

## 0.1.2.18 - 2019-08-05

- Added "FT Run Inspector" dashboard
- Added drilldown to FT Run Inspector dashboard from Jenkins Interactive and Go Green dashboards
- Removed "files changed" table from CQ dashboard
- Updated scenario master lists

## 0.1.2.17.1 - 2019-07-16

- Fixed time range issue on "Matching Core Scenarios" table on FT Truth dashboard
- Fixed mismatched numbers on "Truth Scenario Count by CI" and "Matching Core Scenarios" tables on FT Truth dashboard
- Added description text to "Matching Core Scenarios" table on FT Truth dashboard
- Set y-axis minimum to 0 on "Actual core tests run vs truth core count by CI" panel on FT Truth dashboard
- Renamed "All truth scenarios" panel to "Truth Table" and moved it to the bottom on FT Truth dashboard
- Fixed issue where %%ci33%% runs would not show if 0 stages executed on %%ci33%% and %%ci33%% Run Inspector dashboards
- Added skipped column to UT table on Jenkins Interactive
- Added "avg failed planned regression scenarios" column to FT tables on Jenkins Interactive and Go Green dashboards

## 0.1.2.17 - 2019-07-01

- Added "pipeline" and "branch" filters to %%ci33%% dashboard
- Added beta RCR dashboard
- Added "element" and "lab" filters to ClearQuest dashboard and replace "CI"
  filter with "Verifying Org"
- Demoted CQ dashboard to beta status
- Improved performance of dashboard that report on FTs
- Fixed auto install bug
- Fixed bug in CQ data processing that didn't allow for new fields in the
  schema

## 0.1.2.16 - 2019-06-17

- Started tracking remaining P-Release pipelines
- Started pulling all %%ci33%% pipeline jobs
- Promoted VIC Utilization dashboard
- Changed default time range from "last 30 days" to "last 7 days" for Go Green, Jenkins Production Statistics,
  and Pipeline Availability dashboards
- Enhanced performance of Internal Metrics dashboard
- Added panel on usage % by user on Internal Metrics dashboard
- Added %%ci33%% build type descriptions to Jenkins Interactive and Go Green dashboards
- Fixed bug in duration matrix on Jenkins Production Statistics dashboard
- Updated %%ci33%% dashboard with info on where pipeline started
- Added "timeline" vizualization to help visualize %%ci33%% building
- Updated FT truth table
- Updated reference run implementation to using Jenkins parameters
    - AWS_VIC=blank
    - CLEARCASE_VIEW=blank
    - Build=true
    - Deploy=true
    - Functional_Test=true
- Stopped taking skipped UTs into account for total on Jenkins Interactive dashboard
- Added %%ci33%% Run Inspector dashboard allowing drilldown on one %%ci33%% pipeline run
- Added drilldown capability to %%ci33%% dashboard table
- Fixed FT pass rate calculation issue on Jenkins Interactive

## 0.1.2.15 - 2019-05-13

- Added "runs by platform type" chart to Go Green dashboard
- Added matching scenarios table to FT Truth dashboard
- Added new "Runs" table to %%ci33%% dashboard
- Changed name of nominal filter to "Reference Run" on Jenkins Interactive dashboard
- Added reference run filter to Go Green dashboard
- Added pipeline filter to Jenkins Interactive and Go Green dashboards
- Added drilldown to Go Green dashboard
- Added %%ci21%% pipeline to sources
- Added column descriptions on Go Green

## 0.1.2.14 - 2019-04-15

- Started pulling pipeline.json file from Jenkins for future use
- Now using DEFAULT_BUILD Jenkins data field to determine if a run is "nominal"
- Added "nominal build" filter to Jenkins - Interactive and Go Green dashboards
- Updated VIC status URL
- Updated Python path in Raytheon scripts
- Fixed average scenario pass rate metric on Go Green dashboard statistics table
- Added summary row to VIC Utilization statistics table
- Added platform version filters to Jenkins - Interactive and Go Green dashboards
- Fixed bug where P-Release Jenkins jobs weren't getting pulled
- Renamed and moved some configuration files
- Added configuration management module; default configs (do not touch) are in etc/default whereas
  local configs (modifiable) are in etc/local
- pipeline.properties and pipeline.json files are now pulled for every Jenkins build
- Started counting all "skipped" functional tests as "failed"
- Removed legacy %%ci33%%_BUILD_TYPE determination that used PIPELINE_URL to determine if a P-Release or Blob image was used
- Started pulling PostCore and AllCores %%ci33%% jobs
- Fixed bug in Go Green "Successful FT Runs by CI over Time" chart
- Updated FT truth table
- Added new beta dashboard: "Internal Metrics (BETA)"

## 0.1.2.13 - 2019-02-27

- Changed PIVT delivery structure to use "dist" directory
- Many enhancements to auto install
- Added CI filter to VIC Utilization dashboard
- Added utilization table to VIC Utilization dashboard
- pivt.log now rotates each week
- Split VERSION file into two: VERSION and LASTPULL
- Added MANIFEST file to delivery

## 0.1.2.12 - 2019-02-08

- Enhance cucumber report processing to make it deterministic when there are duplicate scenarios
- Added min and max scenarios run columns to Go Green stats table
- Changed Go Green stats table to disregard runs with no pass/fail numbers
- Fixed bug that would cause a crash if the CQ index couldn't be deleted after processing data
- Added FT truth data beta dashboard that makes use of scenario "truth table"
- Added sanity checks to auto install script

## 0.1.2.11 - 2019-01-25

- Added "platform build" filter to Go Green dashboard
- Changed CI on VIC Utilization dashboard to use ci_allocation field instead of ci field from VIC status data
- Added Yield (BETA) dashboard
- Changed Jenkins - Interactive FT TTR calculation to be based on Jenkins build instead of individual scenario
- Fixed ClearCase view bug in Pipeline Availability dashboard
- Increased robustness of auto install process
- Now filtering out integrity FT tests
- Now filtering out failed and aborted FT runs on Go Green
- Added scenario execution count chart to Go Green
- Fixed Cucumber report processing to account for failed backgrounds

## 0.1.2.10.3 - 2019-01-17

- Fixed Go Green dashboard General Statistics table average calculation
- Fixed Splunk file ingestion

## 0.1.2.10.2 - 2019-01-15

- Fixed Go Green dashboard ClearCase view filtering to account for pipeline build numbers at the end of view names

## 0.1.2.10.1 - 2018-12-13

- Fixed VIC Utilization dashboard, preventing spikes in activity graphs

## 0.1.2.10 - 2018-12-10

- Refactored PIVT deployment directory structure. PIVT is now installed using directories like var, etc, bin, etc.
- Updated RTN scripts to work with this change
- Added util.py for common functions and constants
- Refactored export_jenkins.py and process.py, allowing changes to be made easier
- Started processing VIC data from Jenkins
- Turned most Splunk dashboard dropdowns into multi-select inputs
- Enhanced cause derivation to enable filtering on 2nd-wave jobs
- Started pulling P-Release jobs
- Added pulling of %%ci25%%, %%ci24%%, %%ci23%% FT jobs
- Started pulling VIC status
- Added VIC Utilization (Beta) dashboard
- Fixed %%ci30%% sources

## 0.1.2.9.2 - 2018-12-3

- Fixed Jenkins Interactive FT table MTTR bug

## 0.1.2.9.1 - 2018-11-14

- Fixed Jenkins Interactive FT TTR graph bug

## 0.1.2.9 - 2018-11-07

- Removed need for temp folder during processing, speading up the ingest process by orders of magnitude when processing many archives
- Removed cause determination from process.py and moved it to the source: export_jenkins.py, greatly increasing accuracy
- Now calculating DR open backlog over all time regardless of time window on CQ - Interactive dashboard
- Removed TTR calculation from process.py and moved it into Splunk using a new custom Splunk command, "ttr"
- New beta dashboard: "Pipeline Availability"
- Moved beta dashboards to new "Beta" dropdown
- Started pulling self-service VIC start/shutdown data to lay the groundwork for VIC utilization visualization
- Changed Jenkins Interactive UT pass rate calculation from `pass / total` to `pass / (pass + fail)` (excludes skips)
- General code improvements
- Fixed bug where FT data wasn't getting processed if multiple archives were processed at once

## 0.1.2.8 - 2018-10-18

- Fixed and enhanced cause and FT TTR processing
- Moved "Functional Test Scenario Statistics (BETA)" dashboard out of beta and renamed to "Go Green Dashboard"
- Changed "Go Green Dashboard" tag filter to include only "All," "Core," and "Not Core" options; added release filter
- Added multiple charts on "Go Green Dashboard"
- Completely fixed cause issue. Cause is now retrieved at the source.

## 0.1.2.7 - 2018-09-24

- Now processing cause and TTR more accurately using metadata solution, eliminating the need for persistent "temp" folder
- Now processing feature and scenario data from FT reports, exposing FT tags
- New "Functional Test Scenario Statistics (BETA)" dashboard
- Now monitoring "develop" and "master" "instances" of %%ci33%% core builds

## 0.1.2.6 - 2018-09-05

- %%ci33%% data is now collected and visualized in a separate beta %%ci33%% dashbard
- Fixed bug with Jenkins UT and FT execution count graphs
- Renamed export.py to export_jenkins.py
- export_jenkins.py no longer creates empty files
- process.py no longer loads existing data if there is no new data
- Fixed Jenkins unit test pass rate calculations
- Added DR age units to CQ dashboard
- Changed Jenkins "Avg Success Duration" metric to use UNSTABLE as well as SUCCESS for UTs and FTs
- Cleaned up CQ Perl script and renamed to export_cq.pl
- Updated runner shell scripts
- Fixed bug in Jenkins Production Statistics pipeline duration chart
- Fixed duplicate FT report bug
- Added weekly cause
- Improved general code robustness
- Started pulling %%ci30%% data from Jenkins

## 0.1.2.5 - 2018-07-17

- Added release dropdown to Jenkins Interactive dashboard
- Fixed dashboard refreshing issue

## 0.1.2.4 - 2018-06-28

- Added RTN scripts
- Removed cached Jenkins dashboard from PIVT Splunk app
- Added dynamic span to dashboards
- Changed default time range to last 7 days for interactive dashboards
- Data/temp directory now persists
- Fixed UT and FT TTR calculation
- Updated sources
- Added logging to files
- Collect now uses more detailed timestamp for zip file name
- Export tracks "unpulled" builds so they can be pulled next run
- TTR is now calculated per iteration
- Fixed CQ data columns sorting issue
- Fixed CQ duplicate data issue

## 0.1.2.3 - 2018-05-21

Added
- "Iteration" filter on Jenkins Interactive and Jenkins Production Statistics dashboards
- "Cause" filter on Jenkins Interactive and Jenkins Production Statistics dashboards
- Number of Jobs by Iteration graph on Jenkins PRoduction Statistics dashboard
- Number of Jobs by Cause graph on Jenkins PRoduction Statistics dashboard
- More Jenkins fields available to Splunk like PIPELINE_VERSION

Changed
- CQ query now pulls all iterations and 1.6 labels removed from ClearQuest Interactive dashboard
- Splunk indexes renamed with "pivt_" prefix
- Removed Jenkins - All CIs/Stages - Last 30 Days dashboard
- export.py looks for parent and child FT reports instead of one or the other

Fixed
- Bug with TTR calculation
- Bug with naming of archive in collect.py

## 0.1.2.2 - 2018-05-09

Added
- Filters on Jenkins Production Statistics dashboard to select subsystem, ci, timerange
- Trendline to job runs graph on Jenkins Production Statistics dashboard
- Average pipeline phase duration graph Jenkins Production Statistics dashboard
- Same as above but in a matrix format

## 0.1.2.1 - 2018-05-03

Added
- process.py now looks for splunk_host env variable and uses localhost if none is found
- process.py checks for pivt/default if pivt/local does not exist
- exception handling to export.py
- export.py pulls FT reports from child jobs if parent has none

Fixed
- Jenkins Production Statistics dashboard's last pull date is updated like the others
- export.py use of configparser to correctly use legacy functions

## 0.1.2 - 2018-04-27

Added
- Jenkins - All CIs/Stages - Last 30 Days dashboard that uses scheduled reports for efficiency. Reports run every day at 2 am
- Jenkins Production Statistics dashboard that gives overall view into Jenkins production pipeline

Changed
- Moved sources.csv to the pivt folder
- Renamed sources.csv to sources.txt
- Consolidated users for use by a script in Splunk to just one user
- Updated process.py to use 'id' field instead of 'dbid' field as key for CQ DRs
- Jenkins data pulls no longer overlap and exportpy makes much less requests on the Jenkins server
- Better logging in export.py
- Renamed Jenkins dashboard to Jenkins - Interactive
- Renamed ClearQuest dashboard to ClearQuest - Interactive
- Switched to legacy functions for configparser in export.py to support earlier versions of Python 3

## 0.1.1 - 2018-04-09

Added
- process.py arguments --no-jenkins and --no-cq to exclude processing of jenkins or cq data
- PIVT dashboards "last pulled date" now updated automatically
- Now pulling package, provision, and stage data from Jenkins
- Section in README for Splunk users to add

Changed
- Moved Jenkins job URLs from export.py to their own file (sources.csv)
- Jenkins runs/day metric calculation now uses earliest and latest from time window
- Jenkins MTTR metric field is no longer blank if success is 0% or 100%

Fixed
- Updated CQ Splunk index in process.py delete query
- Typo in copyright
- Removed check for duplicate DRs in existing CQ_Data.csv file
- Drilldown for all result bar graphs
- Charts with data not filling the specified time window now show entire time window
- All charts' x-axis now line up with each other
- Trendlines work correctly now
