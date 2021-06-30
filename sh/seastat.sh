#!/usr/bin/ksh
#
# This script is distributed ASIS, no garantee & support will be provided by it
# and is licensed at GPLV3
#
#####################################################################

# Default run mode
RM="A"         # A for adapter, V for vlan
SLEEP_INT="60" # Amount of seconds to wait before read vlan stats when using vlan view

PATH="${PATH}:/usr/ios/cli"

#####################################################################
vlan_view()
{
  # List devices
  DEV_LIST="$(lsdev | awk '{ if ( $1 ~ /^ent[0-9]/ ) { if (( $2 == "Available" )&&( $0 ~ /Shared Ethernet Adapter/ )) print $1 }}' | xargs)"
  if [ -n "${DEV_LIST}" ]; then
    # Enable accounting
    (
      for D in ${DEV_LIST}
      do
        chdev -l ${D} -a accounting=enabled
      done
    ) 2> /dev/null > /dev/null
    sleep 60

    P1=""
  
    for D in ${DEV_LIST}
    do
      (
        (
          ioscli seastat -d ${D} -n | awk '
          {
            if ( $1 == "VLAN:" )
            {
              latest_vlan = $2;
            } else if ( $1 == "Packets:" ) {
              send_pkg_vlan[latest_vlan] = send_pkg_vlan[latest_vlan] + $2; 
              recv_pkg_vlan[latest_vlan] = recv_pkg_vlan[latest_vlan] + $4;
            } else if ( $1 == "Bytes:" ) {
              send_bytes_vlan[latest_vlan] = send_bytes_vlan[latest_vlan] + $2; 
              recv_bytes_vlan[latest_vlan] = recv_bytes_vlan[latest_vlan] + $4;
            }
          } END {
            for ( vlan in send_pkg_vlan ) {
              printf("%d %d %d %d %d\n", vlan, send_pkg_vlan[vlan], send_bytes_vlan[vlan], recv_pkg_vlan[vlan], recv_bytes_vlan[vlan]);
            }
          }'
          sleep 60
          ioscli seastat -d ${D} -n | awk '
          {
            if ( $1 == "VLAN:" )
            {
              latest_vlan = $2;
            } else if ( $1 == "Packets:" ) {
              send_pkg_vlan[latest_vlan] = send_pkg_vlan[latest_vlan] + $2; 
              recv_pkg_vlan[latest_vlan] = recv_pkg_vlan[latest_vlan] + $4;
            } else if ( $1 == "Bytes:" ) {
              send_bytes_vlan[latest_vlan] = send_bytes_vlan[latest_vlan] + $2; 
              recv_bytes_vlan[latest_vlan] = recv_bytes_vlan[latest_vlan] + $4;
            }
          } END {
            for ( vlan in send_pkg_vlan ) {
              printf("%d %d %d %d %d\n", vlan, send_pkg_vlan[vlan], send_bytes_vlan[vlan], recv_pkg_vlan[vlan], recv_bytes_vlan[vlan]);
            }
          }'
        ) | awk '{
          vlan = $1;
          vlan_list[vlan] = vlan;
          if ( send_pkg_vlan[vlan] ) { send_pkg_vlan[vlan] = $2 - send_pkg_vlan[vlan]; } else { send_pkg_vlan[vlan] = $2; }
          if ( send_bytes_vlan[vlan] ) { send_bytes_vlan[vlan] = $3 - send_bytes_vlan[vlan]; } else { send_bytes_vlan[vlan] = $3; }
          if ( recv_pkg_vlan[vlan] ) { recv_pkg_vlan[vlan] = $4 - recv_pkg_vlan[vlan]; } else { recv_pkg_vlan[vlan] = $4; }
          if ( recv_bytes_vlan[vlan] ) { recv_bytes_vlan[vlan] = $5 - recv_bytes_vlan[vlan]; } else { recv_bytes_vlan[vlan] = $5; }

        } END {
          for ( v in vlan_list )
          {
            printf("VLAN=%d send_pkg_vlan=%d send_bytes_vlan=%d recv_pkg_vlan=%d recv_bytes_vlan=%d\n", v, send_pkg_vlan[v]/60, send_bytes_vlan[v]/60, recv_pkg_vlan[v]/60, recv_bytes_vlan[v]/60);
          }
        }
        '
  
      ) &
      P1="${P1} ${!}"
    done
    wait ${P1}
  
  
    # Disable accounting
    (
      for D in ${DEV_LIST}
      do
        chdev -l ${D} -a accounting=disabled
      done
    ) 2> /dev/null > /dev/null
  fi
}
adapter_view()
{
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
}

help()
{
  echo "${0} [-a|-v]"
  echo " -a to show statistics for adapters"
  echo " -v to show statistics for vlans under SEA"
}

args=`getopt avh ${*}`
if [ ${?} -ne 0 ]; then
  help
  exit 1
fi
set -- $args
for parm
do
  case "${parm}" in
    -a) shift ; RM="A" ;;
    -v) shift ; RM="V" ;;
    -h) shift ; help ; exit 0 ;;
  esac
done

case "${RM}" in
  "A" )
    adapter_view
    ;;
  "V" )
    vlan_view
    ;;
  esac
exit 0
