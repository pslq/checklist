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

for ADPT in $(lsdev | awk '{ if ( $1 ~ /^fcs[0-9]/ ) { if ( $2 == "Available" ) print $1 }}')
do
  fcstat -D ${ADPT} 2>&1  | awk -v ADPT="${ADPT}" \
    '{
      if ( $0 ~ /^Seconds Since Last Reset/ ) {
        last_reset = $5;
      } else if ( $1 == "Frames:" ) {
        send_frames = $2;
        recv_frames = $3;
      } else if ( $1 == "Words:" ) {
        send_words = $2;
        recv_words = $3;
      } else if ( $0 ~ /IP over FC Traffic Statistics/ ) {
        beg_ip_stat = 1;
      } else if ( $0 ~ /FC SCSI Traffic Statistics/ ) {
        beg_ip_stat = 0;
        beg_scsi_stat = 1;
      } else if ( $0 ~ /Input Requests:/ ) {
        if ( beg_ip_stat == 1 ) {
          input_req_ip = $3;
        } else if ( beg_scsi_stat == 1 ) {
          input_req_scsi = $3;
        }
      } else if ( $0 ~ /Output Requests:/ ) {
        if ( beg_ip_stat == 1 )
          output_req_ip = $3;
        else if ( beg_scsi_stat == 1 )
          output_req_scsi = $3;
      } else if ( $0 ~ /Control Requests:/ ) {
        if ( beg_ip_stat == 1 )
          control_ip = $3;
        else if ( beg_scsi_stat == 1 )
          control_scsi = $3;
      } else if ( $0 ~ /Input Bytes:/ ) {
        if ( beg_ip_stat == 1 )
          input_byte_ip = $3;
        else if ( beg_scsi_stat == 1 )
          input_byte_scsi = $3;
      } else if ( $0 ~ /Output Bytes:/ ) {
        if ( beg_ip_stat == 1 )
          output_byte_ip = $3;
        else if ( beg_scsi_stat == 1 )
          output_byte_scsi = $3;
      } else if ( $0 ~ /No DMA Resource Count/ ) {
        no_dma_resource_count = $5;
      } else if ( $0 ~ /No Adapter Elements Count/ ) {
        no_adapter_elements_count = $5;
      } else if ( $0 ~ /No Command Resource Count/ ) {
        no_command_resource_count = $5;
      }
    } END {
        printf("ADPT=%s SND_FRMS=%d RCV_FRMS=%d SND_WRD=%d RCV_WRD=%d IN_REQ_IP=%d IN_REQ_SCSI=%d OUT_REQ_IP=%d OUT_REQ_SCSI=%d CTRL_IP=%d CTRL_SCSI=%d IN_BYTE_IP=%d IN_BYTE_SCSI=%d OUT_BYTE_IP=%d OUT_BYTE_SCSI=%d NO_DMA=%d NO_ELMT=%d NO_RES=%d\n",
        ADPT, send_frames, recv_frames,  send_words, recv_words, input_req_ip, input_req_scsi, output_req_io, output_req_scsi, control_ip, control_scsi, input_byte_ip, input_byte_scsi, output_byte_ip, output_byte_scsi, no_dma_resource_count, no_adapter_elements_count, no_command_resource_count);
      }'
done
