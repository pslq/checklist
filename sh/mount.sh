#!/usr/bin/ksh
#
# This script is distributed ASIS, no garantee & support will be provided by it
# and is licensed at GPLV3
#
#####################################################################
# Global vars
export LANG="C"
export LC_NUMERIC="POSIX"

mount | awk \
'{
  if ( $0 ~ /nointegrity/  ) {
    print("ERROR=\"No integrity on a filesystem will likely read to corruption\"");
  } else if (( $0 ~ /nfs/ )&&(( $0 !~ /bg/ )||( $0 !~ /intr/))) {
    print("ERROR=\"Unsafe nfs mount combination detected\"");
  }
}'

if [ -f /etc/exports ]; then
  awk '{ if ( $1 ~ /^\// ) { if ( $2 ~ /access/ ) { print $1" NGB"; } else { print $1" GB"; }}}' < /etc/exports | while read D GB
  do
    if [ ! -d "${D}" ]; then
      echo "WARN=\"${D} do not exist, the server may go into a hang during the reboot\""
    else
      if [ "${GB}" != "NGB" ]; then
        echo "WARN=\"Anyone can connect to the nfs share ${D}, be careful\""
      fi
    fi
  done
fi

