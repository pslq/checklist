select distinct 
  a.OWNER,
  a.TABLE_NAME,
  a.STATS_UPDATE_TIME,
  b.TIMESTAMP
from DBA_TAB_STATS_HISTORY a, DBA_TAB_MODIFICATIONS b
where
  a.owner not in ( PQ_NOTOWNERS ) and
  a.owner = b.table_owner and a.table_name = b.table_name
