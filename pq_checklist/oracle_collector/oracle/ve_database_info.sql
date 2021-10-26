select
  inst_id, name, log_mode, controlfile_type, open_resetlogs,
  open_mode, protection_mode, protection_level, remote_archive,
  database_role, platform_id, platform_name
from gv$database
