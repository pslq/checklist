select
  INST_ID,
  GROUP#,
  STATUS,
  TYPE,
  MEMBER,
  IS_RECOVERY_DEST_FILE
from
  GV$LOGFILE
order by group#,inst_id
