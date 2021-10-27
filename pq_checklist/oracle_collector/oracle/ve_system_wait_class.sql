select
  inst_id, wait_class, total_waits, time_waited, total_waits_fg, time_waited_fg
from
  GV$SYSTEM_WAIT_CLASS
