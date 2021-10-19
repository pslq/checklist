select
  to_char(FIRST_TIME,'yyyy-mm-dd  hh:MM'),
  inst_id,
  count(*)
from
  gv$log_history
group by to_char(FIRST_TIME,'yyyy-mm-dd  hh:MM'),inst_id
order by 1,2
