#!/usr/bin/ksh
#
# This script is distributed ASIS, no garantee & support will be provided by it
# and is licensed at GPLV3
#
#####################################################################


for ADPT in $(lsdev | awk '{ if ( $1 ~ /^ent[0-9]/ ) { if (( $2 == "Available" )&&( $0 ~ /Shared Ethernet Adapter/ )) print $1 }}')
do
  entstat -d ${ADPT} | awk '
  {
    if ( $0 ~ /ETHERNET STATISTICS/ ) {
      adpt_count = adpt_count+1;
      sub(/\(/, "", $3); sub(/)/, "", $3);
      adpt_name = $3;
      adpt[adpt_count] = adpt_name;
    } else if (( $1 == "Packets:" )&&( $3 == "Packets:" )) {
      pkg_send[adpt_name] = $2;   pkg_recv[adpt_name] = $4;
    } else if (( $1 == "Bytes:" )&& ( $3 == "Bytes:" )) {
      bytes_send[adpt_name] = $2; bytes_recv[adpt_name] = $4;
    } else if (( $0 ~ /^Transmit Errors/ )&&( $0 ~ /Receive Errors:/ )) {
      send_err[adpt_name] = $3;   recv_err[adpt_name] = $6;
    } else if (( $0 ~ /^Packets Dropped/ )&&( $0 ~ /Packets Dropped/ )) {
      send_drop[adpt_name] = $3;  recv_drop[adpt_name] = $6;
    } else if ( $0 ~ /No mbuf Errors/ ) {
      no_mbuf[adpt_name] = $4;
    } else if ( $0 ~ /Physical Port Link Status/ ) {
      phy_link_stat[adpt_name] = $5;
    } else if ( $0 ~ /Logical Port Link Status/ ) {
      log_link_stat[adpt_name] = $5;
    } else if ( $0 ~ /VLAN Tag IDs/ ) {
      spl = split($0, st, ":" );
      vlan[adpt_name] = st[2];
    }
  } END {
    prev = "";
    for ( v in adpt ) {
      en = adpt[v];
      if ( en != prev ) {
        if ( phy_link_stat[en] == "" ) phy_link_stat[en] = "Up";
        if ( log_link_stat[en] == "" ) log_link_stat[en] = "Up";
        printf("ADPT=%s SEND_PKG=%d RECV_PKG=%d SEND_BYTE=%d RECV_BYTE=%d SEND_ERR=%d RECV_ERR=%d MBUF_ERR=%d RECV_DROP=%d SEND_DROP=%d PSTAT=%s LSTAT=%s VLAN=\"%s\"\n",
                en,    pkg_send[en], pkg_recv[en], bytes_send[en], bytes_recv[en], send_err[en], recv_err[en], no_mbuf[en], recv_drop[en],
                send_drop[en], phy_link_stat[en], log_link_stat[en], vlan[en]);
      }
      prev = en;
    }
  }'
done
