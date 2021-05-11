#!/usr/bin/ksh
#####################################################################

# Global vars
export PATH="${PATH}:/usr/lpp/mmfs/bin:/usr/es/sbin/cluster/utilities:/usr/es/sbin/cluster/utilities:/usr/es/sbin/cluster/sbin"
export PATH="${PATH}:/usr/lib/ras:/usr/sbin/rsct/bin:/opt/NetApp/santools/bin:/usr/DynamicLinkManager/bin:/usr/es/sbin/cluster/diag:/usr/ios/cli"
export LANG="C"
export LC_NUMERIC="POSIX"


vmstat -Iwt 5 2 | awk -v BOOTINFOR="$(bootinfo -r)" \
  '{
     if ( $0 ~ /lcpu=/ )
     {
       split($3,v,"=");
       LCPU=v[2];
     }
     if ( $1 ~ /[0-9]/ )
     {
       steps = steps +1;
       run_kthread = $1 + run_kthread;
       block_kthread = $2 + block_kthread;
       raw_dev_thread = $3 + raw_dev_thread;
       amount_of_mem_pages = $4 + amount_of_mem_pages;
       free_mem_pages = $5 + free_mem_pages;
       free_pages = $10 + free_pages;
       scan_pages = $11 + scan_pages;
       user_cpu = $15 + user_cpu;
       sys_cpu  = $16 + sys_cpu;
       idle_cpu = $17 + idle_cpu;
       wait_cpu = $18 + wait_cpu;
     }
   } END {
     pkr=0;
     if ( steps <= 0 ) steps = 1;

     run_kthread         = run_kthread/steps;         user_cpu       = user_cpu/steps;
     sys_cpu             = sys_cpu/steps;             idle_cpu       = idle_cpu/steps;
     wait_cpu            = wait_cpu/steps;            run_kthread    = run_kthread/steps;
     scan_pages          = scan_pages/steps;          free_pages     = free_pages/steps;
     raw_dev_thread      = raw_dev_thread/steps;      block_kthread  = block_kthread/steps;
     amount_of_mem_pages = amount_of_mem_pages/steps; free_mem_pages = free_mem_pages/steps; free_pages = free_pages/steps;

     if ( scan_pages > 0 ) pkr = (scan_pages*5)-free_pages;


     printf("LCPU=%d KTHREADS_RUN=%f KTHREAD_BLOCK=%d SCAN_PAGES=%d PAGE_SCAN_RATIO=%f USER=%f SYS=%f WAIT=%f IDLE=%f\n", LCPU, run_kthread, block_kthread, SCAN_PAGES, pkr, user_cpu, sys_cpu, wait_cpu, idle_cpu);
   }' 



