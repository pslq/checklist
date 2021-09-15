This is a general data collector python/ksh program to collect health and performance data from AIX servers 
It can be executed within the server itself and upload stats data into influxdb, along with health information into syslog
So far only CPU utilization related alerts will be logged, but it's planned to be extended to all monitoring components

If direct data manipulation is desired, all data can be accessed through pq_checklist objects
and a local running deamon can be called through pq_checklist.main()

The deamon will look for configuration files using XDG standard ( ~/.config/pq_checklist.conf /etc/pq_checklist.conf <cwd>/pq_checklist.conf )


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
 - mount.sh --> Check filesystem mount parameters for unsafe settings




