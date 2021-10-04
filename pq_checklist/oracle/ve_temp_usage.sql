select
  ss.tablespace_name,sum((ss.used_blocks*ts.blocksize))/1024/1024 mb
from
  gv$sort_segment ss, sys.ts$ ts
where
  ss.tablespace_name = ts.name
group by ss.tablespace_name
