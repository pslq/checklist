select
  case when username IS NULL THEN 'SYSTEM_BACKGROUND' else username END username,
  inst_id,
  count(*) as TOT
from
  gv$session
group by username,inst_id;

