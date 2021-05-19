#!/usr/bin/ksh
#
# This script is distributed ASIS, no garantee & support will be provided by it
# and is licensed at GPLV3
#
#####################################################################
# Report consolidated data only
consolidate="1"

# Global vars
export PATH="${PATH}:/usr/lpp/mmfs/bin:/usr/es/sbin/cluster/utilities:/usr/es/sbin/cluster/utilities:/usr/es/sbin/cluster/sbin"
export PATH="${PATH}:/usr/lib/ras:/usr/sbin/rsct/bin:/opt/NetApp/santools/bin:/usr/DynamicLinkManager/bin:/usr/es/sbin/cluster/diag:/usr/ios/cli"
export LC_NUMERIC="POSIX"


lspath | awk -v consolidate="${consolidate}" '
{
  if ( $1 == "Enabled" )
    enabled[$2]++;
  else 
    other[$2]++;
  if ( dsk_apt[$2] !~ /$3/ )
    dsk_apt[$2] = dsk_apt[$2]" "$3;
    
  adpt_path[$3]++;

} END {
  asym_dsk_path = 0;
  dead_dsk_path = 0;
  tot_adpt_path = 0;
  tot_adpt      = 0;
  asy_adpt      = 0;

  for ( dsk in enabled )
  {
    if ( dsk % 2 != 0 )
    {
      if ( consolidate != 1 )
        print("ERROR=\"Odd amount of paths for "dsk"\"");
      asym_dsk_path= asym_dsk_path+1;
    }
    n = split(dsk_apt[dsk],P_ADPT," ");
    if ( n < 2 )
    {
      if ( consolidate != 1 )
        print("ERROR=\"Asymmetrical amount of paths for "dsk"\"");
      asym_dsk_path= asym_dsk_path+1;
    }

  }
  for ( dsk in other )
  {
    if ( consolidate != 1 )
      print("ERROR=\"Dead path at "dsk"\"");
    dead_dsk_path= dead_dsk_path+1;
  }

  for ( adpt in adpt_path )
  {
    if ( tot_adpt_path == 0 )
      tot_adpt_path = adpt_path[adpt];
    else
      if ( tot_adpt_path != adpt_path[adpt] )
        asy_adpt = 1;
    tot_adpt++;
  }
  if (( asy_adpt == 1 )&&( consolidate != 1 ))
    print("ERROR=\"Asymmetrical Path distribution across the controllers\"");
  if (( tot_adpt < 2 )&&( consolidate != 1 ))
    print("ERROR=\"Only one disk controller found\"");

  printf("asy_disk_path=%d dead_disk_path=%d asy_adpt=%d tot_adpt=%d\n", asym_dsk_path, dead_dsk_path, asy_adpt, tot_adpt);
}'
