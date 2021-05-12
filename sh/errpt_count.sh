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


errpt -aD | awk '{
  split($0, sp, ":");
  if ( $0 ~ /^Class/ ) {
    CLASSES[sp[2]] = CLASSES[sp[2]] +1;
  } else if ( $0 ~ /^Type/ ) {
    TYPES[sp[2]] = TYPES[sp[2]] +1;
  }
} END {
  ST="";
  for ( v in CLASSES )
    ST=ST" "v"="CLASSES[v];
  for ( v in TYPES )
    ST=ST" "v"="TYPES[v];
  print ST;
}' | sed 's/  */ /g'

