# Checklist
This is the repository for the AIX's Checklist tool

## Checklist ?!
The checklist started as a Korn Shell script to facilitate health-check assessments and performance evaluation of AIX Servers
As it evolved, some of it's contents were split into smaller scripts that could be integrated into 3rd party monitoring tools, like Splunk.
However as analysis became more complex and correlate behavior of several servers in parallel became more important, a major re-write in Python is being done.
At this moment moment about 10% of the original checklist have been ported to Python and it supports:
 - AIX servers 
 - PowerVM Virtual IO Servers
 - Oracle Databases ( using oracle_cx python module )

## Python Script

The Python collector can run locally, within the server or use Ansible to fetch data from remote servers.<br>
All stats collected are parsed and sent to influxdb in order to allow for performance measurement over the time and health-check operations.<br>
All scripts are under [pq_checklist](pq_checklist/) directory, which works as a Python module.<br>
The entry point is pq_checklist.main, as described into the main.py file.<br>

### How to run it
You can run the checklist as a standard process through the "main.py" script or interactively from python shell

#### OS Shell ( Bash/KSH/etc )
  In order to facilitate execution, a shell wrapper is provided<br>

  <pre>$ ./main.py -d</pre>

#####  Available parameters

| Parameter | Description |
| ---: | :--- |
| \-h | Help Message |
| \-l <file> | A influxdb dumpfile to load into the local database ( cannot be used along with -d ) |
| \-d | Run the checklist as a foreground daemon |
| \-c | Specify a config file to be used, skip search for a config file or create a new one |

#### Python shell
Within python3 shell it can be executed as a python module as shown bellow

<pre>
import pq_checklist
config,logger = pq_checklist.get_config(log_start=True,config_path='/etc/pq_checklist.conf')
collector_instance = pq_checklist.general_collector.collector(config=config,logger=logger)
collected_data = collector_instance.collect_all()
</pre>

##### API Documentation
Most of the classes are properly commented out and python's using sphinx formatting

---

### Instalation
The Instalation and dependency tracking is being done using Python's setuptools.

  <pre>python3 setup.py install</pre>

#### Packaging and redistribution
Optionally you can package it into a bdist_whell or even a rpm package in order to facilitate distribution.<br>
Please check setuptools [documentation](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/#id67) for further details.

---

### Configuration
At first execution the checklist will look for it's configuration file following [XDG](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html) variables.<br>
If not found it will also look into **/etc** and **/opt/freeware/etc**, if not found there either it will create one at **\${XDG_CONFIG_HOME}**, using the [pq_checklist/pq_checklist.conf.template](pq_checklist/pq_checklist.conf.template) as template<br>
Key components of the configuration are organized as sessions, and those are:<br>

#### [INFLUXDB]
This session define the database connection parameters and also allow the checklist.<br>
If no database will be used, all query information will be dumped into *dump_file* destination<br>
It's advisable to not remove the parameter *url*.<br>
If no database will be used, just leave with default value "\<influxdb_url>\"<br>
Available tags:<br>

| Tag | Default | Description |
| :---: | :---: | :--- |
| url | \<influxdb_url\> | Url used to connect into influxDB |
| token | \<influxdb_token\> | InfluxDB authentication token |
| org | \<influxdb_org\> | Organization that will be used within InfluxDB |
| bucket | \<influxdb_bucket\> | Bucket into InfluxDB |
| timeout | 50000 | amount of seconds before consider that the query failed |
| dump_file | \/tmp\/influx_queries.json | File to store failed queries or any query if a invalid db url is provided |

#### [ANSIBLE]
When running on Ansible mode, this session define targets, along with which ansible playbook will be played, along with where the artifacts and modules are/will stored
It's advisable to not change the playbook or modules, unless you're extending the checklist capabilities.<br>
Available tags:<br>

| Tag | Default | Description |
| :---: | :---: | :--- |
|host_target | all | Host group which will be the target of the checklist |
|playbook | getperf.yml | Playbook that will be executed, right now the checklist look's for specifically defined into getperf.yml |
|private_data_dir | ansible | Base directory that holds ansible related assets |

#### [MODE]
Under this session its defined how the checklist will behave, which collectors are to be loaded and if the health check routines that exists within the collectors are to be called<br>
Available tags:<br>

| Tag | Default | Description |
| :---: | :---: | :--- |
| mode | local | If the checklist will get statistics from the **local** server or if it will use **ansible** to fetch data |
| healthcheck | True | If the healthcheck routine provided by the collector will be called upon its execution |
| collectors | \[ 'net', 'cpu', 'vio', 'dio' \] | Collectors to load with the checklist, please see collectors session for further details |

#### [LOOP]
This session define the interval, which the checklist will collect data
Available tags:<br>

| Tag | Default | Description |
| :---: | :---: | :--- |
| interval | 300 | Seconds between collection cycles ( only valid when using general_collector's loop ) |
| hc_loop_count | 2 | Interval in collection cycles to call Health routines, in this example hc will be performed every 600 seconds |

#### [CPU] && [ORACLE]
Those are sessions tied to collectors, please check the collector part of this document for details about these config sessions 

---

### Collectors
In order to simplify development, the checklist data gathering capabilities have been split into modules, which are called collectors.<br>
Each collector provide essentially two (02) things :
 - Measurements :<br>
   * Data to be inserted into InfluxDB for further analysis
 - Health Check :<br>
   * Automated analysis of the server health, based on the collected data

>**Important:**<br>
> Whatever message comes out from the health check functions just means something that should be checked from MY perspective.<br>
> Don't engage into tuning crusades or HW capacity endeavors without engage the proper support channels ( like your solution provider )

#### net collector
#### cpu collector
#### vio collector 
#### dio collector
#### oracle collector

---

## Legacy / Standalone shell scripts
The scripts at sh directory are intended to be used in conjunction with [Splunk](https://docs.splunk.com/Documentation/Splunk/8.2.3/SearchReference/Script) and are not really used by the python collector or ansible anymore
Follow the list of scripts and it's purpose:

| Script           | Description |
| :--- | :--- |
| checklist-aix.sh | do a data capture of the server |
| fcstat.sh | Collect Fibre interface statistics |
| netstat.sh | Collect Ethernet interface statistics |
| cpu.sh | Collect CPU/CORE statistics |
| powerha_check.sh | Do a PowerHA Automate health check |
| vmstat_i.sh | Virtual Memory interrupt related statistics |
| vmstat_s.sh | Virtual Memory system wide statistics |
| lspath.sh | Disk multipath health ( Rely on AIX MPIO ) |
| errpt_count.sh | Count amount of elements out of errpt |
| seastat.sh | Get Network Statistics from VIOS SEA Adapters |
| mount.sh | Check filesystem mount parameters for unsafe settings |

## TODO
