import datetime
from .. import pq_round_number
#######################################################################################################################
def get_latest_measurements(self, debug=False, update_from_system:bool = True) :

  ret = []
  current_time = datetime.datetime.utcnow().isoformat()
  active_sessions = self.ve_active_sessions()      # OK
  temp_usage = self.__standard_query__('ve_temp_usage.sql') # OK
  object_count = self.ve_user_object_count()       # OK
  wait_events = self.ve_wait_events()              # OK
  queries_with_pending_work = self.ve_with_work()  # OK

  # Measure logswitches
  for ldb,ldb_info in self.ve_log().items() :
    for instance,instance_data in ldb_info.items() :
      for lswitch in instance_data['log_switches'] :
        lkh = lswitch['datetime'] - datetime.timedelta(minutes=lswitch['datetime'].minute) # hour
        lkm = lswitch['datetime'].isoformat()
        ret.append({
              'measurement' : 'oracle_logswitches',
              'tags' : { 'database' : ldb },
              'fields' : { instance : lswitch['count'] },
              'time' :  lkm })

  # Measure stale stats
  for con_seq,stat_info in self.build_stats_script(self.check_statistics_days).items() :
    database_name = self.database_name(con_seq)
    for user, tables in stat_info.items() :
      ret.append({
        'measurement' : 'oracle_stalestats',
        'tags' : { 'database' : database_name, 'user' : user },
        'fields' : { 'total': len(tables.keys()) },
        'time' : current_time })


  # Measure tablespace
  for con_seq, tbs_data in self.__standard_query__('ve_tablespace_usage.sql').items() :
    database_name = self.database_name(con_seq)
    for tbs in tbs_data :
      ret.append({
        'measurement' : 'oracle_tablespaces',
        'tags' : { 'database' : database_name, 'tablespace' : tbs['tablespace'] },
        'fields' : { 'total': pq_round_number(tbs['total']),
                     'total_physical_cap' : pq_round_number(tbs['total_physical_cap']),
                     'free' : pq_round_number(tbs['free']),
                     'free_pct' :  pq_round_number(tbs['free_pct']) },
        'time' : current_time })


  # Measure longops
  for con_seq, longops in queries_with_pending_work.items() :
    me = {}
    database_name = self.database_name(con_seq)
    for lgop in longops :
      srv,inst,usr = lgop['server'], lgop['inst_name'], lgop['user']

      ret.append({'measurement' : 'oracle_longops',
        'tags' : { 'database' : database_name, 'server' : srv, 'instance' : inst, 'user' : usr },
        'fields' : { 'hash_value' : lgop['hash_value'], 'sql_id' : lgop['sql_id']  },
        'time' : current_time })

  # Measure wait events
  for con_seq, events in wait_events.items() :
    for event in events :
      ret.append({'measurement' : 'oracle_wait_events',
        'tags' : { 'server' : event['server'] , 'instance' : event['inst_name'], 'event' : event['event'] },
        'fields' : { 'count' : event['count'] },
        'time' : current_time })

  # queries from monitor
  for con_seq,data in self.ve_sql_monitor().items() :
    database_name = self.database_name(con_seq)
    ret.append({'measurement' : 'oracle_running_queries',
        'tags' : { 'database' : database_name },
        'fields' : { 'total' : len(data['current']) },
        'time' : current_time })
    for queries in data['current'] :
      ret.append({'measurement' : 'oracle_sql_monitor',
        'tags' : { 'database' : database_name,     'status' : queries['status'], 'username' : queries['username'],
                   'module'   : queries['module'], 'service_name' : queries['service_name'] },
        'fields' : { 'sql_id' : queries['sql_id'], 'tot_time' : queries['tot_time'] },
        'time' : current_time })


  # Measure temporary tablespace usage
  for con_seq, tablespaces in temp_usage.items() :
    database = self.database_name(con_seq)
    for ts in tablespaces :
      ret.append({'measurement' : 'oracle_temp_tablespaces',
                  'tags' : { 'database' : database, 'tablespace' : ts['tablespace'] },
                  'fields' : { 'usage_in_mb' : ts['usage'] }, 'time' : current_time
                })


  # Measure active sessions
  for con_seq,sessions in active_sessions.items() :
    con_count = {}
    for sess in sessions :
      try :
        try :
          con_count[sess['server']][sess['inst_name']]['total_sessions'] += 1
          try :
            con_count[sess['server']][sess['inst_name']][sess['cmd']] += 1
          except :
            con_count[sess['server']][sess['inst_name']][sess['cmd']] = 1
        except :
          con_count[sess['server']][sess['inst_name']] = { 'total_sessions' : 1, sess['cmd'] : 1 }
      except :
        con_count[sess['server']] = { sess['inst_name'] : { 'total_sessions' : 1, sess['cmd'] : 1 } }

    for server,inst_data in con_count.items() :
      for instance, fields in inst_data.items() :
        ret.append({'measurement' : 'oracle_sessions',
                    'tags' : { 'host' : server, 'instance' : instance },
                    'fields' : fields, 'time' : current_time
                   })

  # Measure object per users
  for con_seq,obj_count in object_count.items() :
    target_db = self.database_name(con_seq)
    for user,objs in obj_count.items() :
      tmp_copy = objs
      for tp in ( 'VALID', 'INVALID' ) :
        if tp not in tmp_copy :
          tmp_copy[tp] = 0
      ret.append({'measurement' : 'oracle_objects',
                 'tags' : { 'database' : target_db, 'user' : user },
                 'fields' : tmp_copy, 'time' : current_time })

  return(ret)
