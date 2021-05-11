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


vmstat -sv | awk '
  {
    if ( $0 ~ /pending disk I\/Os blocked with no pbuf/ ) {
      blocked_lvm_io = $1;
    } else if ( $0 ~ /filesystem I\/Os blocked with no fsbuf/ ) {
      fs_blocked_io = $1;
    } else if ( $0 ~ /percentage of memory used for computational pages/ ) {
      pct_comp_mem = $1;
    } else if ( $0 ~ /pages freed by the clock/ ) {
      freed_clock = $1;
    } else if ( $0 ~ /pages examined by clock/ ) {
      exam_clock = $1;
    } else if ( $2 == "iodones" ) {
      iodones = $1;
    } else if ( $0 ~ /pending I\/O waits/ ) {
      pend_io_wait = $1;
    } else if ( $0 ~ /start I\/Os/ ) {
      start_io = $1;
    } else if ( $0 ~ /cpu context switches/ ) {
      cpu_cs = $1;
    } else if ( $0 ~ /device interrupts/ ) {
      dev_intr = $1;
    } else if ( $0 ~ /software interrupts/ ) {
      sw_intr = $1;
    } else if ( $0 ~ /decrementer interrupts/ ) {
      dec_intr = $1;
    } else if ( $0 ~ /syscalls/ ) {
      syscalls = $1;
    }
  } END {
    if ( iodones <= 0 ) iodones = 1;
    if ( freed_clock <= 0 ) freed_clock = 1;
    if ( start_io <= 0 ) start_io = 1;

    freed_clock_ratio = exam_clock/freed_clock;
    iodone_ratio = pend_io_wait/iodones;
    sequential_io_ratio = iodones/start_io;

    printf("blocked_lvm_io=%f fs_blocked_io=%f pct_comp_mem=%f freed_clock_ratio=%f iodone_ratio=%f sequential_io_ratio=%f\n",
      blocked_lvm_io, fs_blocked_io, pct_comp_mem, freed_clock_ratio, iodone_ratio, sequential_io_ratio);
      


  }'

