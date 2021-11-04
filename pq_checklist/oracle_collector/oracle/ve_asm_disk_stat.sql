select
  a.GROUP_NUMBER as GRP_NUMBER,
  b.NAME as DG_NAME,
  a.PATH,
  a.TOTAL_MB/1024 AS DISK_SIZE_IN_GB,
  a.FREE_MB/1024 AS FREE_DISK_SPACE
from
  v$asm_disk_stat a, v$asm_diskgroup_stat b
where
  a.GROUP_NUMBER=b.GROUP_NUMBER
order by GRP_NUMBER
