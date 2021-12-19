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

#### Dependencies
At this moment the checklist ( regardless it's execution mode ), needs the following modules installed on the server:
  - ansible-runner
  - configparser
  - asyncio
  - influxdb_client
  - xdg

  If oracle will be monitored too, the cx_oracle python module is required<br>

  Normally all dependencies should be handled by setuptools during the install<br>
  for further information please check [setup.cfg](setup.cfg) file


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

#### Health check
  Each collector has it's own HealthCheck ( HC ) set of validations, and at each running cycle the HC messages consolidated through the collectors are pushed to syslog<br>
  The messages follow the directives defined at the checklist configuration file


#### net collector
This collector is responsible for parse network related commands<br>
on AIX and VirtualIO Servers, at this moment it will fetch the following commands:

- netstat -s
- netstat -aon
- entstat -d ( for each ent interface found on the server )


##### Health Check routines
At this moment this collector report warnings for several counters from [entstat](https://www.ibm.com/docs/en/aix/7.2?topic=e-entstat-command) command when the increment in abnormal ways, like:<br>

- a counter has not changed for the majority of it's life, but started to increase
- it changes frequently, but began to increase at a faster rate

In case the adapter is [etherchannel](https://www.ibm.com/docs/en/aix/7.2?topic=teaming-configuring-etherchannel) like adapter and is set to use LACP, it will also send messages in case LACP gets out of sync.

###### Counters currently monitored per adapter:

| Session from entstat | Counter |
| :---: | :--- |
| transmit_stats |  ( 'transmit_errors', 'receive_errors', 'transmit_packets_dropped', 'receive_packets_dropped', 'bad_packets', 's_w_transmit_queue_overflow', 'no_carrier_sense', 'crc_errors', 'dma_underrun', 'dma_overrun', 'lost_cts_errors', 'alignment_errors', 'max_collision_errors', 'no_resource_errors', 'late_collision_errors', 'receive_collision_errors', 'packet_too_short_errors', 'packet_too_long_errors', 'timeout_errors', 'packets_discarded_by_adapter', 'single_collision_count', 'multiple_collision_count' |
| 'general_stats' | ( 'no_mbuf_errors' ) |
| 'dev_stats' | ( 'number_of_xoff_packets_transmitted', 'number_of_xon_packets_transmitted', 'number_of_xoff_packets_received', 'number_of_xon_packets_received', 'transmit_q_no_buffers', 'transmit_q_dropped_packets', 'transmit_swq_dropped_packets', 'receive_q_no_buffers', 'receive_q_errors', 'receive_q_dropped_packets' ) |
| 'addon_stats' |  ( 'rx_error_bytes', 'rx_crc_errors', 'rx_align_errors', 'rx_discards', 'rx_mf_tag_discard', 'rx_brb_discard', 'rx_pause_frames', 'rx_phy_ip_err_discards', 'rx_csum_offload_errors', 'tx_error_bytes', 'tx_mac_errors', 'tx_carrier_errors', 'tx_single_collisions', 'tx_deferred', 'tx_excess_collisions', 'tx_late_collisions', 'tx_total_collisions', 'tx_pause_frames', 'unrecoverable_errors'  |
| 'veth_stats' | ('send_errors', 'invalid_vlan_id_packets', 'receiver_failures', 'platform_large_send_packets_dropped') |

###### Metrics inserted into InfluxDB
At this moment the net_collector provide the following metrics:

| metric | tag | Description |
| :--- | :---: | :--- |
| entstat | host | Server that originated the observation | 
| entstat | stats_type | Session within entstat command that generated the entry, can be : transmit_stats, general_stats, dev_stats, addon_stats, veth_stats |
| entstat | interface | Interface that generated the oservation |
| netstat_general | host |  Server that originated the observation |
| netstat_general | protocol | Protocol that generated the observation |
| netstat_general | session_group | Session within the protocol that generated information |
| netstat_general | session | Session within Session group that generated information |

#### cpu collector
#### vio collector 
#### dio collector
#### oracle collector
#### bos collector

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

- [ ] Send messages to a webhook instead of syslog ( like M$ Teams or Slack )
- [ ] Collect data from Linux Servers 
- [ ] Gather statistics from netstat -aon ( AIX )
