select
  INSTANCE_NUMBER, SQL_ID, SESSION_ID, USERNAME, module, program, machine, SESSION_STATE,sum(time_waited), count(*) cnt , event,
  PGA_ALLOCATED, TEMP_SPACE_ALLOCATED
from DBA_HIST_ACTIVE_SESS_HISTORY,DBA_USERS
where time_waited > 0
and  session_state = 'WAITING'
and DBA_HIST_ACTIVE_SESS_HISTORY.user_id = DBA_USERS.user_id
and sample_time >= sysdate - interval 'PQ_SECONDS_MONITOR' second
group by INSTANCE_NUMBER,SESSION_ID,USERNAME,module,program,machine,SESSION_STATE,event,SQL_ID,PGA_ALLOCATED,TEMP_SPACE_ALLOCATED

