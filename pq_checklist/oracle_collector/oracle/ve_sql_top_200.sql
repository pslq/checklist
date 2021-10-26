select * from (select sql_id, elapsed_time*executions tot_time from gv$sql order by 2 desc) where rownum < 200
