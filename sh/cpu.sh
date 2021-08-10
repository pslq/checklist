#!/usr/bin/ksh
#
# This script is distributed ASIS, no garantee & support will be provided by it
# and is licensed at GPLV3
#

#####################################################################
# Report pctUtil based on ent% cores or online cpus ?
rep_mode="kernel" # <ec|vcpu|kernel> # report based only on ec%
# if set to "ec", will use only the ec% field to report data 
# if set to "vcpu" will use the amount of cpus are assigned to the
#   lpar + ec% to caculate total amount that the lpar can get to itself
# if set to "kernel" will report the consolidated amount of user+sys+wait

#####################################################################
count=2    # amount of mpstat samples to read
interval=1 # interval between the samples

#####################################################################
# Run Queue
# By definition ( at least what I understood ), when reading RQ
# If 0, means that a specific CPU is totaly idle
# If 1, means that is fully utilized
# If bigger than 1, means that some processes are being queued which,
#   indicates that the kernel is interchanging processes into this
#   specific CPU, which indicates a bottleneck 
#   On the old times, anything between 0 and ~10 for a specific CPU
#   would likely be ok, and above that the kernel would be swaping
#   proccesses to intensively the the system would look like hanged
#   Taking that history into consideration, there are two ways that I
#   can report RQ, the absolute value ( plain RQ output from mpstat )
#   and relative to the amount of proccess into the queue across the
#   CPUS, and under which RQ value the system will be considered 100%
#   loaded
RQ_REPORT_MODE="relative" # absolute or relative
RQ_RELATIVE_100PCT="10"   # which rq value per cpu represent 100%

# Collect shared proc pool available cores
COLL_LPAR_APP="true"

# Issue Warnings when threshold is reached
# -1 disable warning
# 01 to 99 cpu utilization or pool utilization warning
MAX_CPU_WARN="80"
MIN_CPU_WARN="30"
# Minimal amount of cores available on the pool
# -1 disable warning
# 0 to 999 minimal amount of cores before warning
MIN_CORE_WARN="2"

#####################################################################
# Global vars
export LANG="C"
export LC_NUMERIC="POSIX"
export lpar_data="$(lparstat -i |  awk \
      '{
        if ( $1 == "Type" ) {
          if ( $3 ~ /Shared/ )
            mode = "shr";
          else
            mode = "ded";
        } else if ( $0 ~ /Online Virtual CPUs/ ) {
          ent_cpu = $5;
        } else if (( $0 ~ /Entitled Capacity/ )&&( $0 !~ /Pool/ )) {
          ent_core = $4;
        }
      } END {
        print(mode,ent_cpu,ent_core);
      }')"

