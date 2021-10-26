select
  hash_value||decode(child_number, 0, '', '/'||child_number) sql_hash,
  sql_text
from gv$sql
where
      child_number= 0
  and sql_id = 'PQ_SQLID'
