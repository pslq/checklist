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


mpstat -a 1 1 |
  awk '{
    if ( mode == "" )
    {
      if ( $29 == "ilcs" )
        mode="shr";
      else
        mode="ded";
        
    } else if ( $1 == "ALL" )
    {
      count=count+1;
      v10 = $10+v10; v11 = $11+v11; v13 = $13+v13; v30 = $30+v30;
      v17 = $17+v17; v18 = $18+v18; v19 = $19+v19; v20 = $20+v20;
      v21 = $21+v21; v22 = $22+v22; v24 = $24+v24; v25 = $25+v25;
      v26 = $26+v26; v27 = $27+v27; v28 = $28+v28; v29 = $29+v29;
    }
  } END {
    if ( v10 > 0 ) v10=v10/count; if ( v11 > 0 ) v11=v11/count;
    if ( v13 > 0 ) v13=v13/count; if ( v17 > 0 ) v17=v17/count;
    if ( v18 > 0 ) v18=v18/count; if ( v19 > 0 ) v19=v19/count;
    if ( v20 > 0 ) v20=v20/count; if ( v21 > 0 ) v21=v21/count;
    if ( v22 > 0 ) v22=v22/count; if ( v24 > 0 ) v24=v24/count;
    if ( v25 > 0 ) v25=v25/count; if ( v26 > 0 ) v26=v26/count;
    if ( v27 > 0 ) v27=v27/count; if ( v28 > 0 ) v28=v28/count;
    if ( v29 > 0 ) v29=v29/count; if ( v30 > 0 ) v30=v30/count;

    if ( v10 > 0 )
      ilcs_ratio=(v11*100)/v10;
    else
      ilcs_ratio=(v11*100);
    if ( v30 > 0 )
      vlcs_ratio=(v29*100)/v30;
    else
      vlcs_ratio=(v29*100);

    core_aff=v17+v18;
    mcm_aff=v19+v20;
    poor_aff=v21+v22;

    printf("CPU=all pctUser=%f pctSystem=%f pctIowait=%f pctIdle=%f pctUtil=%f InvoluntaryContextSwitch=%f InvoluntaryCoreContextSwitch=%f RunQueue=%f ent=%f\n",
    v24,v25,v26,v27,v28,ilcs_ratio,vlcs_ratio,v13,v20);

  }'

