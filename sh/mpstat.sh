#!/usr/bin/ksh
#
# This script is distributed ASIS, no garantee & support will be provided by it
# and is licensed at GPLV3
#
#####################################################################


# Global vars
export PATH="${PATH}:/usr/lpp/mmfs/bin:/usr/es/sbin/cluster/utilities:/usr/es/sbin/cluster/utilities:/usr/es/sbin/cluster/sbin"
export PATH="${PATH}:/usr/lib/ras:/usr/sbin/rsct/bin:/opt/NetApp/santools/bin:/usr/DynamicLinkManager/bin:/usr/es/sbin/cluster/diag:/usr/ios/cli"
export LANG="C"
export LC_NUMERIC="POSIX"


mpstat -a 1 2 |
  awk '{
    if ( $1 == "System" )
    {
      if ( $0 ~ /mode=Donating/ ) {
        mode="ded";
      } else if ( $0 ~ /mode=Uncapped/ )
        mode="shr";
    } else {
      if ( $1 == "ALL" )
      {
        count=count+1;
        if ( mode == "shr" )
        {
          user = user + $24; sys  = sys + $25; wait = wait + $26;
          idle = idle + $27; pc   = pc + $28; ec   = ec + $29;
          ics  = ics + $11; cs   = cs  + $10; rq   = rq + $13;
          ilcs = ilcs + $30; vlcs = vlcs + $31;
        } else if ( mode == "ded" ) {
          user = user + $24; sys  = sys + $25; wait = wait + $26;
          idle = idle + $27; pc   = pc + $28; ec   =  ec + ( (pc/($24+$25))*100 );
          ics  = ics + $11; cs   = cs  + $10; rq   = rq + $13;
          ilcs = ilcs + $29; vlcs = vlcs + $30;
        }
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


