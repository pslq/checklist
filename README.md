These set of scripts intend to facilitate AIX server health checks and data collection.

Under the "sh" directory, follow the standard Korn shell scripts to be executed either at one time data capture, or embedded at monitoring tools like Splunk for continuous monitoring.
 - checklist-aix.sh  -> do a data capture of the server
 - fcstat.sh -> Collect Fibre interface statistics
 - netstat.sh  -> Collect Ethernet interface statistics 
 - cpu.sh -> Collect CPU/CORE statistics
 - powerha_check.sh  -> Do a PowerHA Automate health check
 - vmstat_i.sh -> Virtual Memory interrupt related statistics
 - vmstat_s.sh  -> Virtual Memory system wide statistics
 - lspath.sh -> Disk multipath health ( Rely on AIX MPIO )
 - errpt_count.sh -> Count amount of elements out of errpt
 - seastat.sh --> Get Network Statistics from VIOS SEA Adapters



