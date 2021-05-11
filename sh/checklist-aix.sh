#!/usr/bin/ksh
#
# This script is distributed ASIS, no garantee & support will be provided by it
# and is licensed at GPLV3
#
# Author:  Paulo Sergio Lemes Queiroz 
#
#
#####################################################################

# Global vars
export PATH="${PATH}:/usr/lpp/mmfs/bin:/usr/es/sbin/cluster/utilities:/usr/es/sbin/cluster/utilities:/usr/es/sbin/cluster/sbin"
export PATH="${PATH}:/usr/lib/ras:/usr/sbin/rsct/bin:/opt/NetApp/santools/bin:/usr/DynamicLinkManager/bin:/usr/es/sbin/cluster/diag:/usr/ios/cli"
export MY_PID="${$}"
export OUTDIR="/tmp/.check_${MY_PID}"
export MY_PTS="$(ps -fT ${MY_PID} | awk -v PS=${MY_PID} '{ if ( $2 == PS ) print $6; }')"
export DST_FILE="$(dirname ${OUTDIR})/check_$(hostname)-$(date '+%m-%d-%Y-%H-%M').tar"
export FILE_CHECK="N"
export USER_CHECK="N"
export GET_SNAP="N"
export REMOVE_CHECK="N"
export GET_CHECKLIST="N"
export KDB_OK="Y"
export GETPERF="N"
export COLL_SEC="300"
export CALLED_PARMS="${@}"
export CHIELDS=""
export LANG="C"
export GET_SVMON="Y"
export GET_TRUSTCHK="Y"
export GET_TRACE="N"
export GET_GPFS="Y"
export TRUSTCHK_PID=""
export GET_IPTRACE="N"
export GET_HACMP="Y"
export SKIPDISK="N"

# Environment variables that can change process behavior
export ENV_VAL="MALLOCTYPE|MALLOCOPTIONS|MEMORY_AFFINITY|SPINLOOPTIME|YIELDLOOPTIME|AIXTHREAD_MUTEX_FAST|AIXTHREAD_ENRUSG|AIXTHREAD_SCOPE|EXTSHM|LDR_CNTRL|VMM_CNTRL"
#
# Look out for sudo users
if [ -n "${SUDO_COMMAND}" -o -n "${SUDO_UID}" ]; then
  echo "Direct execution through sudo has not been tested, become root before execute the checklist"
  exit 1
fi
if [ $(id -u) -ne 0 ]; then
  echo "Must be executed by root"
  exit 1
fi

# Create repository dir
mkdir ${OUTDIR}


# Check if the program exist on the path
check_exist_bin()
{
  RET=1
  if [ -n "${1}" ]; then
    type ${1} > /dev/null 2>/dev/null
    RET=${?}
  fi
  return ${RET}
}

# Run commands in background 
my_background_checker()
{
  if [ -n "${2}" ]; then
    echo "INFO : BACKGROUND : Background checker called for ${2} to monitor ${1}"
  fi
  if [ -n "${1}" -a "${MY_PID}" != "${1}" ]; then
    P="${1}"
    if [ "$( ps -fT ${P} | awk -v PS="${P}" -v PTS=${MY_PTS} '{ if (( $2 == PS )&&( $1 == "root" )&&( $3 != 1 )&&( $6 == PTS )) print "OK" }')" = "OK" ]; then	
      C=0
      ST="E"
      while [ ${C} -lt 10 ]
      do
        if [ -z "$(ps -T ${PID} | awk -v PTS=${MY_PTS} -v PS="${P}" '{ if (( $1 == PS )&&( $2 == PTS )) print $0; }')" ]; then
          ST="O"
          C=30
        else
          sleep 30
        fi
        C=${C}+1
      done
      if [ ${ST} == "E" ]; then
        echo "WARNING : MAIN : Process hanged and killed due execution timeout: $(ps -flT ${P} -o pid,ppid,ruser,args)" 
        kill -9 ${P} >> ${OUTDIR}/my_background_checker 2>> ${OUTDIR}/my_background_checker
      fi
    fi
  fi
}

my_hbastat()
{
  check_exist_bin hbastat
  if [ ${?} -eq 0 -a -f "${1}" ]; then
    HBA="$(awk '{ if ( $0 ~/Parent HBA Device/ ) print $NF;  }' < ${1})"
    if [ -n "${HBA}" ]; then
      hbastat -d ${HBA}        >> ${OUTDIR}/netinfo/hbastat_d_${HBA}        2>> ${OUTDIR}/netinfo/hbastat_d_${HBA}
      hbastat -qset all ${HBA} >> ${OUTDIR}/netinfo/hbastat_qset_all_${HBA} 2>> ${OUTDIR}/netinfo/hbastat_qset_all_${HBA}
    fi     
  fi
}

my_entstat()
{
  check_exist_bin entstat
  if [ ${?} -eq 0 -a -n "${1}" ]; then
    if [ ! -f "${OUTDIR}/netinfo/lsattr_El_${1}" -a -f "${OUTDIR}/dev_attr/${1}" ]; then
      (
        cd ${OUTDIR}/netinfo
        ln -s ../dev_attr/${1} lsattr_El_${1}
      )
    fi
    entstat -d ${1} > ${OUTDIR}/netinfo/entstat_d_${1} 2>> ${OUTDIR}/netinfo/entstat_d_${1}
    entstat -t ${1} > ${OUTDIR}/netinfo/entstat_t_${1} 2>> ${OUTDIR}/netinfo/entstat_t_${1}
    if [ "${GETPERF}" = "Y" ]; then
      (
        sleep ${COLL_SEC}
        entstat -d ${1} > ${OUTDIR}/netinfo/entstat_d_${1}_end 2>> ${OUTDIR}/netinfo/entstat_d_${1}_end
        entstat -t ${1} > ${OUTDIR}/netinfo/entstat_t_${1}_end 2>> ${OUTDIR}/netinfo/entstat_t_${1}_end
      ) &
      export CHIELDS="${CHIELDS} ${!}"
    fi
    if [ -n "$(grep 'Device Type: Shared Ethernet Adapter' ${OUTDIR}/netinfo/entstat_d_${1})" ]; then
      (
        if [ ! -d "${OUTDIR}/ioscli" ]; then
          mkdir -p ${OUTDIR}/ioscli
        fi
        if [ ! -e "${OUTDIR}/ioscli/entstat_d_${1}" ]; then
          cd ${OUTDIR}/ioscli
          ln -s ../dev_attr/${1} lsattr_El_${1}
          ln -s ../netinfo/entstat_d_${1} .
        fi
      )
    fi
  else
    echo "ERROR : ENSTAT : Entstat command not found or empty request |${1}|"
  fi
}

my_iostat_sfm_parse()
{
  if [ -f "${1}" -a -n "${2}" ]; then
    awk -v TYPE="${2}" '{
           if ( $0 ~ /^FS Name/  )
             c=c+1;
           if ( $1 ~ /\// )
           {
             if ( $4 > 0 )
             {
               avg_io_size=$3/$4;
             } else {
               avg_io_size=0;
             }
             tot=$5+$6;
             if ( tot > 0 )
             {
               perc_read=$5*100/tot;
               perc_write=$6*100/tot;
             } else {
               perc_read=0;
               perc_write=0;
             }
             c1=0;
             f=0;
             for ( V in disk_label )
             {
               if ( disk_label[c1] == $1 )
               {
                 f=1;
                 if ( avg_io_size > avg_io_size_tot[c1] )
                 {
                   avg_io_size_tot[c1] = avg_io_size;
                   perc_read_tot[c1] = perc_read;
                   perc_write_tot[c1] = perc_write;
                 }
               }
               c1=c1+1;
             }
             c1=c1+1;
             if ( f == 0 )
             {
               avg_io_size_tot[c1] = avg_io_size;
               perc_read_tot[c1] = perc_read;
               perc_write_tot[c1] = perc_write;
               disk_label[c] = $1;
             }
           }
         } END {
           for ( V in disk_label )
           {
             if ( avg_io_size_tot[V] > 1 )
               print "INFO : IOSTAT SFM "TYPE" : "disk_label[V]" IO Size: "avg_io_size_tot[V]" Kbytes Read ratio: "perc_read_tot[V]"% Write ratio "perc_write_tot[V]"%";
           }
         }' < ${1}
  fi
}
# Run fcstat on a adapter and calculate utilization
my_fcstat()
{
  if [ ${1} ]; then
    check_exist_bin fcstat
    if [ ${?} -eq 0 ]; then
      if [ ! -d "${OUTDIR}/fcstat" ]; then
        mkdir -p ${OUTDIR}/fcstat
      fi
      fcstat    ${1} 2>> ${OUTDIR}/fcstat/fcstat_${1} >> ${OUTDIR}/fcstat/fcstat_${1}
      fcstat -e ${1} 2>> ${OUTDIR}/fcstat/fcstat_e_${1} >> ${OUTDIR}/fcstat/fcstat_e_${1}
      fcstat -D ${1} 2>> ${OUTDIR}/fcstat/fcstat_D_${1} >> ${OUTDIR}/fcstat/fcstat_D_${1}
      if [ ${?} -eq 0 ]; then
        if [ "${GETPERF}" = "Y" ]; then
          (
            C=${COLL_SEC}
            while [ ${C} -gt 0 ]
            do
              fcstat -D ${1} ${OUTDIR}/fcstat/fcstat_D_${1}_${C}
              sleep 5
              C=$((C-5))
            done
          ) 
        fi
      fi
    fi
  fi
}

