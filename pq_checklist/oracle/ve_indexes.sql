select
  owner,index_name,index_type,table_owner,table_name,table_type,compression,DEGREE,GENERATED,VISIBILITY
from dba_indexes
where owner not in ( PQ_NOTOWNERS ) and TABLE_OWNER not in ( PQ_NOTOWNERS )

