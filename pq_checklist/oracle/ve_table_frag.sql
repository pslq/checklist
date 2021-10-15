select
  owner,table_name,round((blocks*8),2) "size (kb)" ,
  round((num_rows*avg_row_len/1024),2) "actual_data (kb)",
  (round((blocks*8),2) - round((num_rows*avg_row_len/1024),2)) "wasted_space (kb)",
  ((round((blocks * 8), 2) - round((num_rows * avg_row_len / 1024), 2)) / round((blocks * 8), 2)) * 100 - 10 "reclaimable space % "
from dba_tables
where (round((blocks*8),2) > round((num_rows*avg_row_len/1024),2)) and owner not in ( PQ_NOTOWNERS )
order by 6 desc 