################################# File Permissions
validate_permissions()
{
cat << EOTEXT > ${OUTDIR}/.check_core.${$}.sh
#!/bin/ksh
if [ -e "\${1}" ]; then
  file \${1} |  awk '{ if ( \$0 ~ /AIX core file/ ) { print \$1; }}' | sed 's/:$//g'
fi
exit 0
EOTEXT
  chmod 755 ${OUTDIR}/.check_core.${$}.sh

  for VG in $(cat ${OUTDIR}/lvminfo/lsvg_o)
  do
    for FS in $(lsvgfs ${VG})
    do
      find ${FS} -xdev \( -type f \(  -perm -o+w -o -exec ${OUTDIR}/.check_core.${$}.sh {} \; \) \) -o \( -type d -perm -o+w ! -perm -1000 \) -print | while read F
      do
        echo "WARNING : PERM : possible vulnerable file found at ${F} ( permissions : $(ls -ld ${F} | awk '{ print $1; }' | xargs) )"
      done
    done
  done

  # Check inittab / crontab
  (
    (
      for i in $(lsitab -a | sed "{ s/'//g; s/\"//g; }" | cut -d':' -f4- | cut -d'#' -f1)
      do
        if [ -e "${i}" ]; then
          ls -dl ${i} 2>/dev/null
        fi
      done
    ) | sort -u | awk '{ if (( $3 != "root" )&&( $3 != "bin" )&&( $3 != "pconsole" )&&( $4 != "bin" )&&( $4 != "system" )&&( $4 != "security" )&&( $4 != "cron" )) { print "WARNING : PERM : Possible exposure at inittab on "$0; }}'
    (
      for i in $(crontab -l | grep -v ^# | cut -d'#' -f1 | awk '{ for ( x=6 ; x<= NF ; x++ ) { print $x" " }}' )
      do
        if [ -e "${i}" ]; then
          ls -ld ${i} 2>/dev/null
        fi
      done
    ) | sort -u | awk '{ if (( $3 != "root" )&&( $3 != "bin" )&&( $3 != "pconsole" )&&( $4 != "bin" )&&( $4 != "system" )&&( $4 != "security" )&&( $4 != "cron" )) { print "WARNING : PERM : Possible exposure at crontab on "$0; }}'
  )
}
################################# ITCS related to users
validate_userinfo()
{
   lsuser -a maxage minage minalpha minother minlen histsize home umask login rlogin loginretries ALL > ${OUTDIR}/lsuser_ALL 2>> ${OUTDIR}/lsuser_ALL
  (
    while read USR B
    do
      unset maxage minage minalpha minother minlen histsize home umask login rlogin loginretries
      eval ${B}
      if [ ${minage} -ne 1 ]; then
        echo "INFO : LSUSER : UID minage for ${USR} not set to 1"
      fi
      if [ ${histsize} -lt 8 ]; then
        echo "INFO : LSUSER : UID histsize for ${USR} lower than 8"
      fi
      if [ ${minlen} -lt 8 ]; then
        echo "INFO : LSUSER : UID minlen for ${USR} smaller than 8"
      fi
      if [ ${minother} -lt 1 ]; then
        echo "INFO : LSUSER : UID minother for ${USR} smaller than 1"
      fi
      if [ ${minalpha} -lt 1 ]; then
        echo "INFO : LSUSER : UID minalpha for ${USR} smaller than 1"
      fi
      if [ ${maxage} -gt 13 ]; then
        echo "INFO : LSUSER : UID maxage for ${USR} gratter than 13"
      fi
      if [ ${maxage} -eq 0  ]; then
        if [ "${login}" = "true" -o "${rlogin}" = "true" ]; then
          echo "INFO : LSUSER : UID ${USR} defined as non-expiring password and is allowed to login or rlogin"
        fi
      fi
      if [ ${umask} -ne 77 -a ${umask} -ne 22  ]; then
        echo "INFO : LSUSER : UID umask for user ${USR} is neither 77 or 22"
      fi
      if [ ${loginretries} -gt 5 ]; then
        echo "INFO : LSUSER : UID loginretries defined to ${USR} gratter than 5"
      fi
      if [ -d "${home}" ]; then
        if [ "$(ls -ld ${home} | awk '{ print $3; }')" != "${USR}" ]; then
          echo "WARNING : LSUSER : UID ${home} owner it's not ${USR} and it's being used as home directory by it"
        fi
      else
        echo "WARNING : LSUSER : UID ${home} is defined as home of ${USR} but do not exist"
      fi
    done
  ) < ${OUTDIR}/lsuser_ALL 2>> ${OUTDIR}/user_security_info >> ${OUTDIR}/user_security_info
}


# GET DISK INFORMATION
get_diskinfo()
{
  mkdir ${OUTDIR}/diskinfo
  lsdev -Cc disk > ${OUTDIR}/diskinfo/lsdev_disk
  if [ "${GETPERF}" = "Y" ]; then
    C=$((COLL_SEC/2))
    ( iostat -s 5 ${C}     > ${OUTDIR}/diskinfo/iostat_s    ) &
    export CHIELDS="${CHIELDS} ${!}"
    ( iostat -sf 5 ${C}    > ${OUTDIR}/diskinfo/iostat_sf   ) &
    export CHIELDS="${CHIELDS} ${!}"
    ( 
      iostat -sfm        > ${OUTDIR}/diskinfo/iostat_sfm
      my_iostat_sfm_parse ${OUTDIR}/diskinfo/iostat_sfm BOOT
      iostat -sfm 5 ${C} > ${OUTDIR}/diskinfo/iostat_sfm_5_${C}
      my_iostat_sfm_parse ${OUTDIR}/diskinfo/iostat_sfm_5_${C} CURR
    ) &
    export CHIELDS="${CHIELDS} ${!}"
    ( 
      iostat -DRTl > ${OUTDIR}/diskinfo/iostat_DRTl 2>> ${OUTDIR}/diskinfo/iostat_DRTl
      iostat -DRTl 5 ${C}  >  ${OUTDIR}/diskinfo/iostat_DRTl_5_${C} 
    ) &
    export CHIELDS="${CHIELDS} ${!}"
    ( iostat -A 5 ${C}     > ${OUTDIR}/diskinfo/iostat_A    ) &
    export CHIELDS="${CHIELDS} ${!}"
    ( iostat -aTDlRl 5 ${C} > ${OUTDIR}/diskinfo/iostat_aTDlR ) &
    export CHIELDS="${CHIELDS} ${!}"
  fi
  lspath -F"name connection parent path_status status path_id connwhere"  > ${OUTDIR}/diskinfo/lspath
  lsmpio > ${OUTDIR}/diskinfo/lsmpio 2>> ${OUTDIR}/diskinfo/lsmpio
  lsmpio -a > ${OUTDIR}/diskinfo/lsmpio_a 2>> ${OUTDIR}/diskinfo/lsmpio_a
  lsmpio -q > ${OUTDIR}/diskinfo/lsmpio_q 2>> ${OUTDIR}/diskinfo/lsmpio_q
  lsmpio -S -d > ${OUTDIR}/diskinfo/lsmpio_S_d 2>> ${OUTDIR}/diskinfo/lsmpio_S_d
  awk '{ if ( $1 !~ /name|^$/ ) print $1 ; }' < ${OUTDIR}/diskinfo/lsmpio | sort -u | while read A B
  do
    lsmpio -l ${A} -q 2>> ${OUTDIR}/diskinfo/lsmpio_disk_info | cut -d':' -f2- | xargs >> ${OUTDIR}/diskinfo/lsmpio_disk_info
  done

  for D in $(awk '{ print $1; }' < ${OUTDIR}/diskinfo/lspath | sort -u)
  do
    awk -v DSK=${D} -v SFILE="${OUTDIR}/diskinfo/spof_disks" -v TPFILE="${OUTDIR}/diskinfo/disk_paths"  \
      '{
         if (( $1 == DSK )&&( $5 == "Enabled" ))
         {
           P[$3]++;
           TPATH++;
         }
       } END {
         TADAPTER=0;
         for ( i in P )
         { 
           TADAPTER++;
         };
         PLIST=TPATH%2;
         TLIST=TADAPTER%2;
         if (( TPATH == 1)||( PLIST != 0 )||( TADAPTER == 1 )||( TLIST != 0 ))
         {
           print DSK >> SFILE;
         }
         print DSK,TADAPTER,TPATH >> TPFILE
       }' < ${OUTDIR}/diskinfo/lspath
  done

  # spof checks

  awk '{ print $1; }' < ${OUTDIR}/diskinfo/lspath | sort -u | awk -v OD="${OUTDIR}" '
    {
      if ( $1 )
      {
        DSK = $1;
        F = OD"/diskinfo/lspath";
        path = 0;
        while (( getline line < F ) > 0 )
        {
          split(line, L, " ");
          if ( L[1] == DSK )
            path=path+1;
        }
        close(F);
        if ( path < 2 )
          print DSK;

      }
    }'

  for DSK in $(awk '{ print $1; }' < ${OUTDIR}/diskinfo/lsdev_disk)
  do
    /usr/bin/odmget -q name="${DSK}" CuAt 2>&1 | grep -p unique_id | grep value | cut -d'=' -f2- > ${OUTDIR}/diskinfo/CuAt-${DSK}-unique_id

    if [ "${KDB_OK}" = "Y" ]; then
      for V in $(lsattr -Rl ${DSK} -a max_transfer 2>/dev/null) $( lsattr -Rl ${DSK} -a max_coalesce 2>/dev/null)
      do
        echo "hcal ${V}" | kdb 2>&1 | grep Value >>  ${OUTDIR}/dev_attr/${DSK}.hvals
      done
    fi

    if [ -z "$(echo ${DSK} | egrep 'vpath|hdiskpower|hdlm')" ]; then
      # check for spof disks
      awk -v D="${DSK}" -v SPF="${OUTDIR}/diskinfo/spof_disks" '{ if ( $2 == D ) path=path+1 ; } END { if ( path < 2 ) print D >> SPF; }' < ${OUTDIR}/diskinfo/lspath
      lscfg -vpl ${DSK}  2>&1 | awk -v DSK="${DSK}" '{ if ( $0 ~ /Serial Number/ ) { gsub(/Serial|Number|\.|\ /, "", $0); print DSK";"$0; }}' >> ${OUTDIR}/diskinfo/disk_serial
    fi
  done
  # NPIV SPOF check
  if [ -n "$(awk '{ if (( $0 ~ /Virtual Fibre/ )&&( $1 ~ /^fcs/ )) { print "OI"; }}' < ${OUTDIR}/lsdev)" ]; then
    touch ${OUTDIR}/diskinfo/fcs.blacklist
    if [ "${KDB_OK}" = "Y" ]; then
      echo 'vfcs' | kdb 2> ${OUTDIR}/diskinfo/kdb_vfcs > ${OUTDIR}/diskinfo/kdb_vfcs

      if [ "$(awk '{ if ( $1 ~ /^fcs/ ) { gsub(/vfchost/, " ", $4); print $4; }}' < ${OUTDIR}/diskinfo/kdb_vfcs | cut -d' ' -f1 | sort -u | wc -l  | awk '{ print $1; }')" -lt 2 ]; then
        echo "WARNING : NPIV : Possible SPOF on VFC adapter setup, check slot mapping"
      fi
      awk -v DSTBL="${OUTDIR}/diskinfo/fcs.blacklist" '{ if (( $1 ~ /^fcs/ )&&(( $6 == "0x00" )|| ( $4 == "0x00")))
             {
               print "ERROR : NPIV : The NPIV client adapter "$1" is not connected at the VIOS side";
               print "INFO : NPIV : fcstat will not be collected for adapter "$1" due lack of backing device";
               print $1 >> DSTBL;
             }
           }' < ${OUTDIR}/diskinfo/kdb_vfcs
    fi
  fi

  # Check FCS parameters
  for FC in $(awk '{ if ( $3 ~ /fscsi/ )  { print $3; }}' < ${OUTDIR}/diskinfo/lspath | sort -u)
  do
    # FCstat stuff
    export LOC=`awk -v F=${FC} '{ if ( $1 == F ) print $2; }' < ${OUTDIR}/lscfg_vp`
    (
      F1="$(awk -v F="${LOC}" '{ if (( $1 ~ /fcs/ )&&( $2 == F )) print $1; }' < ${OUTDIR}/lscfg_vp)"
      if [ -f "${OUTDIR}/diskinfo/fcs.blacklist" ]; then
        if [ -z "$(awk -v F="${F1}" '{ if ( $1 == F ) print "OI"; }' < ${OUTDIR}/diskinfo/fcs.blacklist)" ]; then
          my_fcstat ${F1}

          if [ "${KDB_OK}" = "Y" ]; then
            for V in $(lsattr -Rl ${F1} -a lg_term_dma 2>/dev/null) $( lsattr -Rl ${F1} -a max_xfer_size 2>/dev/null)
            do
              echo "hcal ${V}" | kdb 2>&1 | grep Value >>  ${OUTDIR}/dev_attr/${FC}.hvals 
            done
          fi
        fi
      fi
    ) &
    export CHIELDS="${CHIELDS} ${!}"
  done


  # Check VSCSI parameters
  if [ -n "$(grep vscsi ${OUTDIR}/lsdev)" ]; then
    if [ -z "$(grep 5300 ${OUTDIR}/oslevel_s )" ]; then
      if [ "${KDB_OK}" = "Y" ]; then
        echo 'cvai' | kdb 2>${OUTDIR}/diskinfo/kdb_cvai >> ${OUTDIR}/diskinfo/kdb_cvai 
        if [ $(awk '{ if ( $1 ~ /vscsi/ ) { print $5; }}' < ${OUTDIR}/diskinfo/kdb_cvai | cut -d'->' -f1 | uniq -c | wc -l | awk '{ print $1; }') -lt 2 ]; then
          echo "WARNING : VSCSI : Possible SPOF on VSCSI adapter setup, check slot mapping"
        fi
      fi
    fi
  fi
 
  # Old datapath stuff
  check_exist_bin datapath
  if [ ${?} -eq 0 ]; then
    if [ -z "$(datapath query version | grep SDDPCM)" ]; then
            print "ERROR : LSVG : The Logical Volume "$1" on Volume Group "VG" is exposed to SPOF";
      if [ -n "$(awk '{ if ( $0 ~ /VeritasVolumes/ ) { print "NOK"; }}' < ${OUTDIR}/lvminfo/lspv)" ]; then
        echo "WARNING : DATAPATH shouldn't be used with VXVM, try to use DMP instead"
      fi
      datapath query adapter > ${OUTDIR}/diskinfo/datapath_query_adapter
      datapath query device  > ${OUTDIR}/diskinfo/datapath_query_device
      datapath query essmap  > ${OUTDIR}/diskinfo/datapath_query_essmap
      lsvpcfg                > ${OUTDIR}/diskinfo/lsvpcfg 2> ${OUTDIR}/diskinfo/lsvpcfg
      echo "INFO : DATAPATH : Datapath should be migrated to SDDPCM"
    fi
  fi
  # SDDPCM stuff
  check_exist_bin pcmpath 
  if [ ${?} -eq 0 ]; then
    if [ -n "$(awk '{ if ( $0 ~ /VeritasVolumes/ ) { print "NOK"; }}' < ${OUTDIR}/lvminfo/lspv)" ]; then
      echo "WARNING : SDDPCM shouldn't be used with VXVM, try to use DMP instead"
    fi
    pcmpath query device     > ${OUTDIR}/diskinfo/pcmpath_query_device
    pcmpath query wwpn       > ${OUTDIR}/diskinfo/pcmpath_query_wwpn
    pcmpath query adapter    > ${OUTDIR}/diskinfo/pcmpath_query_adapter
    pcmpath query devstats   > ${OUTDIR}/diskinfo/pcmpath_query_devstats 2>> ${OUTDIR}/diskinfo/pcmpath_query_devstats
    pcmpath query adaptstats > ${OUTDIR}/diskinfo/pcmpath_query_adaptstats 2>> ${OUTDIR}/diskinfo/pcmpath_query_adaptstats
    if [ ${?} -eq 0 ]; then
      awk \
      '{
         if ( $0 ~ /^Total Dual Active/ )
         {
           TOT_ADPT=$8;
         } else if ( $1 == "I/O:" )
         {
           cmd_elements_tot=cmd_elements_tot+$6;
         }
      } END {
        TOT_AVG=cmd_elements_tot/TOT_ADPT;
        print "INFO : PCMPATH : Estimated required num_cmd_elems on the fc adapters used under sddpcm: "TOT_AVG;
      }' < ${OUTDIR}/diskinfo/pcmpath_query_adaptstats
    fi
  fi
  # POWERMT stuff
  check_exist_bin powermt
  if [ ${?} -eq 0 ]; then
    powermt display         > ${OUTDIR}/diskinfo/powermt_display
    powermt display dev=all > ${OUTDIR}/diskinfo/powermt_display_dev_all
  fi
  # NetApp stuff
  check_exist_bin sanlun
  if [ ${?} -eq 0 ]; then
    if [ -n "$(awk '{ if ( $0 ~ /VeritasVolumes/ ) { print "NOK"; }}' < ${OUTDIR}/lvminfo/lspv)" ]; then
      echo "WARNING : SANLUN shouldn't be used with VXVM, try to use DMP instead"
    fi
    sanlun lun show -v all         > ${OUTDIR}/diskinfo/sanlun_lun_show_v_all
    sanlun lun show -p all         > ${OUTDIR}/diskinfo/sanlun_lun_show_p_all
    sanlun fcp show adapter -v all > ${OUTDIR}/diskinfo/sanlun_fcp_show_adapter_v_all
    # SPOF stuff
    for DSK in $(awk '{ if ( $3 ~ /hdisk/ ) { print $3; }}' < ${OUTDIR}/diskinfo/sanlun_lun_show_v_all)
    do
      TO="`grep \"${DSK} \" ${OUTDIR}/diskinfo/lspath | wc -l | awk '{ print $1; }'`"
      if [ ${TO} -lt 2 ]; then
        echo "${DSK}" >> ${OUTDIR}/diskinfo/spof_disks
      fi
    done
  fi
  # Hitachi stuff
  check_exist_bin dlnkmgr
  if [ ${?} -eq 0 ]; then
    dlnkmgr view -path > ${OUTDIR}/diskinfo/dlnkmgr_view_path
  fi

  # Check for SCSI RAID volumes
  check_exist_bin sisraidmgr
  if [ "${?}" -eq 0 ]; then
    for DSK in $(awk '{ if ( $5 == "RAID" ) { print $1; }}' < ${OUTDIR}/diskinfo/lsdev_disk)
    do
      sisraidmgr -L -l ${DSK} >> ${OUTDIR}/diskinfo/sisraidmgr
      awk '{ if ( $4 == "RAID" ) { if (( $3 != "Optimal" )&&( $3 != "Active" )) { print "ERROR : SISRAIDMGR : The RAID volume "$1" is on "$3" State"; exit 1  } } }' < ${OUTDIR}/diskinfo/sisraidmgr
      if [ ${?} -ne 0 ]; then
        echo "${DSK}" >> ${OUTDIR}/diskinfo/spof_disks
      fi
    done
  fi
}

# GET LVM INFORMATION
get_lvminfo()
{
  mkdir ${OUTDIR}/lvminfo
  # Standard lsvg info
  lsvg     > ${OUTDIR}/lvminfo/lsvg
  lspv     > ${OUTDIR}/lvminfo/lspv
  lsvg -o  > ${OUTDIR}/lvminfo/lsvg_o
  lsvg -i  < ${OUTDIR}/lvminfo/lsvg_o > ${OUTDIR}/lvminfo/lsvg_i
  lsvg -il < ${OUTDIR}/lvminfo/lsvg_o > ${OUTDIR}/lvminfo/lsvg_il
  lsvg -im < ${OUTDIR}/lvminfo/lsvg_o > ${OUTDIR}/lvminfo/lsvg_im
  lsvg -ip < ${OUTDIR}/lvminfo/lsvg_o > ${OUTDIR}/lvminfo/lsvg_ip

  for VG in $(cat ${OUTDIR}/lvminfo/lsvg_o)
  do
    for LV in $(lsvg -l $VG | awk '{ if ( ! system("test -e /dev/"$1) ) { print $1; }}')
    do  
      lslv    ${LV} >> ${OUTDIR}/lvminfo/${VG}_${LV}   2>> ${OUTDIR}/lvminfo/${VG}_${LV}
      lslv -l ${LV} >> ${OUTDIR}/lvminfo/${VG}_${LV}_l 2>> ${OUTDIR}/lvminfo/${VG}_${LV}_l
      lslv -m ${LV} >> ${OUTDIR}/lvminfo/${VG}_${LV}_m 2>> ${OUTDIR}/lvminfo/${VG}_${LV}_m
    done
    lvmo -v ${VG} -a  > ${OUTDIR}/lvminfo/lvmo_v_${VG}_a  2>> ${OUTDIR}/lvminfo/lvmo_v_${VG}_a
    awk -v VG="${VG}" '{ if ( $1 ~ /pervg_blocked_io_count|global_blocked_io_count/ ) { if ( $3 > 0 ) { print "WARNING : LVMO : "VG" has blocked IO, please check pv_pbuf_count under lvmo"; }}}' < ${OUTDIR}/lvminfo/lvmo_v_${VG}_a
  done
  if [ -e /proc/sys/fs/jfs2/memory_usage ]; then
    cat /proc/sys/fs/jfs2/memory_usage > ${OUTDIR}/lvminfo/jfs2_memory_usage 2>> ${OUTDIR}/lvminfo/jfs2_memory_usage
  fi
  # Check for stale stuff
  awk '{ if ( $1 == "STALE" ) { if ( $3 ne 0 ) { print "ERROR : Stale PVs found"; } ; if ( $6 ne 0 ) { print "ERROR : LSVG : Stale LVs found"; } } }' < ${OUTDIR}/lvminfo/lsvg_i
  # Load disk information
  # Check for SPOF LVs
  if [ -f "${OUTDIR}/diskinfo/spof_disks" ]; then
    for VG in $(sort -u ${OUTDIR}/diskinfo/spof_disks |awk -v OD="${OUTDIR}" '{ FO=OD"/lvminfo/lspv"; while (( getline line < FO ) > 0 ) { split(line, L, " "); if ( L[4] == "active" ) print L[3]; }}' | sort -u)
    do
      awk -v VG="${VG}" '
      {
        VNAME=VG":"
        if ( ! $2 )
        {
          if ( $1 == VNAME )
            bg = 1 ;
          else if (( $1 ~ /:$/ )&&( bg == 1 ))
            ed = 1;
        } else if (( bg == 1 )&&( ed != 1 ))
          if (( $6 ~ /open/ )&&( $2 != "sysdump" )&&( $3 == $4 ))
            print "ERROR : LSVG : The Logical Volume "$1" on Volume Group "VG" is exposed to SPOF";
      }' < ${OUTDIR}/lvminfo/lsvg_il
    done
  fi
}

