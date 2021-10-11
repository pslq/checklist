select owner,status,count(status) from dba_objects group by owner,status
