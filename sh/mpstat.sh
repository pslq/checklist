#!/usr/bin/ksh
#
# This script is distributed ASIS, no garantee & support will be provided by it
# and is licensed at GPLV3
#
#####################################################################
# Report pctUtil based on ent% cores or online cpus ?
rep_mode="ec" # <ec|vcpu> # report based only on ec%
# if set to "ec", will use only the ec% field to report data ( can go beyond 100% )
# if set to "vcpu" will use the amountof cpus are assigned to the lpar + ec% to caculate total amount that the lpar can get to itself
##
count=2    # amount of mpstat samples to read
interval=1 # interval between the samples
#####################################################################
# Global vars
export LANG="C"
export LC_NUMERIC="POSIX"


mpstat -a ${interval} ${count} |
  awk -v rep_mode="${rep_mode}" -v lpar_data="$(lparstat -i |  awk \
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
  }')" '{
    split(lpar_data,lpd," ");
    if ( $1 == "ALL" )
    {
      count=count+1;
      if ( lpd[1] == "shr" )
      {
        user = user + $24; sys  = sys + $25; wait = wait + $26;
        idle = idle + $27; pc   = pc + $28;
        ics  = ics + $11; cs   = cs  + $10; rq   = rq + $13;
        ilcs = ilcs + $30; vlcs = vlcs + $31;
        if ( rep_mode == "ec" )
          ec   = ec + $29;
        else {
          ec = ec + ( (lpd[3]*$29)/lpd[2]);
        }
      } else if ( lpd[1] == "ded" ) {
        user = user + $24; sys  = sys + $25; wait = wait + $26;
        idle = idle + $27; pc   = pc + $28; ec   =  ec + ( (pc/($24+$25))*100 );
        ics  = ics + $11; cs   = cs  + $10; rq   = rq + $13;
        ilcs = ilcs + $29; vlcs = vlcs + $30;
      }
    }
  } END {
    pctUser=user/count; pctSystem=sys/count; pctIowait=wait/count;
    pctIdle=idle/count; pctCore=pc/count;    pctUtil=ec/count;
    ics = ics/count;    cs = cs/count;       ilcs = ilcs/count;
    vlcs = vlcs/count;  RunQueue=rq/count;   pc=pc/count;
    InvoluntaryContextSwitch=ics/cs;
    InvoluntaryCoreContextSwitch=ilcs/vlcs;
    printf("CPU=all pctUser=%f pctSystem=%f pctIowait=%f pctIdle=%f pc=%f pctUtil=%f InvoluntaryContextSwitch=%f InvoluntaryCoreContextSwitch=%f RunQueue=%f\n",
                    pctUser,   pctSystem,   pctIowait,   pctIdle,   pc,   pctUtil,   InvoluntaryContextSwitch,   InvoluntaryCoreContextSwitch,   rq);
  }'