(
  ( 
    if [ "${COLL_LPAR_APP}" = "true" ]; then
      lparstat ${interval} ${count} | 
        awk \
          -v lpar_data="${lpar_data}" \
          -v MIN_CORE_WARN="${MIN_CORE_WARN}" \
          '{
             if (( $1 == "%user" )&&( $8 == "app" )) {
               R=1;
             } else if ( ( $1 ~ /^[0-9]/ )&&( R == 1 )) { 
               count = count+1 ;
               cpu = $8+cpu;
             } 
           } END {
             split(lpar_data,lpd," ");
             if ( lpd[1] == "shr" )
             {
               cpu = cpu/count;
               if (( MIN_CORE_WARN > -1 )&&( cpu < MIN_CORE_WARN ))
                 printf("WARN=\"Minimal amount of cores on the pool reached ( %f ), possible resource starvation\"\n", cpu);
               printf("APP=%f ", cpu/count); 
             }
           }'
    else
      echo ""
    fi
  ) &
  P1=${!}
  (
    mpstat -a ${interval} ${count} |
      awk -v RQ_REPORT_MODE=${RQ_REPORT_MODE} \
          -v RQ_RELATIVE_100PCT=${RQ_RELATIVE_100PCT} \
          -v MAX_CPU_WARN="${MAX_CPU_WARN}" \
          -v MIN_CPU_WARN="${MIN_CPU_WARN}" \
          -v rep_mode="${rep_mode}" -v lpar_data="${lpar_data}" \
     '{
        split(lpar_data,lpd," ");
        mode = lpd[1];
        ent_cpu = lpd[2];
        ent_core = lpd[3];
        if ( $1 == "ALL" )
        {
          count=count+1;
          user_total = $24+$25+$26;
          if ( lpd[1] == "shr" )
          {
            user = user + $24; sys  = sys + $25; wait = wait + $26;
            idle = idle + $27; pc   = pc + $28;
            ics  = ics + $11; cs   = cs  + $10; rq   = rq + $13;
            ilcs = ilcs + $30; vlcs = vlcs + $31;
            if ( rep_mode == "ec" ) {
              ec   = ec + $29;
            } else if ( rep_mode == "vcpu" ) {
              core_use = ent_core*$29/100;
              pct_possible_core = core_use/ent_cpu*100
              ec = ec + pct_possible_core;
            } else if ( rep_mode == "kernel" ) {
              ec = ec + user_total;
            }
          } else if ( lpd[1] == "ded" ) {
            user = user + $24; sys  = sys + $25; wait = wait + $26;
            idle = idle + $27; pc   = pc + $28; 
            ics  = ics + $11; cs   = cs  + $10; rq   = rq + $13;
            ilcs = ilcs + $29; vlcs = vlcs + $30;
            if ( rep_mode == "kernel" )
            {
              ec = ec + user_total;
            } else if ( $28/lpd[3] > 0.8 ) {
              ec   =  ec + (lpd[3]/(user_total)*100) ;
            } else {
              ec = ec + ( $28/lpd[3]*100 );
            }
          }
      } else if (( $1 ~ /^[0-9]+$/ )&&( count < 1 ))
          thread_count=thread_count+1;
      } END {
        pctUser=user/count; pctSystem=sys/count; pctIowait=wait/count;
        pctIdle=idle/count; pctCore=pc/count;    pctUtil=ec/count;
        ics = ics/count;    cs = cs/count;       ilcs = ilcs/count;
        vlcs = vlcs/count;  RunQueue=rq/count;   pc=pc/count;
        InvoluntaryContextSwitch=ics/cs;
        InvoluntaryCoreContextSwitch=ilcs/vlcs;
        if ( RQ_REPORT_MODE == "relative" )
          RunQueue = (RunQueue/thread_count)/RQ_RELATIVE_100PCT;
        if ( (pctUser+pctSystem+pctIowait) > MAX_CPU_WARN ) {
          if (( InvoluntaryCoreContextSwitch > 10 )&&( lpd[1] == "shr" )) {
            printf("WARN=\"Possible core starvation identified due high utilization + high InvoluntaryCoreContextSwitch\"\n");
          } else if ( InvoluntaryContextSwitch > 30 ) {
            printf("WARN=\"Possible cpu starvation due high InvoluntaryContextSwitch\"\n");
          } else
            printf("WARN=\"High CPU utilization\"\n");
        } else if ( (pctUser+pctSystem+pctIowait) < MIN_CPU_WARN ) {
          printf("WARN=\"CPU Utilization too low, consider cpu reduction\"\n");
        }

        printf("CPU=all pctUser=%f pctSystem=%f pctIowait=%f pctIdle=%f pc=%f pctUtil=%f InvoluntaryContextSwitch=%f InvoluntaryCoreContextSwitch=%f RunQueue=%f\n",
                        pctUser,   pctSystem,   pctIowait,   pctIdle,   pc,   pctUtil,   InvoluntaryContextSwitch,   InvoluntaryCoreContextSwitch,   RunQueue);
      }'
  ) &
  P2=${!}
  wait ${P1} ${P2}
)  | awk '
{
  if ( $0 ~ /WARN/ )
    WARN = 1;
  print($0);
} END {
  if ( WARN != 1 )
    print("WARN=\"OK\"");
}
'