get_gpfsinfo()
{
  # GPFS stuff
  if [ -d "/usr/lpp/mmfs/bin" ]; then
    mkdir ${OUTDIR}/fsinfo/gpfs
    (
      for FS in $(egrep 'mmfs|gpfs' ${OUTDIR}/fsinfo/mount | awk '{ print "mmlsfs "$1" -d"; }' | sh  | grep Disk | awk '{ print $2; }' | sed 's/;/ /g')
      do
        if [ -z "`mmlsnsd -md ${FS} | grep $(hostname)`" ]; then
          echo ${FS} 
        fi
      done
    ) > ${OUTDIR}/fsinfo/gpfs/nsd_based_fs
    mmlscluster      > ${OUTDIR}/fsinfo/gpfs/mmlscluster
    mmlsnsd -am      > ${OUTDIR}/fsinfo/gpfs/mmlsnsd_am
    mmlsconfig       > ${OUTDIR}/fsinfo/gpfs/mmlsconfig
    mmlsmgr          > ${OUTDIR}/fsinfo/gpfs/mmlsmgr
    mmlsfs all       > ${OUTDIR}/fsinfo/gpfs/mmlsfs_all
    mmfsadm dump version >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_version 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_version
    mmfsadm dump waiters >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_waiters 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_waiters
    mmfsadm dump quorumState >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_quorumState 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_quorumState
    mmfsadm dump thread all >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_thread_all 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_thread_all
    mmfsadm dump threadstacks >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_threadstacks 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_threadstacks
    mmfsadm dump threadstats >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_threadstats 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_threadstats
    mmfsadm dump mutex >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_mutex 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_mutex
    mmfsadm dump condvar >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_condvar 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_condvar
    mmfsadm dump asyncevents >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_asyncevents 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_asyncevents
    mmfsadm dump config >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_config 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_config
    mmfsadm dump tscomm >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_tscomm 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_tscomm
    mmfsadm dump verbs >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_verbs 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_verbs
    mmfsadm dump cfgmgr >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_cfgmgr 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_cfgmgr
    mmfsadm dump fsmgr >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_fsmgr 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_fsmgr
    mmfsadm dump stripe >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_stripe 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_stripe
    mmfsadm dump disk >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_disk 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_disk
    mmfsadm dump nsd >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_nsd 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_nsd
    mmfsadm dump nsdcksum >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_nsdcksum 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_nsdcksum
    mmfsadm dump nsdrg >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_nsdrg 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_nsdrg
    mmfsadm dump odb >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_odb 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_odb
    mmfsadm dump fsck >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_fsck 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_fsck
    # Checar manualmente
    mmfsadm dump iocounters >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_iocounters 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_iocounters
    #
    mmfsadm dump malloc >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_malloc 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_malloc
    # Borrowed from https://www.ibm.com/developerworks/community/wikis/home?lang=en#!/wiki/General+Parallel+File+System+(GPFS)/page/Collect+and+process+GPFS+cluster+statistics
    #egrep -A 4 "^Statistics|^Delta" ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_malloc |\
    #  awk 'BEGIN {  RS="--" }
    #  { \
    #    if ( $1 == "Delta") { printf "INFO : GPFS : Heap %s %s ,",$4,$5; }
    #    if ( $1 == "Statistics" ) { 
    #      if ( $5 == "2" ) { 
    #        printf "SharedSeg: %s %s %s %s %s %s %s %3.2f%% in use ",$9,$10,$11,$12,$24,$25,$26,(($9/$24)*100);
    #      }
    #      if (  $5== "3" ) { 
    #        printf "TokenSeg: %s %s %s %s %s %s %s %3.2f%% in use\n",$9,$10,$11,$12,$24,$25,$26,(($9/$24)*100)
    #      }
    #    }
    #  }'
    ##
    mmfsadm dump vfsstats >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_vfsstats 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_vfsstats
    mmfsadm dump mb >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_mb 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_mb
    grep Worker1  ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_mb | awk '{ print "INFO : GPFS : "$0; }'
    mmfsadm dump res >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_res 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_res
    mmfsadm dump sxlock >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_sxlock 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_sxlock
    mmfsadm dump rwxlock >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_rwxlock 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_rwxlock
    mmfsadm dump brt >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_brt 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_brt
    mmfsadm dump reclock >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_reclock 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_reclock
    mmfsadm dump fs >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_fs 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_fs
    egrep ' name |estF'  ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_fs | awk '{ print "INFO : GPFS : "$0; }'
    egrep "nPrefetchThreads:|total wait" ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_fs | awk '{ print "INFO : GPFS : "$0; }'

    mmfsadm dump afm >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_afm 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_afm
    mmfsadm dump mmap >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_mmap 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_mmap
    mmfsadm dump log >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_log 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_log
    mmfsadm dump quota >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_quota 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_quota
    mmfsadm dump DACspy >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_DACspy 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_DACspy
    mmfsadm dump events exporter >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_events_exporter 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_events_exporter
    mmfsadm dump dmapi >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_dmapi 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_dmapi
    mmfsadm dump lwe >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_lwe 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_lwe
    mmfsadm dump sanergy >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_sanergy 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_sanergy
    mmfsadm dump instances >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_instances 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_instances
    mmfsadm dump compact files >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_compact_files 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_compact_files
    mmfsadm dump updatelogger >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_updatelogger 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_updatelogger
    mmfsadm dump alloc >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_alloc 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_alloc
    mmfsadm dump dealloc >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_dealloc 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_dealloc
    mmfsadm dump ialloc >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_ialloc 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_ialloc
    mmfsadm dump iallocmgr >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_iallocmgr 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_iallocmgr
    mmfsadm dump tmstats >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_tmstats 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_tmstats
    mmfsadm dump tokenmgr >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_tokenmgr 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_tokenmgr
    mmfsadm dump allocmgr >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_allocmgr 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_allocmgr
    mmfsadm dump pit >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_pit 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_pit
    mmfsadm dump filesets >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_filesets 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_filesets
    mmfsadm dump winsec >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_winsec 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_winsec
    mmfsadm dump lstat >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_lstat 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_lstat
    mmfsadm dump indirect blocks >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_indirect_blocks 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_indirect_blocks
    mmfsadm dump llfile >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_llfile 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_llfile
    mmfsadm dump iohist >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_iohist 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_iohist
    mmfsadm dump pdisk >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_pdisk 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_pdisk
    mmfsadm dump pdiskdevs >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_pdiskdevs 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_pdiskdevs
    mmfsadm dump nspdclient >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_nspdclient 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_nspdclient
    mmfsadm dump nspdserver >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_nspdserver 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_nspdserver
    mmfsadm dump vdisk >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_vdisk 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_vdisk
    mmfsadm dump vtracks >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_vtracks 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_vtracks
    mmfsadm dump recoverygroupevents >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_recoverygroupevents 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_recoverygroupevents
    mmfsadm dump vdiskbufs >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_vdiskbufs 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_vdiskbufs
    mmfsadm dump encrypt >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_encrypt 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_encrypt
    mmfsadm dump complete >> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_complete 2>> ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_complete
    mmlsnode -a      > ${OUTDIR}/fsinfo/gpfs/mmlsnode_a 2>> ${OUTDIR}/fsinfo/gpfs/mmlsnode_a
    tsstatus         > ${OUTDIR}/fsinfo/gpfs/tsstatus 2>> ${OUTDIR}/fsinfo/gpfs/tsstatus
    mmlsnsd -L       > ${OUTDIR}/fsinfo/gpfs/mmlsnsd_L 2>> ${OUTDIR}/fsinfo/gpfs/mmlsnsd_L
    mmlsnsd -X       > ${OUTDIR}/fsinfo/gpfs/mmlsnsd_X 2>> ${OUTDIR}/fsinfo/gpfs/mmlsnsd_X
    mmremotecluster show all > ${OUTDIR}/fsinfo/gpfs/mmremotecluster_show_all 2>> ${OUTDIR}/fsinfo/gpfs/mmremotecluster_show_all
    mmremotefs show all > ${OUTDIR}/fsinfo/gpfs/mmremotefs_show_all 2>> ${OUTDIR}/fsinfo/gpfs/mmremotefs_show_all
    mmauth show > ${OUTDIR}/fsinfo/gpfs/mmauth_show 2>> ${OUTDIR}/fsinfo/gpfs/mmauth_show
    mmlscallback > ${OUTDIR}/fsinfo/gpfs/mmlscallback 2>> ${OUTDIR}/fsinfo/gpfs/mmlscallback
    mmgetstate > ${OUTDIR}/fsinfo/gpfs/mmgetestate 2>> ${OUTDIR}/fsinfo/gpfs/mmgetestate
    for FS in $( awk '{ if ( $1 ~ /\/dev\// ) { print $1; }}' < ${OUTDIR}/fsinfo/gpfs/mmlsconfig )
    do
      mmdefragfs ${FS} -i >> ${OUTDIR}/fsinfo/gpfs/mmdefragfs_$(echo ${FS} | sed 's/\//_/g') 2>> ${OUTDIR}/fsinfo/gpfs/mmdefragfs_$(echo ${FS} | sed 's/\//_/g')
      mmdf ${FS} >> ${OUTDIR}/fsinfo/gpfs/mmdf_$(echo ${FS} | sed 's/\//_/g') 2>> ${OUTDIR}/fsinfo/gpfs/mmdf_$(echo ${FS} | sed 's/\//_/g')
    done

    awk '{
      if (( $1 == "-B" )&&( $2 < 131072 ))
      {
        SB=$2/32;
        print "WARNING : MMLSFS : GPFS with block size smaller than 128k, subblock = "SB" bytes";
      } else if (( $1 == "-j" )&&( $2 == "cluster" ))
      {
        print "WARNING : MMLSFS : GPFS with cluster allocation policy is set, double check fragmentation status";
      }
    }' < ${OUTDIR}/fsinfo/gpfs/mmlsfs_all  | sort -u

    # Still testing
    cat ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_config ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_cfgmgr | awk \
    '{
       if (( $8 == "up" )&&( $2 ~ /</ ))
       {
         if ( $5 ~ /m/ )
         {
           mgm=mgm+1;
         }
         node=node+1;
       } else if ( $2 == "maxFilesToCache" ) {
         MFTC = $3;
       } else if ( $2 == "maxStatCache" ) {
         MSC = $3;
       } else if ( $2 == "pagepool" ) {
         PGP = $3;
       } else if ( $2 == "pagepoolMaxPhysMemPct" ) {
         PGPP = $3;
       } else if ( $2 == "statCacheDirPct" ) {
         SCDP = $3;
       } else if ( $1 == "tokenMemLimit" ) {
         TKM = $2;
       } else if ( $0 ~ /idleSocketTimeout|failureDetectionTime|maxReceiverThreads|minMissedPingTimeout|tscWorkerPool|maxReceiverThreads|maxGeneralThreads|prefetchThreads|worker1Threads|worker3Threads/ ) {
         print "INFO : MMFSADM : "$0;
       }
     } END {
       MFTCS=MFTC*3/1024;
       MSCS=(MSC*400)/1024/1024;
       EXPMEM=((mgm-1)*600000*(TKM/256));
       EXPREQ=(node*(MFTC+MSC));
       TKMS=TKM/1024/1024;
       TC=(MFTC*4)-MSC;
       if ( TC != 0 )
       {
         if ( TC > 0 ) {
           print "WARNING : MMFSADM : GPFS maxFilesToCache is bigger than 4 * maxStatCache";
         } else {
           print "WARNING : MMFSADM : GPFS maxFilesToCache is smaller than 4 * maxStatCache";
         }
       }
       print "INFO : MMFSADM : GPFS Required Memory: "EXPREQ;
       print "INFO : MMFSADM : GPFS Used Memory: "EXPMEM;
       print "INFO : MMFSADM : GPFS Max files to cache size: "MFTCS;
       print "INFO : MMFSADM : GPFS Max Stat Cache size: "MSCS;
       print "INFO : MMFSADM : GPFS Token memory: "TKMS;
     }'
     for WRD in $(awk '{ if ( $3 !~ /---|\n/ ) { print $3; }}' < ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_iohist | sort -u) 
     do
       echo "INFO : MMFSADM : GPFS IO COUNT HIST : ${WRD} $(grep -c ${WRD} ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_iohist)"
     done 
     grep -p 'Thread pool utilization' ${OUTDIR}/fsinfo/gpfs/mmfsadm_dump_thread_all | awk '{ print "INFO : MMFSADM : GPFS "$0; }' 
# idleSocketTimeout=0
#GPFS: failureDetectionTime=60
#GPFS: minMissedPingTimeout=60
#GPFS: tscWorkerPool=128
#GPFS: maxReceiverThreads=nump
#         (#MGRS-1)*600000*(#TOKENMEM/256*1024) >= #MEMBERS * (MFTC + MSC)

    for IDS in $(cat ${OUTDIR}/process/running_users)
    do
      mmdsh -N all "lsuser -a account_locked unsuccessful_login_count loginretries maxage lastupdate groups capabilities id ${IDS}" >> ${OUTDIR}/fsinfo/gpfs/account_info 2>> ${OUTDIR}/fsinfo/gpfs/account_info
    done

    if [ "${GETPERF}" = "Y" ]; then
      # Collect mmpmon
      echo "INFO : Get mmpmon data ( will take around 2 minutes )"
      echo fs_io_s > ${OUTDIR}/fsinfo/gpfs/mmpmon_in
      echo io_s > ${OUTDIR}/fsinfo/gpfs/mmpmon_in
      mmpmon -d 1000 -i ${OUTDIR}/fsinfo/gpfs/mmpmon_in  -r ${COLL_SEC}  -p > ${OUTDIR}/fsinfo/gpfs/mmpmon_out 2>> ${OUTDIR}/fsinfo/gpfs/mmpmon_out

      echo "INFO : GPFS - Get Average filesize ( will be stat intensive )"
      TOT=0
      FCOUNT=0
      echo "directory;ls size;istat size;number of objects" > ${OUTDIR}/fsinfo/gpfs/mmfs.dirsize_info
      find $(mmlsfs all -T | awk '{ if ( $1 == "-T" ) { print $2; }}' | xargs) -xdev | while read D
      do
        S1="$(ls -ld ${D} 2>/dev/null | awk '{ split($5, T, "," ); print T[1]; }')"
        if [ -n "${S1}" ]; then
          if [ -d "${D}" ]; then
            S2="$(istat ${D} 2>/dev/null | awk '{ if ( $0 ~ /Length/  ) { print $5; }}')"
            if [ -n "${S3}" ]; then
              echo "${D} ${S1};${S2};$(find ${D} -xdev -print 2>/dev/null | awk '{ x=x+1; } END { print x; }')" >> ${OUTDIR}/fsinfo/gpfs/mmfs.dirsize_info
            fi
          else
            TOT=$((TOT+S1))
            FCOUNT=$((FCOUNT+1))
          fi
        fi
      done
#for i in  $(find /usr/local/boinc/data -ignore_readdir_race -type d -print)
#do
#  LSS=$(ls ${i} | wc -c) 
#  LSSF=$((LSS*5)) 
#  STAT=$(stat -c %s ${i}) 
#  if [ "${LSS}" -le "${STAT}" ]; then
#    echo $i 
#  fi
#done
      AVGFS=$((TOT/FCOUNT))
      echo "INFO : GPFS : Average file size ${AVGFS}" | tee -a ${OUTDIR}/fsinfo/gpfs/avg_size
    fi
  fi
}

get_fsinfo()
{
  mkdir ${OUTDIR}/fsinfo
  mount > ${OUTDIR}/fsinfo/mount
  lsfs -a > ${OUTDIR}/fsinfo/lsfs_a
  lsfs -qa > ${OUTDIR}/fsinfo/lsfs_qa
  df -k > ${OUTDIR}/fsinfo/df_k
  df -kI > ${OUTDIR}/fsinfo/df_ki
  ioo -L > ${OUTDIR}/fsinfo/ioo_L 2>> ${OUTDIR}/fsinfo/ioo_L
  ioo -aF > ${OUTDIR}/fsinfo/ioo_aF 2>> ${OUTDIR}/fsinfo/ioo_aF
  if [ -n "$(grep '1485-123 Error' ${OUTDIR}/fsinfo/ioo_L)" ]; then
    echo "ERROR : Unable to retrieve all ioo system calls, possible kernel corruption"
  fi

  exportfs > ${OUTDIR}/fsinfo/exportfs
  if [ -f /etc/exports ]; then
    awk '{ if ( $1 ~ /^\// ) { if ( $2 ~ /access/ ) { print $1" NGB"; } else { print $1" GB"; }}}' < /etc/exports | while read D GB
    do
      if [ ! -d "${D}" ]; then
        echo "WARNING : EXPORTFS : ${D} do not exist, the server may go into a hang during the reboot"
      else
        if [ "${GB}" != "NGB" ]; then
          echo "WARNING : EXPORTFS : Anyone can connect to the nfs share ${D}, be careful"
        fi 
      fi
    done
    echo "INFO : SHOWMOUNT : NFS SHARES MOUNTED ON REMOTE HOSTS :"
    showmount -a 2>> ${OUTDIR}/fsinfo/showmount | tee -a ${OUTDIR}/fsinfo/showmount | awk '{ print "INFO : SHOWMOUNT : "$0; }' 
    echo "-----------------------------------------------------------------"
  fi
  # NFS stuff
  for i in p m s
  do
    rpcinfo -${i} > ${OUTDIR}/fsinfo/rpcinfo_$i 2>> ${OUTDIR}/fsinfo/rpcinfo_$i
  done
  for i in c b d g m n r s t 4 z
  do
    nfsstat > ${OUTDIR}/fsinfo/nfsstat_$i 2>> ${OUTDIR}/fsinfo/nfsstat_$i
  done

  # LSOF stuff
  check_exist_bin lsof
  if [ ${?} -eq 0 ]; then
    lsof -a -L -M -n -S 30 -U -X >> ${OUTDIR}/fsinfo/lsof 2>> ${OUTDIR}/fsinfo/lsof
  fi

  # Veritas Stuff
  check_exist_bin vxassist
  if [ ${?} -eq 0 ]; then
    mkdir -p ${OUTDIR}/vxsf
    echo "INFO : This system appear to have Veritas Storage Fundations installed, double check Disk Subsystem "
    lmxconfig -V > ${OUTDIR}/vxsf/lmxconfig_V 2>> ${OUTDIR}/vxsf/lmxconfig_V
    vxaslkey     > ${OUTDIR}/vxsf/vxaslkey 2>> ${OUTDIR}/vxsf/vxaslkey
    vxdg list  >> ${OUTDIR}/vxsf/vxdg_list 2>> ${OUTDIR}/vxsf/vxdg_list
    for i in $(awk '{ if ( $1 !~ /NAME/ ) print $1; }' < ${OUTDIR}/vxsf/vxdg_list)
    do
      vxdg list ${i}      >> ${OUTDIR}/vxsf/vxdg_list_${i} 2>> ${OUTDIR}/vxsf/vxdg_list_${i}
      vxprint -g ${i} -Pl >> ${OUTDIR}/vxsf/vxprint_g_${i}_Pl 2>> ${OUTDIR}/vxsf/vxprint_g_${i}_Pl
      vxstat -g ${i} -d   >> ${OUTDIR}/vxsf/vxstat_g_${i}_d 2>> ${OUTDIR}/vxsf/vxstat_g_${i}_d
    done
    vxdisk list >> ${OUTDIR}/vxsf/vxdisk_list 2>> ${OUTDIR}/vxsf/vxdisk_list
    for i in $(awk '{ if ( $1 !~ /DEVICE/ ) print $1; }' < ${OUTDIR}/vxsf/vxdisk_list)
    do
      vxdisk list ${i} >> ${OUTDIR}/vxsf/vxdisk_list_${i} 2>> ${OUTDIR}/vxsf/vxdisk_list_${i}
      awk -v DNAME=${i} \
        '{
           if ( $1 == "numpaths:" )
             s_paths=1 ;
           if (( s_paths == 1 )&&( $1 != "numpaths:" ))
           {
             if ( $2 != "state=enabled" )
               print "WARNING : VXDISK The disk "DNAME" has a non enabled path at "$1;
           }
         }' < ${OUTDIR}/vxsf/vxdisk_list_${i}
    done
    vxdisk -o alldgs -e list >> ${OUTDIR}/vxsf/vxdisk_o_alldgs_e_list 2>> ${OUTDIR}/vxsf/vxdisk_o_alldgs_e_list
    vxdisk path >> ${OUTDIR}/vxsf/vxdisk_path 2>> ${OUTDIR}/vxsf/vxdisk_path
    if [ ${?} -eq 0 ]; then
      for D in $(awk '{ if ( $2 != "DANAME" ) print $2; }' < ${OUTDIR}/vxsf/vxdisk_path | sort -u) 
      do
        awk -v D=${D} '{ if ( $2 == D ) x=x+1; } END { if ( x < 2 ) print "WARNING : VXDISK : Detected possible SPOF or MPIO conflict at disk "D; }' < ${OUTDIR}/vxsf/vxdisk_path
      done
    fi

    vxtask -l list >> ${OUTDIR}/vxsf/vxtask_l_list 2>> ${OUTDIR}/vxsf/vxtask_l_list
    vxannotate print attribute >> ${OUTDIR}/vxsf/vxannotate_print_attribute 2>> ${OUTDIR}/vxsf/vxannotate_print_attribute

    vxdmpadm listctlr all >> ${OUTDIR}/vxsf/vxdmpadm_listctlr_all 2>> ${OUTDIR}/vxsf/vxdmpadm_listctlr_all
    if [ ${?} -eq 0 ]; then
      awk '{ if ( $1 ~  /^vscsi/ ) print "WARNING : VXDMPADM : The controller "$1" is being controlled by VXDMP and this might lead to conflicts"; }' < ${OUTDIR}/vxsf/vxdmpadm_listctlr_all
    fi

    vxdmpadm listenclosure all >> ${OUTDIR}/vxsf/vxdmpadm_listenclosure_all 2>> ${OUTDIR}/vxsf/vxdmpadm_listenclosure_all
    vxdmpadm listapm all >> ${OUTDIR}/vxsf/vxdmpadm_listapm_all 2>> ${OUTDIR}/vxsf/vxdmpadm_listapm_all
    vxdmpadm getsubpaths  >> ${OUTDIR}/vxsf/vxdmpadm_getsubpaths 2>> ${OUTDIR}/vxsf/vxdmpadm_getsubpaths
    vxdmpadm iostat show all >> ${OUTDIR}/vxsf/vxdmpadm_iostat_show_all 2>> ${OUTDIR}/vxsf/vxdmpadm_iostat_show_all
    vxdmpadm -q -e iostat show all >> ${OUTDIR}/vxsf/vxdmpadm_q_e_iostat_show_all 2>> ${OUTDIR}/vxsf/vxdmpadm_q_e_iostat_show_all
    vxdmpadm -q -e iostat show all groupby=ctlr >> ${OUTDIR}/vxsf/vxdmpadm_q_e_iostat_show_all_groupby_ctlr 2>> ${OUTDIR}/vxsf/vxdmpadm_q_e_iostat_show_all_groupby_ctlr
    vxdmpadm stat restored >> ${OUTDIR}/vxsf/vxdmpadm_stat_restored 2>> ${OUTDIR}/vxsf/vxdmpadm_stat_restored
    vxdmpadm stat errord >> ${OUTDIR}/vxsf/vxdmpadm_stat_errord 2>> ${OUTDIR}/vxsf/vxdmpadm_stat_errord
    vxdmpadm gettune all >> ${OUTDIR}/vxsf/vxdmpadm_gettune_all 2>> ${OUTDIR}/vxsf/vxdmpadm_gettune_all
    qiostat >> ${OUTDIR}/vxsf/qiostat 2>> ${OUTDIR}/vxsf/qiostat
    qiostat -r >> ${OUTDIR}/vxsf/qiostat_r 2>> ${OUTDIR}/vxsf/qiostat_r
    for i in $(awk '{ if ( $0 ~ /vxfs/ ) print $2; }' < ${OUTDIR}/fsinfo/mount)
    do
      vxfsstat -b  ${i} >> ${OUTDIR}/vxsf/vxfsstat_b_${i} 2>> ${OUTDIR}/vxsf/vxfsstat_b_${i}
      vxfsstat -v  ${i} >> ${OUTDIR}/vxsf/vxfsstat_v_${i} 2>> ${OUTDIR}/vxsf/vxfsstat_v_${i}
      vxfsstat -i  ${i} >> ${OUTDIR}/vxsf/vxfsstat_i_${i} 2>> ${OUTDIR}/vxsf/vxfsstat_i_${i}
      vxfsstat -vz ${i} >> ${OUTDIR}/vxsf/vxfsstat_vz_${i} 2>> ${OUTDIR}/vxsf/vxfsstat_vz_${i}
    done
    if [ -e "/etc/vx" ]; then
      tar -cpvf ${OUTDIR}/vxsf/vxfs_config.tar /etc/vx 2>> /dev/null >> /dev/null
    fi

    for i in $(awk '{ if ( $3 == "CONNECTED" ) print $1; }' < ${OUTDIR}/vxsf/vxdmpadm_listenclosure_all)
    do
      vxdmpadm getattr enclosure ${i} iopolicy >> ${OUTDIR}/vxsf/vxdmpadm_getattr_enclosure_${i}_iopolicy 2>> ${OUTDIR}/vxsf/vxdmpadm_getattr_enclosure_${i}_iopolicy
      vxdmpadm getattr enclosure ${i} >> ${OUTDIR}/vxsf/vxdmpadm_getattr_enclosure_${i} 2>> ${OUTDIR}/vxsf/vxdmpadm_getattr_enclosure_${i}
    done


    # VCS Interface config
    check_exist_bin gabconfig
    if [ ${?} -eq 0 ]; then
      gabconfig -a >> ${OUTDIR}/vxsf/gabconfig_a 2>> ${OUTDIR}/vxsf/gabconfig_a
      if [ -f /etc/VRTSvcs/conf/config/main.cf ]; then
        tar -cpf ${OUTDIR}/vxsf/VRTSvcs_conf.tar /etc/VRTSvcs/conf 2>&1 >> /dev/null
      fi
      hacf -verify /etc/VRTSvcs/conf/config >>  ${OUTDIR}/vxsf/hacf_-verify 2>> ${OUTDIR}/vxsf/hacf_-verify
    fi
  fi

}

