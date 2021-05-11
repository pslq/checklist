#!/usr/bin/ksh
#####################################################################

# Global vars
export PATH="${PATH}:/usr/lpp/mmfs/bin:/usr/es/sbin/cluster/utilities:/usr/es/sbin/cluster/utilities:/usr/es/sbin/cluster/sbin"
export PATH="${PATH}:/usr/lib/ras:/usr/sbin/rsct/bin:/opt/NetApp/santools/bin:/usr/DynamicLinkManager/bin:/usr/es/sbin/cluster/diag:/usr/ios/cli"
export LANG="C"
export LC_NUMERIC="POSIX"


if [ -x "/usr/es/sbin/cluster/diag/clconfig" ]; then
  /usr/es/sbin/cluster/diag/clconfig -v -O -tr -V normal > /tmp/.pq.${$}.clconfig 2>> /tmp/.pq.${$}.clconfig 
  if [ ${?} -ne 0 ]; then
    echo "ERROR=\"PowerHA Checkup failure\""
  fi
  egrep '^WARNING|^ERROR' /tmp/.pq.${$}.clconfig | cut -d':' -f2- | while read A ; do echo "ERROR=\"${A}\"" ; done
  if [ -f "/tmp/.pq.${$}.clconfig" ]; then
    rm -f /tmp/.pq.${$}.clconfig
  fi
fi
exit 0

