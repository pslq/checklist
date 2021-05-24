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


lsdev | awk '{
  if ( $1 ~ /^en[0-9]/ )
  {
    if ( $2 != "Available" )
    {
      print("ERROR=\"Disabled adapter "$1"\"");
    }
  }
}'

for ADPT in $(lsdev | awk '{ if ( $1 ~ /^en[0-9]/ ) { if ( $2 == "Available" ) print $1 }}')
do
  entstat -d ${ADPT} | awk -v en="${ADPT}" '{
    if (( $1 == "Packets:" )&&( $3 == "Packets:" )) {
      send_pkg = $2;   recv_pkg = $4;
    } else if (( $1 == "Bytes:" )&&( $3 == "Bytes:" )) {
      send_bytes = $2; recv_bytes = $4;
    } else if ( $0 ~ /^Transmit Errors:/ ) {
      send_err   = $3; recv_err = $6;
    } else if ( $0 ~ /^No mbuf Errors:/ ) {
      mbuf_err   = $4;
    } else if ( $0 ~ /^Hypervisor Send Failures:/ ) {
      send_hyp_err = $4;
    } else if ( $0 ~ /^Hypervisor Receive Failures:/ ) {
      recv_hype_err = $4;
    }
  } END { 
    printf("ADPT=%s SEND_PKG=%d RECV_PKG=%d SEND_BYTE=%d RECV_BYTE=%d SEND_ERR=%d RECV_ERR=%d MBUF_ERR=%d SEND_HYPE_ERR=%d RECV_HYPE_ERR=%d AVG_SEND_BYTE=%f AVG_RECV_BYTE=%f\n",
      en, send_pkg, recv_pkg, send_bytes, recv_bytes, send_err, recv_err, mbuf_err, send_hyp_err, recv_hype_err, send_bytes/send_pkg, recv_bytes/recv_pkg);
  }'
done