get_netinfo()
{
  mkdir ${OUTDIR}/netinfo
  check_exist_bin tcptr
  if [ ${?} -eq 0 ]; then
    tcptr -show > ${OUTDIR}/netinfo/tcptr_show 2>> ${OUTDIR}/netinfo/tcptr_show
    awk '{ if ( $0 !~ /No policy defined/ ) print "WARNING : TCPTR : TCP Traffic regulator enabled" }' < ${OUTDIR}/netinfo/tcptr_show
  fi

  lsfilt       > ${OUTDIR}/netinfo/lsfilt 2>> ${OUTDIR}/netinfo/lsfilt
  lsfilt -a    > ${OUTDIR}/netinfo/lsfilt_a 2>> ${OUTDIR}/netinfo/lsfilt_a

  lsattr -El inet0 > ${OUTDIR}/netinfo/inet0
  ifconfig -a  > ${OUTDIR}/netinfo/ifconfig_a
  netstat -aon > ${OUTDIR}/netinfo/netstat_aon
  netstat -ain > ${OUTDIR}/netinfo/netstat_ain
  netstat -anr > ${OUTDIR}/netinfo/netstat_anr
  netstat -s   > ${OUTDIR}/netinfo/netstat_s
  netstat -v   > ${OUTDIR}/netinfo/netstat_v 2>> ${OUTDIR}/netinfo/netstat_v
  netstat -an  > ${OUTDIR}/netinfo/netstat_an
  netstat -m   > ${OUTDIR}/netinfo/netstat_m 2>> ${OUTDIR}/netinfo/netstat_m

  awk '{ if (( $0 ~ /priority mblk failures/ )&&( $1 > 0 )) print "WARNING : NETSTAT : mbuffer errors reported at netstat -m" }' < ${OUTDIR}/netinfo/netstat_m

  netstat -M   > ${OUTDIR}/netinfo/netstat_M 2>> ${OUTDIR}/netinfo/netstat_M
  if [ "${GETPERF}" = "Y" ]; then
    C=${COLL_SEC}
    while [ ${C} -gt 0 ]
    do
      sleep 5
      C=$((C-5))

      netstat -s   > ${OUTDIR}/netinfo/netstat_s_${C} 2>> ${OUTDIR}/netinfo/netstat_s_${C}
  
      # Validate Socket backlog
      netstat -aon > ${OUTDIR}/netinfo/netstat_aon_${C} 2>> ${OUTDIR}/netinfo/netstat_aon_${C}
      netstat -an > ${OUTDIR}/netinfo/netstat_an_${C}   2>> ${OUTDIR}/netinfo/netstat_an_${C}
      netstat -ain > ${OUTDIR}/netinfo/netstat_ain_${C} 2>> ${OUTDIR}/netinfo/netstat_ain_${C}
      netstat -anr > ${OUTDIR}/netinfo/netstat_anr_${C} 2>> ${OUTDIR}/netinfo/netstat_anr_${C}
    done
  fi

  for A in $(awk '{ if ( $1 ~ /^en/ ) { print $1; }}' < ${OUTDIR}/netinfo/netstat_ain | sort -u)
  do
    my_entstat ${A} 
    my_hbastat ${OUTDIR}/netinfo/entstat_d_${A}
  done

  arp -a  > ${OUTDIR}/netinfo/arp_a
  /usr/sbin/rsct/bin/ctsvhbac > ${OUTDIR}/netinfo/ctsvhbac 2>> ${OUTDIR}/netinfo/ctsvhbac
  no -L > ${OUTDIR}/netinfo/no_L 2>> ${OUTDIR}/netinfo/no_L
  no -aF > ${OUTDIR}/netinfo/no_aF 2>> ${OUTDIR}/netinfo/no_aF

  awk '{
         if (( $1 ~ /sockthresh|strthresh/ )&&( $3 > 85 ))
           print "WARNING : NO : Network parameter sockthresh or strthresh are set to "$3"% of the thewall memmory ( too high )";
         if (( $1 ~ /tcp_pmtu_discover|udp_pmtu_discover/ )&&( $3 == 0 ))
           print "WARNING : NO : Network parameter "$1" have been set to "$3;
       }' < ${OUTDIR}/netinfo/no_aF

  if [ -n "$(grep '1485-123 Error' ${OUTDIR}/netinfo/no_L)" ]; then
    echo "ERROR : Unable to retrieve all no system calls, possible kernel corruption"
  fi

  pmtu display >> ${OUTDIR}/netinfo/pmtu_display 2>> ${OUTDIR}/netinfo/pmtu_display
  sna -d s 2> ${OUTDIR}/netinfo/sna_d_s > ${OUTDIR}/netinfo/sna_d_s
  lssrc -s sna -l > ${OUTDIR}/netinfo/lssrc_s_sna_l 2> ${OUTDIR}/netinfo/lssrc_s_sna_l
  awk \
    '{
       if ( $6 == "LISTEN" )
       {
         if ( $4 ~ /\.25$/ )          { print "WARNING : NETSTAT : SMTP Service running";
         } else if ( $4 ~ /\.7$/ )    { print "WARNING : NETSTAT : ECHO Service running";
         } else if ( $4 ~ /\.19$/ )   { print "WARNING : NETSTAT : CHARGEN Service running";
         } else if ( $4 ~ /\.69$/ )   { print "WARNING : NETSTAT : TFTP Service running";
         } else if ( $4 ~ /\.23$/ )   { print "WARNING : NETSTAT : TELNET Service running";
         } else if ( $4 ~ /\.9$/ )    { print "WARNING : NETSTAT : DISCARD Service running";
         } else if ( $4 ~ /\.13$/ )   { print "WARNING : NETSTAT : DAYTIME Service running";
         } else if ( $4 ~ /\.67$/ )   { print "WARNING : NETSTAT : BOOTPS Service running";
         } else if ( $4 ~ /\.79$/ )   { print "WARNING : NETSTAT : FINGER Service running";
         } else if ( $4 ~ /\.21$/ )   { print "WARNING : NETSTAT : FTP Service running";
         } else if ( $4 ~ /\.514$/ )  { print "WARNING : NETSTAT : SHELL/RSH Service running";
         } else if ( $4 ~ /\.513$/ )  { print "WARNING : NETSTAT : LOGIN Service running";
         } else if ( $4 ~ /\.13$/ )   { print "WARNING : NETSTAT : DAYTIME Service running";
         } else if ( $4 ~ /\.37$/ )   { print "WARNING : NETSTAT : TIME Service running";
         } else if ( $4 ~ /\.9090$/ ) { print "WARNING : NETSTAT : WSM Service running";
         }
       }
     }' < ${OUTDIR}/netinfo/netstat_an

     # Organize hosts talking to this server
     awk '{ if (( $5 !~ /^\*|^:|127.0.0.1/ )&&( $0 ~ /tcp|udp/ )) print $5; }' < ${OUTDIR}/netinfo/netstat_an | cut -d'.'  -f-4 | sort -u > ${OUTDIR}/netinfo/connected_remote_hosts
     echo "INFO : NETSTAT : Hosts connected to this server : $(cat ${OUTDIR}/netinfo/connected_remote_hosts | xargs)"

  if [ -x "/usr/sbin/iptrace" -a "${GETPERF}" = "Y" -a "${GET_IPTRACE}" = "Y" ]; then
    (
      startsrc -s iptrace -a "-B -S 128 -T ${OUTDIR}/netinfo/iptrace_B_S_128.raw" >>  ${OUTDIR}/netinfo/startsrc_iptrace 2>> ${OUTDIR}/netinfo/startsrc_iptrace
      sleep ${COLL_SEC}
      stopsrc -s iptrace >> ${OUTDIR}/netinfo/stopsrc_iptrace 2>> ${OUTDIR}/netinfo/stopsrc_iptrace
      ipreport -Trsn ${OUTDIR}/netinfo/iptrace_B_S_128.raw >> ${OUTDIR}/netinfo/iptrace_B_S_128.ipreport 2>> ${OUTDIR}/netinfo/iptrace_B_S_128.ipreport
    ) &
    export CHIELDS="${CHIELDS} ${!}"
  fi

}

get_hacmpinfo()
{
  if [ -d "/usr/es/sbin/cluster/utilities" ]; then
    mkdir ${OUTDIR}/hacmp
    svmon -C clstrmgr > ${OUTDIR}/hacmp/svmon_clstrmgr
    for i in \
      cllsif cllslv cl_lspv cllsnode clRGinfo cldump cldisp \
      cllsfs cllslv cl_lspv cllsnode clRGinfo cldump cldisp \
      cllsif cllsfs cllscf cllsclstr cllsipnw cllslv \
      cllsnim cllsres cllsserv cllssite cllsstbys cllssvcs cllstopsvcs cllsvgdata \
      clshowres cllscf cllsclstr 
    do
      ${i} > ${OUTDIR}/hacmp/$(basename ${i}) 2>> ${OUTDIR}/hacmp/$(basename ${i})
    done

    for i in $(cllsgrp)
    do
      cllsvg -g $i > ${OUTDIR}/hacmp/cllsvg_g_$i
      cllsdisk -g $i > ${OUTDIR}/hacmp/cllsdisk_g_$i
    done
    # Export PowerHA config
    cl_exportdefinition -o "${OUTDIR}/hacmp/powerha_definition.haw" 2>> ${OUTDIR}/hacmp/cl_exportdefinition.log >> ${OUTDIR}/hacmp/cl_exportdefinition.log 

    # Diag PowerHA status
    (
      check_exist_bin clver
      if [ ${?} -eq 0 ]; then
        clver -rt -b -C yes >> ${OUTDIR}/hacmp/clver_rt_b_C_yes 2>> ${OUTDIR}/hacmp/clver_rt_b_C_yes &
        PID="${!}"
        my_background_checker "${PID}" "clver"
      else
        clconfig -v -O -tr -V normal > ${OUTDIR}/hacmp/clconfig_v_O_tr_V_normal 2>> ${OUTDIR}/hacmp/clconfig_v_O_tr_V_normal &
        PID="${!}"
        my_background_checker "${PID}" "clconfig"
      fi
    ) &

    check_exist_bin lscluster
    if [ ${?} -eq 0 ]; then
      for i in c i d s
      do
        lscluster -${i} 2>&1 > ${OUTDIR}/hacmp/lscluster_${i}
      done
    fi
    for i in c i n w m
    do
      cltopinfo -${i} 2>&1 > ${OUTDIR}/hacmp/cltopinfo_${i}
    done
    lssrc -Ss clstrmgrES 2>&1 > ${OUTDIR}/hacmp/lssrc_Ss_clstrmgrES
    lssrc -Ss clinfoES   2>&1 > ${OUTDIR}/hacmp/lssrc_Ss_clinfoES
    lssrc -ls gsclvmd    2>&1 > ${OUTDIR}/hacmp/lssrc_ls_gsclvmd
    lssrc -g cluster     2>&1 > ${OUTDIR}/hacmp/lssrc_g_cluster
    clrgdependency -t PARENT_CHILD -sp 2>${OUTDIR}/hacmp/clrgdependency_t_PARENT_CHILD_sp > ${OUTDIR}/hacmp/clrgdependency_t_PARENT_CHILD_sp
    clhandle -a                        2>&1 > ${OUTDIR}/hacmp/clhandle_a
    /usr/bin/odmget HACMPcluster       2>&1 > ${OUTDIR}/hacmp/odmget_HACMPcluster
    for NODE in $(clnodename | xargs | sed 's/ /,/g')
    do
      for IDS in $(cat ${OUTDIR}/process/running_users)
      do
        cl_lsuser -cspoc "-f -n ${NODE}" \
          -a account_locked unsuccessful_login_count loginretries maxage lastupdate groups capabilities id ${IDS} \
          >> ${OUTDIR}/hacmp/cl_lsuser_running_apps 2>> ${OUTDIR}/hacmp/cl_lsuser_running_apps
        if [ ${?} -ne 0 ]; then
          echo "ERROR : LSUSER : POWERHA Unable to get user information from ${NODE} ( User = ${IDS} )"
        fi
      done
    done
    if [ "${GETPERF}" = "Y" ]; then
      check_exist_bin rpvstat
      if [ ${?} -eq 0 ]; then
        (
          rpvstat -A -t -i 1 -c ${COLL_SEC} >> ${OUTDIR}/hacmp/rpvstat_Ati &
          my_background_checker "${!}" "rpvstat"
        ) &
        (
          rpvstat -C -t -i 1 -c ${COLL_SEC} >> ${OUTDIR}/hacmp/rpvstat_Cti &
          my_background_checker "${!}" "rpvstat"
        ) &
      fi
    fi

    # Collect AIX cluster info
    check_exist_bin clctrl
    if [ ${?} -eq 0 ]; then
      clctrl -tune -L > ${OUTDIR}/hacmp/clctrl_L     2>> ${OUTDIR}/hacmp/clctrl_L
      clctrl -tune -a > ${OUTDIR}/hacmp/clctrl_a     2>> ${OUTDIR}/hacmp/clctrl_a
      clctrl -sec -e  > ${OUTDIR}/hacmp/clctrl_sec_e 2>> ${OUTDIR}/hacmp/clctrl_sec_e
    fi

    # Collect AIX cluster info
    check_exist_bin clmgr
    if [ ${?} -eq 0 ]; then
      for i in "cluster ALL" repository site node network interface resource_group fallback_timer persistent_ip \
        service_ip application_controller application_monitor dependency tape file_collection snapshot method \
        log volume_group logical_volume file_system physical_volume mirror_pool efs ldap_server ldap_client hmc cod
      do
        clmgr query ${i} >  ${OUTDIR}/hacmp/clmgr_query_$(echo ${i} | sed 's/ /_/g' ) 2>> ${OUTDIR}/hacmp/clmgr_query_$(echo ${i} | sed 's/ /_/g' )
      done
    fi

  else
    echo "INFO : No PowerHA utilities directory found, assuming no PowerHA"
  fi
}


