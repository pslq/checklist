#!/usr/bin/ksh
#
# This script is distributed ASIS, no garantee & support will be provided by it
# and is licensed at GPLV3
#
#####################################################################

# Global vars
export PATH="${PATH}:/usr/lpp/mmfs/bin:/usr/es/sbin/cluster/utilities:/usr/es/sbin/cluster/utilities:/usr/es/sbin/cluster/sbin"
export PATH="${PATH}:/usr/lib/ras:/usr/sbin/rsct/bin:/opt/NetApp/santools/bin:/usr/DynamicLinkManager/bin:/usr/es/sbin/cluster/diag:/usr/ios/cli"
export LC_NUMERIC="POSIX"


lspath | awk '
{
  if ( $1 == "Enabled" )
    enabled[$2]++;
  else 
    other[$2]++;
  if ( dsk_apt[$2] !~ /$3/ )
    dsk_apt[$2] = dsk_apt[$2]" "$3;
    
  adpt_path[$3]++;

} END {
  for ( dsk in enabled )
  {
    if ( dsk % 2 != 0 )
    {
      print("ERROR=\"Odd amount of paths for "dsk"\"");
    }
    n = split(dsk_apt[dsk],P_ADPT," ");
    if ( n < 2 )
    {
      print("ERROR=\"Asymmetrical amount of paths for "dsk"\"");
    }

  }
  for ( dsk in other )
  {
    print("ERROR=\"Dead path at "dsk"\"");
  }

  tot_adpt_path = 0;
  tot_adpt = 0;
  asy_adpt = 0;
  for ( adpt in adpt_path )
  {
    if ( tot_adpt_path == 0 )
      tot_adpt_path = adpt_path[adpt];
    else
      if ( tot_adpt_path != adpt_path[adpt] )
        asy_adpt = 1;
    tot_adpt++;
  }
  if ( asy_adpt == 1 )
  {
    print("ERROR=\"Asymmetrical Path distribution across the controllers\"");
  }
  if ( tot_adpt < 2 )
  {
    print("ERROR=\"Only one disk controller found\"");
  }
}'