get_vioinfo()
{
  if [ -e "/usr/ios/cli/ioscli" ]; then
    mkdir -p ${OUTDIR}/ioscli
    for cmd in ioslevel lsgcl lsrole lsnports lssvc lsfailedlogin lsvopt lssvc lssw
    do
      ioscli ${cmd} > ${OUTDIR}/ioscli/${cmd} 2>/dev/null
    done
    for F in /usr/ios/cli/ios.level /usr/ios/cli/ios.level.new /usr/ios/cli/FPLEVEL.txt
    do
      if [ -e "${F}" ]; then
        awk -v F=${F} '{ print F" : "$0 }' < ${F} >> ${OUTDIR}/ioscli/ioslevel_files 2>> ${OUTDIR}/ioscli/ioslevel_files
      fi
    done
    if [ -f /usr/ios/cli/ios.level -a -f /usr/ios/cli/ios.level.new ]; then
      cat /usr/ios/cli/ios.level /usr/ios/cli/ios.level.new | sort -u | wc -l |\
        awk '{ if ( $1 > 1 ) { print "INFO : IOSLEVEL : Differences between ios.level and ios.level.new, a deeper check into installed packages is recommended"; }}'
    fi

    # Get VIOS setup parameters
    ioscli rules -o diff -s -d 2> ${OUTDIR}/ioscli/rules_o_diff_s_d >> ${OUTDIR}/ioscli/rules_o_diff_s_d

    # Validate SEA
    ioscli lsmap -net -all -fmt ':'  > ${OUTDIR}/ioscli/lsmap_net_all  2>/dev/null
    cut -d':' -f3,4 ${OUTDIR}/ioscli/lsmap_net_all | grep ^ent | sort -u | sed 's/:/ /g' | while read SEA BACK
    do
      if [ -n "$(awk -v BK="${BACK}" '{ if ( BK == $1 ) { if ( $0 ~ /EtherChannel/ ) { print "OI"; }}}' < ${OUTDIR}/lsdev)" ]; then
        if [ -e "${OUTDIR}/dev_attr/${BACK}"  ]; then
          awk -v BACK="${BACK}" '{
                 if ( $1 == "adapter_names" )
                 {
                   dev_num=split($2, T, "," );
                   if ( dev_num < 2 )
                      print "ERROR : LSATTR : Etherchannel "BACK" has only 1 physical adapter";
                 } else if (( $1 == "hash_mode" )&&( $2 != "src_dst_port" )) { 
                   print "WARNING : LSATTR : Etherchannel "BACK" not optimized, should use hash_mode src_dst_port";
                 } else if (( $1 == "mode" )&&( $2 != "8023ad" )) {
                   print "WARNING : LSATTR Etherchannel "BACK" not using LACP";
                 }
               }' < ${OUTDIR}/dev_attr/${BACK}
        fi
      else
        echo "ERROR : LSDEV : ${BACK} Not a etherchannel"
      fi

      echo "INFO : ENTSTAT : Requesting entstat of ${SEA}"
      my_entstat ${SEA} 
      my_hbastat ${OUTDIR}/ioscli/entstat_${SEA}

      # from perfmpr
      if [ "${GETPERF}" = "Y" ]; then
        (
          for i in $(awk '{ if (( $0 ~ /Shared Ethernet Adapter/ )&&( $0 ~ /Available/ )) { print $1 }}' < ${OUTDIR}/lsdev)
          do
            echo "${i} $(awk '{ if ( $1 == "accounting" ) print $2; }' < ${OUTDIR}/dev_attr/${i})" >> ${OUTDIR}/ioscli/sea_original_account_state
            chdev -l ${i} -a accounting=enabled >> /dev/null 2>> /dev/null
          done

          awk '{ if (( $0 ~ /Shared Ethernet Adapter/ )&&( $0 ~ /Available/ )) { print $1 }}' < ${OUTDIR}/lsdev | while read seadev
          do
            C=${COLL_SEC}
            while [ ${C} -gt 0 ]
            do
              sleep 5
              C=$((C-5))
              seastat -d $seadev > ${OUTDIR}/ioscli/seastat_d_${seadev}_${C} 2>> ${OUTDIR}/ioscli/seastat_d_${seadev}_${C}
            done
          done

          awk '{ system("chdev -l "$1" -a accounting="$2); }' < ${OUTDIR}/ioscli/sea_original_account_state >> /dev/null 2>> /dev/null
        ) &
        export CHIELDS="${CHIELDS} ${!}"
      fi
    done
    for EN in ${OUTDIR}/ioscli/entstat_*
    do
      awk -v EN="${EN}" '{
             if ( $0 ~ /High Availability Statistics/ ) start=1
             if ( start == 1 )
             {
               if ( $0 ~ /High Availability Mode:/  ) mode=$4; 
               if ( $1 == "Priority:" ) prio=$2;
               if ( $0 ~ /Control Channel PVID:/ ) { if ( $4 ~ /^[0-9]*$/ ) ctl_chan=$4; else ctl_chan="ERR"; } 
             }
           } END {
             print EN,mode,prio,ctl_chan;
           }' < ${EN} >> ${OUTDIR}/ioscli/sea_modes
    done
    TOTSEAA="$(grep Auto ${OUTDIR}/ioscli/sea_modes | wc -l | awk '{ print $1; }')"
    if [ ${TOTSEAA} -gt 1 ]; then
      for i in $(cut -d' ' -f3 ${OUTDIR}/ioscli/sea_modes | sort -u)
      do
        CURPRIOSEAA="$(cut -d' ' -f3 ${OUTDIR}/ioscli/sea_modes | grep ${i} | wc -l | awk '{ print $1; }')"
        if [ ${CURPRIOSEAA} -gt $((TOTSEAA/2)) ]; then
          echo "WARNING : SEA : Possible SEA unbalance, too many SEAs with priority ${i}"
        fi
      done
      awk '{ if ( $5 == "ERR" ) print "ERROR : SEA : Unable to identify the control channel vlan id for "$1; }' < ${OUTDIR}/ioscli/sea_modes
    fi
    

    ioscli lsmap -npiv -all -fmt ':' > ${OUTDIR}/ioscli/lsmap_npiv_all 2>/dev/null
    for FC in $(cut -d':' -f7 < ${OUTDIR}/ioscli/lsmap_npiv_all | sort -u )
    do
      (
        my_fcstat ${FC}
      ) &
      export CHIELDS="${CHIELDS} ${!}"
      VFCCNT="$(cut -d':' -f7 < ${OUTDIR}/ioscli/lsmap_npiv_all | grep ${FC} | wc -l | awk '{ print $1; }')"
      if [ ${VFCCNT} -gt 0 ]; then
        echo "INFO : LSMAP : The adapter ${FC} provide access to ${VFCCNT} NPIV clients and has to hold a max of $((VFCCNT*256)) command elements"
      fi
    done

    for i in $(awk -F: '{ print $4; }' <  ${OUTDIR}/ioscli/lsmap_npiv_all  | sort -u)
    do
      awk -F: -v HST="${i}" '{ if ( $4 == HST ) cnt=cnt+1;  } END { print "INFO : LSMAP NPIV : "cnt" clients found for host "HST; } ' < ${OUTDIR}/ioscli/lsmap_npiv_all
    done


    ioscli lsmap -all       -fmt ':' > ${OUTDIR}/ioscli/lsmap_all      2>/dev/null
    ioscli lsmap -ams -all  -fmt ':' > ${OUTDIR}/ioscli/lsmap_ams_all  2>/dev/null
    ioscli lsmap -fmt ':' -field svsa physloc clientid vtd lun backing -all > ${OUTDIR}/ioscli/lsmap_cust 2>/dev/null

    if [ -f "${OUTDIR}/diskinfo/spof_disks" ]; then
      for D in $(cut -d':' -f6 ${OUTDIR}/ioscli/lsmap_cust | sort -u)
      do
        if [ -n "$(awk -v DSK=${D} '{ if ( $1 == DSK ) { print "OPS"; }}' < ${OUTDIR}/diskinfo/spof_disks)" ]; then
          echo "ERROR : LSPATH : ${D} is exposed to SPOF"
        fi
      done
    fi
    ioscli lsauth ALL       > ${OUTDIR}/ioscli/lsauth_ALL 2>/dev/null
    ioscli lssp             > ${OUTDIR}/ioscli/lssp 2>/dev/null

    if [ "${GETPERF}" = "Y" ]; then
      C=$((COLL_SEC/2))
      (
        ioscli viostat -adapter >> ${OUTDIR}/ioscli/viostat_adapter 2>> ${OUTDIR}/ioscli/viostat_adapter
        ioscli viostat -sys -adapter -tty >> ${OUTDIR}/ioscli/viostat_sys_adapter_tty 2>> ${OUTDIR}/ioscli/viostat_sys_adapter_tty
        ioscli viostat -adapter 5 ${C} >> ${OUTDIR}/ioscli/viostat_adapter_5 2>> ${OUTDIR}/ioscli/viostat_adapter_5
        ioscli fcstat -client  >> ${OUTDIR}/ioscli/fcstat_client 2>> ${OUTDIR}/ioscli/fcstat_client
      ) &
      export CHIELDS="${CHIELDS} ${!}"
    fi
    

    check_exist_bin kdb
    if [ ${?} -eq 0 ]; then
      awk '{ if (( $0 ~ /vfchost/ )&&( $0 ~ /Available/ )) { print $1 }}' < ${OUTDIR}/lsdev | while read host
      do
        echo "svfcCI; svfcPrQs; svfcva $host" | kdb >> ${OUTDIR}/ioscli/kdb_${host}
      done
    fi

    # Shared Storage Pool stuff
    ioscli cluster -list            > ${OUTDIR}/ioscli/ioscli_cluster_-list 2>> ${OUTDIR}/ioscli/ioscli_cluster_-list
    CLNAME="$(awk '{ if ( $1 == "CLUSTER_NAME:" ) { print $2; } }' < ${OUTDIR}/ioscli/ioscli_cluster_-list)"
    if [ "${CLNAME}" != "" ]; then
      ioscli cluster -status -clustername ${CLNAME}          > ${OUTDIR}/ioscli/ioscli_cluster_-status 2>> ${OUTDIR}/ioscli/ioscli_cluster_-status
      ioscli cluster -status -clustername ${CLNAME} -verbose > ${OUTDIR}/ioscli/ioscli_cluster_-status_-verbose 2>> ${OUTDIR}/ioscli/ioscli_cluster_-status_-verbose
      ioscli snapshot -clustername ${CLNAME} -list           > ${OUTDIR}/ioscli/ioscli_snapshot_list 2>> ${OUTDIR}/ioscli/ioscli_snapshot_list
      ioscli lssp -clustername ${CLNAME}                     > ${OUTDIR}/ioscli/ioscli_lssp_clustername_${CLNAME} 2>> ${OUTDIR}/ioscli/ioscli_lssp_clustername_${CLNAME}
      for SP in $(awk '{  if ( $1 == "POOL_NAME:" ) { print $2; }}' < ${OUTDIR}/ioscli/ioscli_lssp_clustername_${CLNAME})
      do
         ioscli lssp -clustername ${CLNAME} -sp ${SP} -bd >> ${OUTDIR}/ioscli/ioscli_lssp_clustername_${CLNAME}_sp_${SP}_bd 2>> ${OUTDIR}/ioscli/ioscli_lssp_clustername_${CLNAME}_sp_${SP}_bd

      done
    fi
    ioscli tier -list -verbose      > ${OUTDIR}/ioscli/ioscli_tier_-list_-verbose 2>> ${OUTDIR}/ioscli/ioscli_tier_-list_-verbose
    ioscli lu -list -verbose        > ${OUTDIR}/ioscli/ioscli_lu_-list_-verbose 2>> ${OUTDIR}/ioscli/ioscli_lu_-list_-verbose
    ioscli pv -list -verbose        > ${OUTDIR}/ioscli/ioscli_pv_-list_-verbose 2>> ${OUTDIR}/ioscli/ioscli_pv_-list_-verbose
    ioscli failgrp -list -verbose   > ${OUTDIR}/ioscli/ioscli_failgrp_-list_-verbose 2>> ${OUTDIR}/ioscli/ioscli_failgrp_-list_-verbose
    ioscli alert -list              > ${OUTDIR}/ioscli/ioscli_alert_list 2>> ${OUTDIR}/ioscli/ioscli_alert_list

  fi
}

get_processinfo()
{
  # Memory / Proc info
  lsps -a                   > ${OUTDIR}/lsps_a
  lsps -s                   > ${OUTDIR}/lsps_s
  ####### Process ps information
  mkdir -p ${OUTDIR}/process
  ps -aek -o '%a:%U:%G'     > ${OUTDIR}/process/ps_aek
  ps -ef                    > ${OUTDIR}/process/ps_ef
  ps -eZ                    > ${OUTDIR}/process/ps_eZ
  ps -elfk                  > ${OUTDIR}/process/ps_elfk
  ps -ekmo THREAD           > ${OUTDIR}/process/ps_ekmo_THREAD
  ps aux                    > ${OUTDIR}/process/ps_aux
  ps -el                    > ${OUTDIR}/process/ps_el
  ps guww                   > ${OUTDIR}/process/ps_guww
  cat ${OUTDIR}/process/ps_guww | while read A ; do if [ "$(echo ${A} | grep wait)" ]; then break ; else  echo ${A} ; fi ; done | grep -v ^USER > ${OUTDIR}/process/running_proc_list
  ps -Afmo pid,ppid,tid,thcount,flags,pri,cpu,bnd,sched,nice,dpgsz,spgsz,tpgsz,shmpgsz,time,etime,vsz,st,rssize,pmem,pcpu,args > ${OUTDIR}/process/ps_Afmo_tons
  awk '{ cnt=cnt+1 ; if ( $4 != "-" ) thcnt=thcnt+$4; } END { tot=cnt/thcnt;  print "INFO : PS : Average threads per process : "tot; }' < ${OUTDIR}/process/ps_Afmo_tons;

  # Create a library dir
  awk '{ if ( $2 != "PID" ) { system("procldd "$2" 2>/dev/null"); system("procwdx "$2" 2>/dev/null"); } }' < ${OUTDIR}/process/ps_ef | cut -f1 -d'[' | cut -d':' -f2 | while read A
  do
    if [ -f "${A}" ]; then
      dirname ${A} 2>/dev/null
    fi 
  done | sort -u | xargs | sed 's/ /:/g' > ${OUTDIR}/process/checklibpath

  PCNT=0
  PAMN=0
  for PLST in $(awk '{ print $2; }' < ${OUTDIR}/process/running_proc_list)
  do
    X=$(awk -v P="${PLST}" '{ if ( $1 == P ) print $4 }' < ${OUTDIR}/process/ps_Afmo_tons)
    PCNT=$((PCNT+X))
    PAMN=$((PAMN+1))
  done
  if [ ${PAMN} -gt 0 ]; then
    T=$((PCNT/PAMN))
    echo "INFO : PS : Average threads per running process before the first wait : ${T}"
  fi
  echo "INFO : PS : Amount of process running before the first wait : ${PAMN}"
  if [ -n "$(grep kbiod ${OUTDIR}/process/running_proc_list)" ]; then
    echo "INFO : PS : KBIOD on top list, sb_max should be evaluated to at least >= ( tcp_sendspace+tcp_recvspace+udp_sendspace+udp_recvspace)*2.5"
  fi
  if [ -n "$(grep vx_sched ${OUTDIR}/process/running_proc_list)" ]; then
    echo "INFO : PS : vx_sched on top list mean that a veritas filesystem is probably under heavy pressure; veritas tunning should be evaluated"
  fi
  if [ -n "$(grep uprintfd ${OUTDIR}/process/running_proc_list)" ]; then
    if [ -d "/var/mqm/trace" ]; then
      echo "INFO : PS : MQ trace enabled and no AMQ_DISABLE_AIX_NATIVE_TRACE=1 have been defined, this could be pressuring uprintfd"
    else
      echo "INFO : PS : uprintfd consuming resources, errpt increment ratio and contents should be evaluated"
    fi
  fi


  egrep -v "STIME|LOGNAME" ${OUTDIR}/process/ps_ef | sort +3 -r | head -n 30 > ${OUTDIR}/process/cpu_intensive_proc
  for UID in $(awk '{ print $1; }' < ${OUTDIR}/process/cpu_intensive_proc | sort -u)
  do
    lsuser -a account_locked unsuccessful_login_count loginretries maxage lastupdate groups capabilities id ${UID} >> ${OUTDIR}/process/lsuser_info
  done
  for PID in $(awk '{ print $2; }' < ${OUTDIR}/process/cpu_intensive_proc | sort -u)
  do
    ps ewwww ${PID} | grep ${PID} >> ${OUTDIR}/process/ps_environment
    ps -Z -T ${PID} | grep ${PID} >> ${OUTDIR}/process/ps_pages
  done
  awk 
  awk "{
         if (( \$0 ~ /${ENV_VAL}/ )&&( \$0 !~ /ENV_VAL/ ))
           print \"INFO : PS : Process have control variables exported, check ps ewww on PID \"\$1\" for more info\";
       }" < ${OUTDIR}/process/ps_environment | sort -u

  awk '{ if ( $3 != "UID" ) { print $3; }}' < ${OUTDIR}/process/ps_elfk | sort -u > ${OUTDIR}/process/running_users
  pstat -a > ${OUTDIR}/process/pstat_a 2>> ${OUTDIR}/process/pstat_a

  if [ "${GET_SVMON}" = "Y" ]; then
    # Top 20 process
    # svmon check
    (
      echo "INFO : Processing svmon..."
      (
        svmon -G -O unit=MB,timestamp=on,pgsz=on,affinity=detail  > ${OUTDIR}/process/svmon_GO_affinity  2>> ${OUTDIR}/process/svmon_GO_affinity &
        PID="${!}"
        my_background_checker "${PID}" "svmon"
      ) &

      ( 
        svmon -P -O unit=MB,sortentity=pin,timestamp=on -t 10 > ${OUTDIR}/process/svmon_P_O_pin 2>> ${OUTDIR}/process/svmon_P_O_pin &
        PID="${!}"
        my_background_checker "${PID}" "svmon"
      ) &

      (
        svmon -P -O unit=auto,filtercat=shared,filtertype=working > ${OUTDIR}/process/svmon_P_O_working 2>> ${OUTDIR}/process/svmon_P_O_working &
        PID="${!}"
        my_background_checker "${PID}" "svmon"
      ) &

  
  
      # Top 20 process
      svmon -P -O unit=auto | head -24 | tail -23 | while read A B
      do
        svmon -nrP ${A} > ${OUTDIR}/process/svmon_nrP_${A} 2>> ${OUTDIR}/process/svmon_nrP_${A}
        check_exist_bin procstack
        if [ ${?} -eq 0 ]; then
          (
            procstack    ${A} >> ${OUTDIR}/process/procstack_${A} 2>> ${OUTDIR}/process/procstack_${A} &
            PID="${!}"
            my_background_checker "${PID}" "procstat"
          ) &
          (
            procfiles -n ${A} >> ${OUTDIR}/process/procfiles_${A} 2>> ${OUTDIR}/process/procfiles_${A} &
            PID="${!}"
            my_background_checker "${PID}" "procfiles"
          ) &
          procmap      ${A} >> ${OUTDIR}/process/procmap_${A} 2>> ${OUTDIR}/process/procmap_${A}
          procwdx      ${A} >> ${OUTDIR}/process/procwdx_${A} 2>> ${OUTDIR}/process/procwdx_${A}
          procldd      ${A} >> ${OUTDIR}/process/procldd_${A} 2>> ${OUTDIR}/process/procldd_${A}
          procflags    ${A} >> ${OUTDIR}/process/procflags_${A} 2>> ${OUTDIR}/process/procflags_${A}
        fi
      done
      # Top process
      svmon -Put 1 > ${OUTDIR}/process/svmon_Put_1 2>> ${OUTDIR}/process/svmon_Put_1
    ) &
    export CHIELDS="${CHIELDS} ${!}"
  fi

  (
    if [ "${GETPERF}" = "Y" ]; then
      cd ${OUTDIR}/process
      check_exist_bin tprof
      if [ ${?} -eq 0 -a "${GET_TRACE}" = "Y" ]; then
        while [ -n "$(ps -ef | grep iptrace | grep -v grep)" ]
        do
          sleep 5 
        done 
        echo "-----------------------------------------------------------------------------------------------"
        echo "INFO : Get tprof information..."
        (
          # Get current event codes
          pstat -A     >> ${OUTDIR}/process/pstat_A 2>> ${OUTDIR}/process/pstat_A
          trcrpt -j    >> ${OUTDIR}/process/trcrpt_j 2>> ${OUTDIR}/process/trcrpt_j
          locktrace -S >> ${OUTDIR}/process/locktrace_S 2>> ${OUTDIR}/process/locktrace_S
          LIBPATH="${PATH}:$(cat ${OUTDIR}/process/checklibpath)" \
            trace -a -fn -o ${OUTDIR}/process/locktrace.raw -T 40M -L 400M -C all -d -p -r PURR \
              2>> ${OUTDIR}/process/locktrace.raw.cmdout >> ${OUTDIR}/process/locktrace.raw.cmdout
          trcnm >> ${OUTDIR}/process/trcnm 2>> ${OUTDIR}/process/trcnm
          trcon >> ${OUTDIR}/process/trcon 2>> ${OUTDIR}/process/trcon
          sleep ${COLL_SEC}
          trcstop
          gennames -f >> ${OUTDIR}/process/gennames_f 2>> ${OUTDIR}/process/gennames_f
          gensyms -F  >> ${OUTDIR}/process/gensyms.out 2>> ${OUTDIR}/process/gensyms.out.2
          locktrace -R >> ${OUTDIR}/process/locktrace_R 2>> ${OUTDIR}/process/locktrace_R
          trcrpt -Oexec=on,pid=on,tid=on,cpuid=on,svc=on ${OUTDIR}/process/locktrace.raw > ${OUTDIR}/process/locktrace.formated 2>> ${OUTDIR}/process/locktrace.formated.out

          cp /etc/trcfmt ${OUTDIR}/process

          netpmon -O all -r PURR -v -i ${OUTDIR}/process/locktrace.raw -n ${OUTDIR}/process/gensyms.out -o ${OUTDIR}/fsinfo/netpmon_O_all_r_PURR_v \
            2>> ${OUTDIR}/fsinfo/netpmon_O_all_r_PURR_v.cmdout >> ${OUTDIR}/fsinfo/netpmon_O_all_r_PURR_v.cmdout
          filemon -i ${OUTDIR}/process/locktrace.raw -n ${OUTDIR}/process/gensyms.out -v -O detailed,all  >> ${OUTDIR}/process/filemon  2>> ${OUTDIR}/process/filemon

          splat -i ${OUTDIR}/process/locktrace.raw -n ${OUTDIR}/process/gensyms.out -da -sa -o ${OUTDIR}/process/splat.all.acquisitions >> ${OUTDIR}/process/splat.all.cmdout 2>> ${OUTDIR}/process/splat.all.cmdout
          splat -i ${OUTDIR}/process/locktrace.raw -n ${OUTDIR}/process/gensyms.out -da -sc -o ${OUTDIR}/process/splat.all.cpu_hold     >> ${OUTDIR}/process/splat.all.cmdout 2>> ${OUTDIR}/process/splat.all.cmdout
          splat -i ${OUTDIR}/process/locktrace.raw -n ${OUTDIR}/process/gensyms.out -da -se -o ${OUTDIR}/process/splat.all.hold_time    >> ${OUTDIR}/process/splat.all.cmdout 2>> ${OUTDIR}/process/splat.all.cmdout
          splat -i ${OUTDIR}/process/locktrace.raw -n ${OUTDIR}/process/gensyms.out -da -ss -o ${OUTDIR}/process/splat.all.spin_count   >> ${OUTDIR}/process/splat.all.cmdout 2>> ${OUTDIR}/process/splat.all.cmdout
          splat -i ${OUTDIR}/process/locktrace.raw -n ${OUTDIR}/process/gensyms.out -da -sw -o ${OUTDIR}/process/splat.all.real_wait    >> ${OUTDIR}/process/splat.all.cmdout 2>> ${OUTDIR}/process/splat.all.cmdout
          splat -i ${OUTDIR}/process/locktrace.raw -n ${OUTDIR}/process/gensyms.out -da -sW -o ${OUTDIR}/process/splat.all.wait_qdepth  >> ${OUTDIR}/process/splat.all.cmdout 2>> ${OUTDIR}/process/splat.all.cmdout
          curt -i ${OUTDIR}/process/locktrace.raw -o ${OUTDIR}/process/curt.out -n ${OUTDIR}/process/gensyms.out\
            -m ${OUTDIR}/process/trcnm.out -e -p -ss -t -P 2>> ${OUTDIR}/process/curt.out.cmd >> ${OUTDIR}/process/curt.out.cmd
          cp /unix ${OUTDIR}/process/unix


          # Tprof stuff
          if [ -n "$(awk '{ if ( $1 ~ /6.1/ ) print "OI"; }' < ${OUTDIR}/lslpp_h_bos.mp)" ]; then
           tprof -skeuj -x sleep ${COLL_SEC}  > ${OUTDIR}/process/tprof.out 2>> ${OUTDIR}/process/tprof.out
          else
            tprof  -BDINRtljcskeS "${PATH}:$(cat ${OUTDIR}/process/checklibpath)" -x sleep ${COLL_SEC}  > ${OUTDIR}/process/tprof.out 2>> ${OUTDIR}/process/tprof.out
          fi
          trcstop >> /dev/null 2>> /dev/null

          # run truss -aedf -o truss.out <command>  # Trace command execution #  tprof -zlskeu -r trace
        ) &
        export CHIELDS="${CHIELDS} ${!}"
      fi
    fi
  ) &
  export CHIELDS="${CHIELDS} ${!}"
  vmo -L                    > ${OUTDIR}/vmo_L 2>> ${OUTDIR}/vmo_L
  vmo -aF                   > ${OUTDIR}/vmo_aF 2>> ${OUTDIR}/vmo_aF
  if [ -n "$(grep '1485-123 Error' ${OUTDIR}/vmo_L)" ]; then
    echo "ERROR : Unable to retrieve all vmo system calls, possible kernel corruption"
  fi
  schedo -aF                > ${OUTDIR}/schedo_aF 2>> ${OUTDIR}/schedo_aF
  schedo -L                 > ${OUTDIR}/schedo_L 2>> ${OUTDIR}/schedo_L
}

# Process lpar statistics ( Performance related analysis )
get_cpu_meminfo()
{
  # collect performance information
  if [ "${GETPERF}" = "Y" ]; then
    if [ -d "/var/perf/daily/" ]; then
      echo "INFO : TOPASOUT : Collecting contents of /var/perf/daily"
      mkdir -p ${OUTDIR}/topasout
      (
        cd /var/perf/daily
        for F in *.topas
        do
          if [ -f "${F}" ]; then
            if [ -f "${F}.csv" ]; then
              cp ${F}.csv ${OUTDIR}/topasout
            else
              topasout -a ${F}
              if [ -f "${F}.csv" ]; then
                mv ${F}.csv ${OUTDIR}/topasout
              fi
            fi
          fi
        done
      )
    fi
    (
      C=$(((COLL_SEC/5)+1))
      ( 
        lparstat -H > ${OUTDIR}/lparstat_H_begin 2>> ${OUTDIR}/lparstat_H_begin
        sleep ${COLL_SEC} 
        lparstat -H > ${OUTDIR}/lparstat_H_end   2>> ${OUTDIR}/lparstat_H_end

        echo "INFO : LPARSTAT H ---- : BEGIN ANALYSIS"
        echo "INFO : LPARSTAT H : Percentual at begin:"
        awk \
          -v TOT="$(awk '{ if ( $2 ~ /^[0-9]+$/ ) { if ( $2 > 0 ) tot=tot+$2; } } END { print tot; }' < ${OUTDIR}/lparstat_H_begin)" \
          '{
             if ( $2 ~ /^[0-9]+$/ )
             {
               t=$2*100/TOT;
               if ( t > 2 )
               {
                 print $1,t;
               } else {
                 other=other+t;
               }
             }
           } END {
             print "General Other",other;
           }' < ${OUTDIR}/lparstat_H_begin | while read A
         do
           echo "INFO : LPARSTAT H BEGIN : ${A}"
         done 
        echo "INFO : LPARSTAT H : Percentual at end:"  
        awk \
          -v TOT="$(awk '{ if ( $2 ~ /^[0-9]+$/ ) { if ( $2 > 0 ) tot=tot+$2; } } END { print tot; }' < ${OUTDIR}/lparstat_H_end)" \
          '{
             if ( $2 ~ /^[0-9]+$/ )
             {
               t=$2*100/TOT;
               if ( t > 2 )
               {
                 print $1,t;
               } else {
                 other=other+t;
               }
             }
           } END {
             print "General Other",other;
           }' < ${OUTDIR}/lparstat_H_end | while read A
         do
           echo "INFO : LPARSTAT H END : ${A}"
         done
         echo "INFO : LPARSTAT H ---- : END ANALYSIS"
 
      ) &
      export CHIELDS="${CHIELDS} ${!}"
      ( lparstat -d 5 ${C} > ${OUTDIR}/lparstat_d_5_${C}   2>> ${OUTDIR}/lparstat_d_5_${C} ) &
      export CHIELDS="${CHIELDS} ${!}"
      ( lparstat -h  5 ${C} > ${OUTDIR}/lparstat_h_5     2>> ${OUTDIR}/lparstat_h_5 ) &
      export CHIELDS="${CHIELDS} ${!}"
      ( lparstat -E   5 ${C} > ${OUTDIR}/lparstat_E_5   2>> ${OUTDIR}/lparstat_E_5   ) &
      export CHIELDS="${CHIELDS} ${!}"
      ( lparstat -mpe 5 ${C} > ${OUTDIR}/lparstat_mpe_5 2>> ${OUTDIR}/lparstat_mpe_5 ) &
      export CHIELDS="${CHIELDS} ${!}"
      ( 
        mpstat -a 2>> ${OUTDIR}/mpstat_a > ${OUTDIR}/mpstat_a
        mpstat -a 5 ${C} 2>> ${OUTDIR}/mpstat_a_5  > ${OUTDIR}/mpstat_a_5
      ) &
      export export CHIELDS="${CHIELDS} ${!}"
      ( mpstat -d 5 ${C}     > ${OUTDIR}/mpstat_d       2>> ${OUTDIR}/mpstat_d ) &
      export CHIELDS="${CHIELDS} ${!}"
      ( mpstat -i 5 ${C}     > ${OUTDIR}/mpstat_i       2>> ${OUTDIR}/mpstat_i ) &
      export CHIELDS="${CHIELDS} ${!}"
      ( mpstat -h 5 ${C}     > ${OUTDIR}/mpstat_h       2>> ${OUTDIR}/mpstat_h ) &
      export CHIELDS="${CHIELDS} ${!}"
      ( mpstat -s 5 ${C}     > ${OUTDIR}/mpstat_s       2>> ${OUTDIR}/mpstat_s ) &
      export CHIELDS="${CHIELDS} ${!}"
      (
        mpstat -w 2>> ${OUTDIR}/mpstat_w | tee -a ${OUTDIR}/mpstat_w |\
          awk '{
                 if ( $1 == "ALL" )
                 {
                   print "INFO : MPSTAT BOOT : Average Logical Processor Affinity : "$10;
                 }
               }'
        mpstat -w 5 ${C}    > ${OUTDIR}/mpstat_w_5       2>> ${OUTDIR}/mpstat_w_5
      ) &
      export CHIELDS="${CHIELDS} ${!}"
      ( 
        vmstat -i            > ${OUTDIR}/vmstat_i_begin         2>> ${OUTDIR}/vmstat_i_begin
        sleep ${COLL_SEC}
        vmstat -i            > ${OUTDIR}/vmstat_i_end         2>> ${OUTDIR}/vmstat_i_end
      ) &
      export CHIELDS="${CHIELDS} ${!}"
      ( alstat -e 5 ${C} >> ${OUTDIR}/alstat_e_5 2>> ${OUTDIR}/alstat_e_5 ) &
      export CHIELDS="${CHIELDS} ${!}"
      ( alstat -v 5 ${C} >> ${OUTDIR}/alstat_v_5 2>> ${OUTDIR}/alstat_v_5 ) &
      export CHIELDS="${CHIELDS} ${!}"
      ( emstat -a 5 ${C} >> ${OUTDIR}/emstat_a_5 2>> ${OUTDIR}/emstat_a_5 ) &
      export CHIELDS="${CHIELDS} ${!}"
      ( emstat -v 5 ${C} >> ${OUTDIR}/emstat_v_5 2>> ${OUTDIR}/emstat_v_5 ) &
      export CHIELDS="${CHIELDS} ${!}"
      ( vmstat -Iwt 5 ${C}   > ${OUTDIR}/vmstat_Iwt_5     2>> ${OUTDIR}/vmstat_Iwt_5 ) &
      export CHIELDS="${CHIELDS} ${!}"
      # hpmstat stuff
      if [ ! -e "/usr/ios/cli/ioscli" -a "${GET_TRACE}" = "Y" ]; then
        ( 
          hpmstat -r -g 61 3 10 > ${OUTDIR}/hpmstat_r_g_61_3_10    2>> ${OUTDIR}/hpmstat_r_g_61_3_10
          hpmstat -g 180 10     > ${OUTDIR}/hpmstat_g_180_10    2>> ${OUTDIR}/hpmstat_g_180_10
          hpmstat -g 101 10     > ${OUTDIR}/hpmstat_g_101_10    2>> ${OUTDIR}/hpmstat_g_101_10
          hpmstat -g 53 10      > ${OUTDIR}/hpmstat_g_53_10     2>> ${OUTDIR}/hpmstat_g_53_10
          hpmstat -u -g 108 10  > ${OUTDIR}/hpmstat_u_g_108_10  2>> ${OUTDIR}/hpmstat_u_g_108_10 
          hpmstat -u 10         > ${OUTDIR}/hpmstat_u_10        2>> ${OUTDIR}/hpmstat_u_10
          hpmstat -k -g 108 10  > ${OUTDIR}/hpmstat_k_g_108_10  2>> ${OUTDIR}/hpmstat_k_g_108_10
          hpmstat -H -g 108 10  > ${OUTDIR}/hpmstat_H_g_108_10  2>> ${OUTDIR}/hpmstat_H_g_108_10
          hpmstat -s 0 5 $((COLL_SEC/5)) >> ${OUTDIR}/hpmstat_s_0_5_$((COLL_SEC/5)) 2>> ${OUTDIR}/hpmstat_s_0_5_$((COLL_SEC/5))
        ) &
        export CHIELDS="${CHIELDS} ${!}"
      fi
    )
  fi
  (
    vmstat -f      >> ${OUTDIR}/vmstat_f_begin 2>> ${OUTDIR}/vmstat_f_begin
    vmstat -sp ALL >> ${OUTDIR}/vmstat_sp_ALL_begin 2>> ${OUTDIR}/vmstat_sp_ALL_begin
    sleep ${COLL_SEC}
    vmstat -f      >> ${OUTDIR}/vmstat_f_end 2>> ${OUTDIR}/vmstat_f_end
    vmstat -sp ALL >> ${OUTDIR}/vmstat_sp_ALL_end 2>> ${OUTDIR}/vmstat_sp_ALL_end
  ) &
  export CHIELDS="${CHIELDS} ${!}"

  (
    vmstat -sv     >> ${OUTDIR}/vmstat_sv_begin     2>> ${OUTDIR}/vmstat_sv_begin
    sleep ${COLL_SEC}
    vmstat -sv     >> ${OUTDIR}/vmstat_sv_end     2>> ${OUTDIR}/vmstat_sv_end
    awk -v MINPERM="$(awk '{ if ( $1 == "minperm%" ) print $2; }' < ${OUTDIR}/vmo_L)" -v TOT_MEM="$(awk '{ if ( $0 ~ /Online Memory/  ) print $4; }' < ${OUTDIR}/lparstat_i)" \
    '{
      if ( $0 ~ /pending disk I\/Os blocked with no pbuf/ ) {
        if ( $1 > 0 )
          print "WARNING : VMSTAT : blocked lvm IO, please check pv_pbuf_count under lvmo";
      } else if ( $0 ~ /filesystem I\/Os blocked with no fsbuf|external pager filesystem I\/Os blocked with no fsbuf/ ) {
        if ( $1 > 0 )
          print "WARNING : VMSTAT : blocked FS IO, please check jfs/jfs2 buffer setup";
      } else if ( $0 ~ /percentage of memory used for computational pages/ ) {
        if ( $1 > 75 )
          print "WARNING : VMSTAT : "$1"% of pages are being used for computational memory ( lpar might need more memory )";
        else if ( $1 < 20 )
          print "WARNING : VMSTAT : "$1"% of pages are being used for computational memory ( lpar has too much memory )";

        projected_mem = int(TOT_MEM*$1/55)+1;
        print "INFO : VMSTAT : Projected memory size for this lpar: "projected_mem" MB";
        print "INFO : VMSTAT : Actual memory size of this lpar: "TOT_MEM" MB";

      } else if ( $0 ~ /pages freed by the clock/ ) { freed_clock = $1;
      } else if ( $0 ~ /pages examined by clock/ ) {  exam_clock = $1;
      } else if ( $2 == "iodones" ) { iodones = $1;
      } else if ( $0 ~ /pending I\/O waits/ ) { pend_io_wait = $1;
      } else if ( $0 ~ /start I\/Os/ ) { start_io = $1;
      } else if ( $0 ~ /cpu context switches/ ) { cpu_cs = $1;
      } else if ( $0 ~ /device interrupts/ ) { dev_intr = $1;
      } else if ( $0 ~ /software interrupts/ ) { sw_intr = $1;
      } else if ( $0 ~ /decrementer interrupts/ ) { dec_intr = $1;
      } else if ( $0 ~ /syscalls/ ) { syscalls = $1;
      } else if ( $0 ~ /numperm percentage|numclient percentage/ ) {
        if ( MINPERM > $1 )
          print "WARNING : VMSTAT : "$2" is below minperm%";
      }
    } END {
      if ( freed_clock > 0 )
      {
        res1 = (exam_clock*100)/freed_clock;
        if ( res1 < 40 )
          print "WARNING : VMSTAT : Server might need more memory, pages examined by clock vs pages freed by clock ratio ( "res1" ) is too low";
      }
      if ( iodones <= 0 ) iodones = 1;
      res1 = (pend_io_wait*100)/iodones;
      if ( res1 > 80 )
        print "WARNING : VMSTAT : IO Contention at the system, lacking buffers to complete non-blocking IO, ratio: "res1;

      if ( start_io > 0 ) { res1 = (iodones*100)/start_io; print "INFO : VMSTAT : Sequential IO ratio estimated at : "res1; }
      if ( dec_intr > 0 ) { res1 = cpu_cs/dec_intr; print "INFO : VMSTAT : Average Decrementer Interrupt per CPU CS : "res1; }
      if ( sw_intr > 0 ) { res1 = cpu_cs/sw_intr; print "INFO : VMSTAT : Average Software Interrupt per CPU CS : "res1; } else
        print "WARNING : VMSTAT : Software interrupts reported as 0";

      if ( dev_intr > 0 ) {
        res1 = cpu_cs/dev_intr; print "INFO : VMSTAT : Average Device Interrupt per CPU CS: "res1;
        if ( res1 > 25 ) { print "INFO : VMSTAT : Consider re-evaludate big_tick_size / timeslice"; } else if ( res1 < 1 )
          print "WARNING : VMSTAT : Device interrupts against cpu cs is too high, possible device contention";
      } else
        print "WARNING : VMSTAT : Device Interrupts reported as 0";

      if ( dec_intr > 0 ) { res1 = syscalls/dec_intr; print "INFO : VMSTAT : Average system Calls per Decrementer Interrupt : "res1; } else
        print "WARNING : VMSTAT : Decrementer Interrupts reported as 0";
    }' < ${OUTDIR}/vmstat_sv_end
  ) &
  export CHIELDS="${CHIELDS} ${!}"

}

get_generalinfo()
{
  # General info
  lparstat -i                 > ${OUTDIR}/lparstat_i 2>> ${OUTDIR}/lparstat_i
  if [ ${?} -ne 0 ]; then
    echo "INFO : LPARSTAT : Statistics are disabled on the lpar, enable it on lpar profile"
  fi
  prtconf                     > ${OUTDIR}/prtconf 2>> ${OUTDIR}/prtconf
  uptime                      > ${OUTDIR}/uptime
  uname -a                    > ${OUTDIR}/uname_a
  oslevel -r                  > ${OUTDIR}/oslevel_r
  oslevel -s                  > ${OUTDIR}/oslevel_s
  instfix -i                  > ${OUTDIR}/instfix_i
  lslpp -l                    > ${OUTDIR}/lslpp_l
  lslpp -h bos.mp*            > ${OUTDIR}/lslpp_h_bos.mp 2>> ${OUTDIR}/lslpp_h_bos.mp
  emgr -l                     > ${OUTDIR}/emgr_l 2>> ${OUTDIR}/emgr_l
  lppchk -vm3                 > ${OUTDIR}/lppchk_vm3 2>> ${OUTDIR}/lppchk_vm3
  audit query                 > ${OUTDIR}/audit_query  2>> ${OUTDIR}/audit_query
  bootlist -m normal -o       > ${OUTDIR}/bootlist_m_normal_o
  lssecattr -c -F ALL         > ${OUTDIR}/lssecattr_c_F_ALL 2> ${OUTDIR}/lssecattr_c_F_ALL
  lsrole -f ALL               > ${OUTDIR}/lsrole_f_ALL
  ipl_varyon -i               > ${OUTDIR}/ipl_varyon_i
  bootinfo -b                 > ${OUTDIR}/bootinfo_b
  bootinfo -r                 > ${OUTDIR}/bootinfo_r
  ctctrl -q                   > ${OUTDIR}/ctctrl_q
  lsdevinfo                   > ${OUTDIR}/lsdevinfo 2>> ${OUTDIR}/lsdevinfo
  # disable trace for LAN :  ctctrl -r -c netinet memtraceoff
  awk '{ if (( $1 !~ /^\.|Component|\||--/ )&&( $5 ~ /OFF/ )) print "INFO : CTCTRL : Memory Trace disabled for "$1 ; }' < ${OUTDIR}/ctctrl_q
  lssrad -av                  > ${OUTDIR}/lssrad_av 2>> ${OUTDIR}/lssrad_av

  genkex -d > ${OUTDIR}/genkex_d
  if [ "${GET_TRUSTCHK}" = "Y" ]; then
    ( 
      check_exist_bin trustchk
      if [ ${?} -eq 0 ]; then
        echo "INFO : Getting trustchk information..."
        trustchk -n ALL           > ${OUTDIR}/trustchk_n_ALL 2>> ${OUTDIR}/trustchk_n_ALL
        export TRUSTCHK_PID="${!}"
      fi
    ) &
    export CHIELDS="${CHIELDS} ${!}"
  fi

  check_exist_bin kdb
  if [ ${?} -eq 0 ]; then
    if [ -n "$(echo "quit" | kdb 2>&1 | grep 'Version mismatch between unix file and memory image')" ]; then
      echo "ERROR : Running kernel don't match installed one"
      echo "  Install date history :"
      awk '{ if ( $0 ~ /COMMIT|APPLY/ ) { print "  ",$1,$2,$4,$5; }}' < ${OUTDIR}/lslpp_h_bos.mp
      export KDB_OK="N"
    else 
      echo "mempool *"             | kdb >> ${OUTDIR}/kdb_mempool 2>> ${OUTDIR}/kdb_mempool
      echo "frameset *"            | kdb >> ${OUTDIR}/kdb_frameset 2>> ${OUTDIR}/kdb_frameset
      echo "memp *\n\nvmpool -l *" | kdb >> ${OUTDIR}/kdb_memp_vmpool 2>> ${OUTDIR}/kdb_memp_vmpool
      echo "vmker -seg"            | kdb >> ${OUTDIR}/kdb_vmker 2>> ${OUTDIR}/kdb_vmker
      echo "xm -u"                 | kdb >> ${OUTDIR}/kdb_xm 2>> ${OUTDIR}/kdb_xm
      echo "mtrc"                  | kdb >> ${OUTDIR}/kdb_mtrc 2>> ${OUTDIR}/kdb_mtrc
      echo "rmap *"                | kdb >> ${OUTDIR}/kdb_rmap 2>> ${OUTDIR}/kdb_rmap
      echo "iplcb -mem"            | kdb >> ${OUTDIR}/kdb_iplcb 2>> ${OUTDIR}/kdb_iplcb
      # pending IO
      echo "pdt *"                 | kdb >> ${OUTDIR}/kdb_pdt 2>> ${OUTDIR}/kdb_pdt
    fi

  else
    echo "WARNING : PKG : kdb not found"
    export KDB_OK="N"
  fi

  check_exist_bin rpm
  if [ ${?} -eq 0 ]; then
    rpm -qa 2>&1 > ${OUTDIR}/rpm_qa
  fi

  if [ ! -e "/unix" ]; then
    echo "ERROR : KERNEL : /unix not found, ipl won't work properly"
  fi
  if [ -f "${OUTDIR}/instfix_i" ]; then
    for i in $(awk '{ if (( $0 ~ /Not all filesets for/  )&&( $5 ~ /ML$|SP$/ )) { print $5 }}' < ${OUTDIR}/instfix_i | sort -u)
    do
      instfix -ick ${i} | awk -F':' '{ if ( $5 == "-" ) { print "WARNING : INSTFIX : Missing fix "$2" version "$3; }}' 
    done
  fi

  # VLM Stuff
  wlmcntrl -q    >> ${OUTDIR}/wlmcntrl_q    2>> ${OUTDIR}/wlmcntrl_q

  # Save config files
  mkdir -p ${OUTDIR}/conf_dump/odm
  for i in /etc/profile /etc/environment /etc/hosts /etc/inittab /etc/services /etc/filesystems \
           /etc/exports /etc/security/limits ~root/.rhosts /etc/inetd.conf /usr/es/sbin/cluster/etc/clhosts \
           /usr/es/sbin/cluster/etc/clinfo.rc /usr/es/sbin/cluster/etc/exports /usr/es/sbin/cluster/etc/harc.net \
           /usr/es/sbin/cluster/etc/ClSm /etc/resolv.conf /etc/netsvc.conf /etc/rc.net /etc/rc.nfs /usr/es/sbin/cluster/.use_telinit \
           /etc/snmpd.conf  /etc/snmpdv3.conf /etc/snmpd.peers /etc/syslog.conf /var/adm/clavan.log /usr/es/sbin/cluster/netmon.cf \
           /usr/es/sbin/cluster/netmon.cf /usr/es/sbin/cluster/etc/rhosts /usr/es/sbin/cluster/etc/cl_event_summaries.txt \
           /usr/es/sbin/cluster/etc/config/clip_config /usr/es/sbin/cluster/etc/config/clvg_config /etc/ntp.conf \
           /tmp/.netprobe.log /tmp/.ipHarvest.log /usr/es/sbin/cluster/etc/clpol /var/ha/log/nim.topsvcs.* /var/ha/log/nmDiag.topsvcs.* \
           /var/adm/ras/mmfs.log.latest /var/adm/ras/mmfs.log.previous /etc/ssh/sshd_config /etc/ssh/ssh_config /etc/netcd.conf \
           /etc/cronlog.conf /etc/security/audit/config /etc/security/audit/objects /etc/rc.bootc /etc/security/audit/bincmds \
           /etc/security/audit/events /etc/security/audit/streamcmds /etc/rc /etc/oratab
   do
     if [ -e "${i}" ]; then
       cp ${i} ${OUTDIR}/conf_dump/$(echo ${i} | sed 's/\//_/g') >> ${OUTDIR}/conf_dump/collect_stat 2>> ${OUTDIR}/conf_dump/collect_stat
     fi
   done

   # Copy log files
   if [ -e "${OUTDIR}/conf_dump/_etc_syslog.conf" ]; then
     for F in $(awk '{ if ( $0 !~ /^#|^$/ ) print $2; }' < ${OUTDIR}/conf_dump/_etc_syslog.conf)
     do
       if [ -e "${F}" -a -z "$(echo ${F} | grep '/dev')" ]; then
         gzip -9c < ${F} > ${OUTDIR}/conf_dump/"$(echo ${F} | sed 's/\//_/g')".gz 2>> ${OUTDIR}/conf_dump/collect_stat
       fi
     done
   fi
   # Copy HACMP logs
   if [ -d "/var/hacmp/log" ]; then
     (
       cd /var/hacmp/log
       tar -cpf ${OUTDIR}/conf_dump/var_hacmp_log.tar .
     )
   fi
   # Copy ODM information
   (
     cd /etc/objrepos
     for i in *
     do
       odmget ${i} >> ${OUTDIR}/conf_dump/odm/${i} 2>> ${OUTDIR}/conf_dump/odm/${i}
     done
   )
   lsitab -a > ${OUTDIR}/conf_dump/inittab

  mkdir -p ${OUTDIR}/crontabs
  cp /var/spool/cron/crontabs/* ${OUTDIR}/crontabs

  # rmc / dlpar
  if [ -x /usr/sbin/rsct/bin/rmcdomainstatus ]; then
    /usr/sbin/rsct/bin/rmcdomainstatus -s ctrmc >> ${OUTDIR}/rmcdomainstatus_ctrmc 2>> ${OUTDIR}/rmcdomainstatus_ctrmc
    if [ ${?} -ne 0 ]; then
      echo "ERROR : RMCDOMAINSTATUS : Unable to determine rmc connectivity"
    fi
  fi 
  (
    mkdir -p ${OUTDIR}/lsrsrc
    lsrsrc  > ${OUTDIR}/lsrsrc/lsrsrc  2>> ${OUTDIR}/lsrsrc/lsrsrc
    HANGED_CMD=""
    # Work around as lsrsrc commands sometimes hang
    (
      for P in $(cat ${OUTDIR}/lsrsrc/lsrsrc)
      do
        lsrsrc ${P} > ${OUTDIR}/lsrsrc/${P} 2>> ${OUTDIR}/lsrsrc/${P} &
        PID=${!}
        my_background_checker "${PID}" "lssrc"
      done
    ) >> ${OUTDIR}/lsrsrc/lsrsrc.service_status 2>> ${OUTDIR}/lsrsrc/lsrsrc.service_status
    if [ -z "$(grep HMCIPAddr ${OUTDIR}/lsrsrc/*IBM.MCP* 2>/dev/null)" -a -z "$(grep HMCIPAddr ${OUTDIR}/lsrsrc/*IBM.ManagementServer* 2>/dev/null)" ]; then
      echo "WARNING : LSRSRC : No HMC connectivity detected"
    fi
  ) &
  export CHIELDS="${CHIELDS} ${!}"

  if [ -x /usr/sbin/rsct/bin/hatsdmsinfo ]; then
    /usr/sbin/rsct/bin/hatsdmsinfo 2> ${OUTDIR}/hatsdmsinfo >> ${OUTDIR}/hatsdmsinfo
  fi
  /usr/sbin/rsct/bin/ctsvhbac > ${OUTDIR}/ctsvhbac 2>> ${OUTDIR}/ctsvhbac
  awk '{ if (( $1 == "Status:" )&&( $2 == "Attention" )) { print "WARNING : CTSVHBAC : Not all network interfaces are trusted by RSCT, you may face DLPAR problems"; }}' < ${OUTDIR}/ctsvhbac | sort -u

  # Device information
  lsdev > ${OUTDIR}/lsdev
  ls -l /dev > ${OUTDIR}/ls_l_dev
  mkdir ${OUTDIR}/dev_attr
  mkdir ${OUTDIR}/dev_cfg

  PMT="N"
  check_exist_bin powermt
  if [ ${?} -eq 0 ]; then
    PMT="Y"
  fi

  awk -v OUTDIR="${OUTDIR}" -v SKIPDISK="${SKIPDISK}" -v PMT="${PMT}" \
    '{
       if (( $1 !~ /hdisk/  )||(( PMT == "Y" )&&( SKIPDISK == "Y" )&&( $0 ~ /PowerPath/ )||( SKIPDISK == "N" )))
       {
         c1 = "lsattr -El "$1;
         while( ( c1 |getline v) > 0 ) print v >> OUTDIR"/dev_attr/"$1; close(c1);
         if ( $2 == "Available" )
         {
           c2 = "lscfg -vpl "$1" 2>&1";
           while( ( c2 |getline v) > 0 ) print v >> OUTDIR"/dev_cfg/"$1; close(c2);
         }
       }
     }' < ${OUTDIR}/lsdev

  for DV in mem0 aio0 sys0
  do
    ln -s ${OUTDIR}/dev_attr/${DV} ${OUTDIR}/${DV}
  done

  # Firmware information
  lsmcode -A > ${OUTDIR}/lsmcode_A 2>> ${OUTDIR}/lsmcode_A
  # Slot information
  lsparent -C -k scsi_scb   > ${OUTDIR}/lsparent_Ck_scsi_scb 2>> ${OUTDIR}/lsparent_Ck_scsi_scb
  lsparent -C -k lsa        > ${OUTDIR}/lsparent_Ck_lsa      2>> ${OUTDIR}/lsparent_Ck_lsa
  lsparent -C -k wsa        > ${OUTDIR}/lsparent_Ck_wsa      2>> ${OUTDIR}/lsparent_Ck_wsa
  lsparent -C -k scsi       > ${OUTDIR}/lsparent_Ck_scsi     2>> ${OUTDIR}/lsparent_Ck_scsi
  lsslot -c pci             > ${OUTDIR}/lsslot_c_pci         2>> ${OUTDIR}/lsslot_c_pci
  lscfg -vp                 > ${OUTDIR}/lscfg_vp

  # Aso checks
  check_exist_bin asoo
  if [ ${?} -eq 0 ]; then
    asoo -L > ${OUTDIR}/asoo_L 2>> ${OUTDIR}/asoo_L
  fi

  dscrctl -q  > ${OUTDIR}/dscrctl_q 2>> ${OUTDIR}/dscrctl_q
  if [ -n "$(grep '1485-123 Error' ${OUTDIR}/dscrctl_q)" ]; then
    echo "ERROR : Unable to retrieve all dscrctl system calls, possible kernel corruption"
  fi

  smtctl >> ${OUTDIR}/smtctl 2>> ${OUTDIR}/smtctl

  lssrc -a                  > ${OUTDIR}/lssrc_a 
  /usr/lib/ras/dumpcheck -p > ${OUTDIR}/dumpcheck_p 2> ${OUTDIR}/dumpcheck_p

  for SDU in /etc/sudoers /opt/etc/sudoers /usr/local/etc/sudoers /opt/freeware/etc/sudoers
  do
    if [ -f "${SDU}" ]; then
      if [ -n "$(grep '!logfile' ${SDU})" ]; then
        echo "WARNING : SUDOERS : wrong logging directive defined on ${SDU}"
      fi
    fi
  done

  # Print information
  (
    if [ -x /usr/lib/lpd/pio/etc/piolsvp ]; then
      /usr/lib/lpd/pio/etc/piolsvp -p > ${OUTDIR}/piolsvp 2>> ${OUTDIR}/piolsvp &
      PID="${!}"
      my_background_checker "${PID}" "piolsvp"
    else
      /usr/bin/lsallq                 > ${OUTDIR}/lsallq  2>> ${OUTDIR}/lsallq &
      PID="${!}"
      my_background_checker "${PID}" "lsallq"
    fi
  ) &
  (
    lpstat -W                         > ${OUTDIR}/lpstat  2>> ${OUTDIR}/lpstat &
    PID="${!}"
    my_background_checker "${PID}" "lpstat"
  ) &

  # Env and user info
  env       > ${OUTDIR}/env
  export    > ${OUTDIR}/export
  who       > ${OUTDIR}/who
  who -b    > ${OUTDIR}/who_b

  ## Remind:
  # MEMORY_AFFINITY=MCM
  # AIXTHREAD_SCOPE='S'
  # LDR_CNTRL='DATAPSIZE=64K@TEXTPSIZE=64K@STACKPSIZE=64K'
  # LDR_CNTRL=MAXDATA=0xD0000000@DSA
  # LDR_CNTRL=USERREGS  --> usefull for GC 
  # LDR_CNTRL=LARGE_PAGE_DATA=Y
  # VMM_CNTRL='vmm_fork_policy=COW'
  # EXTSHM=ON
  # unset AIXTHREAD_ENRUSG
  # AIXTHREAD_MNRATIO=1:1 or 1:x  , work only on AIXTHREAD_SCOPE=P
  # AIXTHREAD_MUTEX_FAST , ON make mutex switch faster
  # YIELDLOOPTIME=0 , bigger help on complex mutex
  # export MALLOCOPTIONS=pool,pool_balanced,buckets,no_mallinfo
  # export MALLOCOPTIONS=watson,mulitiheap:16,considersize
  # export MALLOCOPTIONS=buckets,mulitiheap:16,considersize
  # export MALLOCOPTIONS=pool,mulitiheap:16,considersize
  # export MALLOCOPTIONS=pool,multiheap,buckets
  # export MALLOCOPTIONS=watson
  # Multiheap size = 1/4 of amount of VCPU
  # MALLOCTYPE=3.1  --> eat twice memory of others
  # MALLOCTYPE=watson -> fastest on 64bits
  # MALLOCOPTIONS=pool<:max_size>
  # MALLOC DISCLAIM -> force more frequent GC calls on AIXVMM 
  # AIX_STDBUFSZ=1024
  # RT_GRQ=ON  --> Pute the thread on global queue instead of the processor queue ( similar of AIXTHREAD_SCOPE )

  # RWlock_Debug=off

  # Validate exported variables that change process behavior:
  cat ${OUTDIR}/env ${OUTDIR}/export | awk "{ if (( \$0 ~ /${ENV_VAL}/ )&&( \$0 !~ /ENV_VAL/ )) print \"INFO : Exported variable \"\$0; }"

  if [ "${USER_CHECK}" = "Y" ]; then
    last -100 > ${OUTDIR}/last_100
  fi
  history   > ${OUTDIR}/history

  for P in $(echo ${PATH} | sed 's/:/ /g')
  do
    if [ "${P}" = "." ]; then
      echo "WARNING : ENV : You have . defined as part of PATH, this can lead to problems"
    elif [ "${P}" = "${HOME}" ]; then
      echo "WARNING : ENV : You have your home defined as part of PATH, this can lead to problems"
    fi
  done

  # Error and console logs
  errpt                             > ${OUTDIR}/errpt
  errpt -a                          > ${OUTDIR}/errpt_a
  for log in bootlog bosinstlog cfglog conslog lvmcfg.log nimlog
  do
    alog -o -f /var/adm/ras/${log}  > ${OUTDIR}/alog_o_f_${log} 2>> ${OUTDIR}/alog_o_f_${log}
  done

  ipcs -bm      > ${OUTDIR}/ipcs_bm      2>> ${OUTDIR}/ipcs_bm
  ipcs -aPqrsXm > ${OUTDIR}/ipcs_aPqrsXm 2>> ${OUTDIR}/ipcs_aPqrsXm

  # sysdumpdev stuff
  sysdumpdev -l > ${OUTDIR}/sysdumpdev_l 2>> ${OUTDIR}/sysdumpdev_l
  sysdumpdev -e > ${OUTDIR}/sysdumpdev_e 2>> ${OUTDIR}/sysdumpdev_e



  # netcdstuff
  if [ -n "$(awk '{ if (( $1 == "netcd" ) && ( $3 != "inoperative" )) { print "RUN" }}' < ${OUTDIR}/lssrc_a)" ]; then
    lssrc -ls netcd >> ${OUTDIR}/lssrc_ls_netcd 2>> ${OUTDIR}/lssrc_ls_netcd
    check_exist_bin netcdctrl
    if [ ${?} -eq 0 ]; then
      netcdctrl -t dns -e hosts -a > ${OUTDIR}/netcdctrl_t_dns_e_hosts 2>> ${OUTDIR}/netcdctrl_t_dns_e_hosts
    fi
  fi
}

validate_sshd_config()
{
  for conf in \
    /etc/openssh/sshd_config /etc/ssh/sshd_config \
    /etc/ssh/sshd2_config /etc/ssh2/sshd_config \
    /etc/ssh2/sshd2_config /etc/sshd_config \
    /etc/sshd2_config /usr/local/etc/sshd_config /usr/local/etc/sshd2_config
  do
    if [ -f "${conf}" ]; then
      echo "INFO : Checking ${conf}..."
      awk '{ 
        x = tolower($1);
        if ( x == "logingracetime" ) { if (( $2 > 120 )||( $2 == 0 )) { print "WARNING : SSHD_CONFIG : LoginGraceTime not between 120 & 1"; }
        } else if ( x == "maxstartups" )  { if ( $2 > 100 ) { print "WARNING : SSHD_CONFIG : MaxStartups gratter than 100"; }
        } else if ( x == "maxauthtries" ) { if ( $2 > 5 ) { print "WARNING : SSHD_CONFIG : MaxAuthTries gratter than 5"; }
        } else if ( x == "keyregenerationinterval" ) { if (( $2 > 3600 )||( $2 == 0 )) { print "WARNING : SSHD_CONFIG : KeyRegenerationInterval not between 3600 & 1"; }
        } else if ( x == "acceptenv" ) {  print "WARNING : SSHD_CONFIG : AcceptEnv should not be allowed"; 
        } else {
          y = tolower($2);
          if (( x ~ /^printmotd$|^strictmodes$|^tcpkeepalive$|^permittty$/ )&&( y != "yes" )) {  print "WARNING : SSHD_CONFIG : "$1" defined as no";
          } else if (( x ~ /^permituserenvironment$|^permitrootlogin$|^gatewayports$/ )&&( y != "no" )) {  print "WARNING : SSHD_CONFIG : "$1" defined as no";
          } else if (( x == "loglevel" )&&( y == "debug" )){ print "WARNING : SSHD_CONFIG : LogLevel defined as DEBUG"; }
        }
      }' < ${conf}
    fi
  done
}

get_snap()
{
  mkdir -p ${OUTDIR}/snap
  echo 'y' | snap -r >> ${OUTDIR}/snap/log 2>> ${OUTDIR}/snap/log
  if [ -x "/usr/lib/cluster/caa_snap" ]; then
    echo 'y' | snap -gGtnfLRc caa >> ${OUTDIR}/snap/log 2>> ${OUTDIR}/snap/log
  else
    echo 'y' | snap -gGtnfLRc  >> ${OUTDIR}/snap/log 2>> ${OUTDIR}/snap/log
  fi
  mv /tmp/ibmsupt/snap.pax* ${OUTDIR}/snap  >> ${OUTDIR}/snap/log 2>> ${OUTDIR}/snap/log
  echo 'y' | snap -r  >> ${OUTDIR}/snap/log 2>> ${OUTDIR}/snap/log
}

get_all()
{
  if [ "${GET_TRACE}" = "Y" -o "${GET_IPTRACE}" = "Y" ]; then
    if [ -n "`df -k "$(dirname ${OUTDIR})" | awk '{ if (( $3 ~ /[0-9]/ )&&( $3 < 2097152 )) print "OI"; }'`" ]; then
      echo "INFO: GENERAL : At least 2Gbytes is needed at $(dirname ${OUTDIR}) to run the checklist safely. ABORTING..."
      do_exit
    fi
  fi
  if [ "$(uname)" = "Linux" ]; then
    echo "ERROR: This script is meant for AIX/VIOS"
    do_exit
  fi
  if [ "${GETPERF}" = "Y" ]; then
    M=$(((COLL_SEC/60*3)+5))
    echo "Collecting data.... ( will take at least ${M} minutes )"
  else
    echo "Collecting data...."
  fi
  (
    cd ${OUTDIR}
    echo "BEGIN : $(date)"
    echo "INFO: GENERAL : Used parameters: ${CALLED_PARMS}"
    if [ "${GETPERF}" = "Y" ]; then
      echo "INFO : GENERAL : Performance collection step: ${COLL_SEC}"
    fi
    echo "INFO : STEP : ----------------------------------------------------------------------------------------"
    echo "INFO : STEP : Get general info..."
    get_generalinfo

    echo "INFO : STEP : ----------------------------------------------------------------------------------------"
    echo "INFO : STEP : Get Running proccess info..."
    get_processinfo

    echo "INFO : STEP : ----------------------------------------------------------------------------------------"
    echo "INFO : STEP : Get CPU / Memory info"
    ( get_cpu_meminfo ) &
    export CHIELDS="${CHIELDS} ${!}"

    echo "INFO : STEP : ----------------------------------------------------------------------------------------"
    echo "INFO : STEP : Get network config..."
    ( get_netinfo ) &
    export CHIELDS="${CHIELDS} ${!}"

    echo "INFO : STEP : ----------------------------------------------------------------------------------------"
    echo "INFO : STEP : Get LVM config..."
    get_lvminfo

    echo "INFO : STEP : ----------------------------------------------------------------------------------------"
    echo "INFO : STEP : Get disk config..."
    ( get_diskinfo ) &
    export CHIELDS="${CHIELDS} ${!}"

    echo "INFO : STEP : ----------------------------------------------------------------------------------------"
    echo "INFO : STEP : Get filesystem config..."
    get_fsinfo

    if [ "${GET_GPFS}" = "Y" ]; then
      echo "INFO : STEP : ----------------------------------------------------------------------------------------"
      echo "INFO : STEP : Get GPFS config..."
      get_gpfsinfo
    fi

    echo "INFO : STEP : ----------------------------------------------------------------------------------------"
    echo "INFO : STEP : Get VIO related info..."
    get_vioinfo

    if [ -d "/usr/es/sbin/cluster/utilities" -a "${GET_HACMP}" = "Y" ]; then
      echo "INFO : STEP : ----------------------------------------------------------------------------------------"
      echo "INFO : STEP : Get PowerHA related info..."
      get_hacmpinfo
    fi

    echo "INFO : STEP : ----------------------------------------------------------------------------------------"
    echo "INFO : STEP : Validate ssh config..."
    validate_sshd_config

    if [ "${USER_CHECK}" = "Y" ]; then
      echo "INFO : STEP : ----------------------------------------------------------------------------------------"
      echo "INFO : STEP : Validate user security settings..."
      ( validate_userinfo ) &
      export CHIELDS="${CHIELDS} ${!}"
    fi

    if [ "${FILE_CHECK}" = "Y" ]; then
      echo "INFO : STEP : ----------------------------------------------------------------------------------------"
      echo "INFO : STEP : Validate Filesystem permissions..."
      ( validate_permissions ) &
      export CHIELDS="${CHIELDS} ${!}"
    fi
    if [ "${GET_SNAP}" = "Y" ]; then
      echo "INFO : STEP : ----------------------------------------------------------------------------------------"
      echo "INFO : STEP : Get System snap..."
      get_snap
    fi
    echo "INFO : GENERAL : Waiting sub process: ${CHIELDS}"
    if [ -n "${TRUSTCHK_PID}" ]; then
      if [ -n "$( ps -ef | awk -v TRUSTCHK_PID="${TRUSTCHK_PID}" '{ if (( $2 == TRUSTCHK_PID )&&( $0 ~ /trustchk/ )) print "OI"; }')" ]; then
        sleep ${COLL_SEC}
        ps -ef | awk -v TRUSTCHK_PID="${TRUSTCHK_PID}" '{ if (( $2 == TRUSTCHK_PID )&&( $0 ~ /trustchk/ )) system("kill -15 "$2); }'
      fi
    fi

    # Wait for other chields ( ugly but works )
    W=1
    while [ W -eq 1 ]
    do
      F=0
      ps -ef | while read A B C
      do
        for i in ${CHIELDS}
        do
          if [ "${B}" = "${i}" ]; then
            export F=1
          fi
        done
      done
      if [ $(ps -ef | awk -v MY_PID="${MY_PID}" '{ if ( $3 == MY_PID ) c=c+1 ; } END { print c; }') -lt 3 -a ${F} -eq 0 ]; then
        export W=0
      else
        sleep 2
      fi
    done
    wait


  ) 2>> ${OUTDIR}/checklist_run.log >> ${OUTDIR}/checklist_run.log

  echo "INFO : STEP : Last Step called at $(date)" | tee -a ${OUTDIR}/checklist_run.log
  
  if [ -d "${OUTDIR}" -a "${REMOVE_CHECK}" = "N" ]; then
    cd ${OUTDIR}
    check_exist_bin gzip
    if [ ${?} -eq 0 ]; then
      tar -cpf - . | gzip -9c > ${DST_FILE}.gz
      echo "Current checklist saved on ${DST_FILE}.gz"
    else
      check_exist_bin compress
      if [ ${?} -eq 0 ]; then
        tar -cpf - . | compress -c > ${DST_FILE}.Z
        compress ${DST_FILE}
        echo "Current checklist saved on ${DST_FILE}.Z"
      else
        tar -cpf ${DST_FILE} .
        echo "Current checklist saved on ${DST_FILE}"
      fi
    fi
  fi
}

do_exit()
{
  if [ -n "${CHIELDS}" ]; then
    if [ "${GETPERF}" = "Y" ]; then
      if [ "${GET_IPTRACE}" = "Y" ]; then
        stopsrc -s iptrace > /dev/null 2>/dev/null
      fi
      trcstop > /dev/null 2> /dev/null
    fi
    
    kill -15 ${CHIELDS} > /dev/null 2> /dev/null
    sleep 5
    kill -9  ${CHIELDS} > /dev/null 2> /dev/null
  fi
      
  if [ -d "${OUTDIR}" ]; then
    cd /
    rm -rf ${OUTDIR} 2>> /dev/null >> /dev/null
  fi
  if [ "${REMOVE_CHECK}" = "Y" -a -f "${DST_FILE}" ]; then
    rm -f ${DST_FILE} 2>> /dev/null >> /dev/null
  fi
  exit 0
}


# Cleanup on exit
trap do_exit SIGINT SIGHUP SIGKILL SIGPIPE SIGTERM


checklist_help()
{
  echo "checklist-aix.ksh -g [-G|-h][-s|-S|-T|-f|-u|-r|-i|-M|-t|-P] | { [-c] <oldfile> }"
  echo "                   -h This help message"
  echo "                   -g Create a new checklist"
  echo "                   -s Get a snap along with the checklist"
  echo "                   -f Process file permissions ( follow itcs104 )"
  echo "                   -u Process user account setup ( follow itcs104 )"
  echo "                   -r Remove checklist after completed"
  echo "                   -G Collect performance related information"
  echo "                   -M Skip GPFS information"
  echo "                   -S Skip svmon processing"
  echo "                   -T Skip trustchk processing"
  echo "                   -t Collect trace/tprof/hpmstat data"
  echo "                   -H Skip PowerHA information"
  echo "                   -i Collect an iptrace report ( require -G )"
  echo "                   -P Get only hdiskpower status ( when powermt detected )"
  echo "                   -c <oldfile> compare the actual config with a older checklist"
}

args=`getopt GfuiSgTtMsrhHc: ${*}`
if [ ${?} -ne 0 -o ${#} -lt 1 ]; then
  checklist_help
  exit 1
fi
set -- $args
for parm
do
  case "${parm}" in
    -g) shift ; export GET_CHECKLIST="Y" ;;
    -h) shift ; checklist_help ; do_exit ;;
    -r) shift ; export REMOVE_CHECK="Y" ;;
    -s) shift ; export GET_SNAP="Y" ;;
    -f) shift ; export FILE_CHECK="Y" ;;
    -u) shift ; export USER_CHECK="Y" ;;
    -S) shift ; export GET_SVMON="N" ;;
    -T) shift ; export GET_TRUSTCHK="N" ;;
    -t) shift ; export GET_TRACE="Y" ;;
    -M) shift ; export GET_GPFS="N" ;;
    -P) shift ; export GET_HACMP="N" ;;
    -c) shift ; echo "Not implemented" ;;
    -i) shift ; export GET_IPTRACE="Y" ;;
    -G) shift ; export GETPERF="Y" ;;
    -P) shift ; export SKIPDISK="Y" ;; 
  esac
done
if [ "${GET_CHECKLIST}" = "Y" ]; then
  get_all
fi
do_exit
