#!/opt/freeware/bin/python3

# All imports used
from .. import avg_list, debug_post_msg, pq_round_number
from ast import literal_eval
import importlib, datetime, os.path, time, os, json
from .OracleConnection import OracleConnection


class collector(OracleConnection) :
  def __init__(self, logger = None, config = None, bos_data = None) :
    '''
    Get performance and health metrics from oracle database instances
    '''
    super().__init__( config = config, logger = logger)
    self.bos_data = bos_data

    return(None)

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


#######################################################################################################################
  def health_check(self,update_from_system:bool = True) -> list :
    '''
    '''
    ret = []

    # Measure logswitches
    if self.log_switches_hour_alert > 0 :
      databases = {}
      for ldb,ldb_info in self.ve_log().items() :
        databases[ldb] = {}
        for instance,instance_data in ldb_info.items() :
          databases[ldb][instance] = {}
          for lswitch in instance_data['log_switches'] :
            lkh = lswitch['datetime'] - datetime.timedelta(minutes=lswitch['datetime'].minute) # hour
            try :
              databases[ldb][instance][lkh] += lswitch['count']
            except :
              databases[ldb][instance][lkh] = lswitch['count']
      for db,data in databases.items() :
        for instance,dates in data.items() :
          for dt,cnt in dates.items() :
            if cnt > self.log_switches_hour_alert :
              ret.append('The instance %s of database %s switched logs %d times at : %s'%(instance,ldb,cnt,str(dt)))

    # Placeholder to store sql_ids
    sql_ids = {}
    fts_count = 0
    # Dump directory
    dst_dir = os.path.join(self.script_dumpdir,'dumped_queries')

    for con_seq, longops in self.ve_with_work().items() :
      database_name = self.database_name(con_seq)
      sql_ids[database_name] = []
      for lgop in longops :
        sql_ids[database_name].append(lgop['sql_id'])
      ids = list(set(sql_ids[database_name]))
      sql_ids[database_name] = ids
      if len(ids) > 0 :
        ret.append('The database %s has a total of %d longops happening, please check dumped queries'%(database_name,len(ids)))

    if self.dump_longops :
      try :
        os.mkdir(dst_dir)
      except :
        pass

      for con_seq,queries in sql_ids.items() :
        database_name = self.database_name(con_seq)
        for sql_id in queries :
          fts_count += 1 if self.ve_sqltxt(sql_id, con_seq, dst_dir=dst_dir, dump_only_if_fts=True)['has_fts'] else 0

    if self.dump_running_ids :
      # queries from monitor
      try :
        os.mkdir(dst_dir)
      except :
        pass

      for con_seq,data in self.ve_sql_monitor().items() :
        database_name = self.database_name(con_seq)
        for sql_id in data['top_queries'] :
          fts_count += 1 if self.ve_sqltxt(sql_id, con_seq, dst_dir=dst_dir, dump_only_if_fts=True)['has_fts'] else 0

    if fts_count > 0 :
      ret.append('Long queries detected using full table scan, please check %d'%fts_count)


    # Make degrag scripts:
    dst_dir = os.path.join(self.script_dumpdir,'stats_files')
    try :
      os.mkdir(dst_dir)
    except :
      pass
    self.build_defrag_script(reclaimable_treshold=50, max_parallel=4, estimate_percent=60, output_dir=dst_dir)
    self.build_stats_script(self.check_statistics_days, max_parallel=4, estimate_percent=60, output_dir=dst_dir, op='gather')

    return(ret)

#######################################################################################################################
  def ve_sqltxt(self,sql_id:str, position:int, dst_dir:str='', dump_only_if_fts:bool=True) -> dict :
    '''
    Fetch a SQL text from the database

    Returns :
      dict -> { 'hash_value' : '', 'sqltxt' : '', 'plan' : [] }
    '''
    ret = { 'hash_value' : '', 'sqltxt' : '', 'plan' : [], 'has_fts' : False }
    database_name = self.database_name(position)

    if len(dst_dir) > 0 :
      dst_plan = os.path.join(dst_dir,'%s_%s_plan.txt'%(database_name,sql_id))
      dst_txt = os.path.join(dst_dir,'%s_%s_txt.sql'%(database_name,sql_id))
      if os.path.exists(dst_plan) and os.path.exists(dst_txt) :
        return(ret)

    rpl = [ [ 'PQ_SQLID', sql_id ] ]
    query_str = self.load_sqlfile(os.path.join(self.query_dir,'ve_sqltxt.sql'),
                                  notdefined=True, specific_replacements=rpl)

    for _, row in self.get_remote_query('', query_string=query_str, specific_pos = position) :
      ret['hash_value'], ret['sqltxt']  = row[0], row[1]

    if len(ret['hash_value']) > 0 :
      rpl = [[ 'PQ_HASH_VALUE', ret['hash_value']]]
      query_str = self.load_sqlfile(os.path.join(self.query_dir,'ve_plan.sql'),
                                    notdefined=True, specific_replacements=rpl)
      for _, ( oid, parent_id, operation, object_name, byts, rows, cost ) \
          in self.get_remote_query('', query_string=query_str, specific_pos = position) :
        dct = { 'id' : oid, 'parent_id' : parent_id, 'operation' : operation, 'object_name' : object_name,
                'bytes' : byts, 'rows' : rows, 'cost' : cost }
        ret['plan'].append(dct)

    if len(dst_dir) > 0 :
      ret['has_fts'] = True if any([ True if "FULL" in l['operation'] else False for l in ret['plan'] ]) else False

      if dump_only_if_fts and ret['has_fts'] or ( not dump_only_if_fts ) :
        dst_plan = os.path.join(dst_dir,'%s_%s_plan.txt'%(database_name,sql_id))
        dst_txt = os.path.join(dst_dir,'%s_%s_txt.sql'%(database_name,sql_id))
        if not os.path.exists(dst_plan) :
          with open(dst_plan, 'a+') as fptr :
            json.dump(ret['plan'],fptr)
        if not os.path.exists(dst_txt)  :
          with open(dst_txt, 'a+') as fptr :
            fptr.writelines(ret['sqltxt'])

    return(ret)

#######################################################################################################################
  def build_stats_script(self, days:int, tables:list=[],  max_parallel:int=4, estimate_percent:int=60, \
                               op:str='gather',  output_dir:str="") -> list :
    '''
    Build gather statistcs scripts for a specific set of tables or for everything outside the exclude list

    Parameters :
      op : str -> Which kind of operation should be executed:
                  "gather" will generate a script for dbms_stats.GATHER_TABLE_STATS
                  "delete" will generate a script for dbms_stats.delete_table_stats
                  "both" will generate both

      estimate_percent : int ->  Estimate percent passed to GATHER_TABLE_STATS

      max_parallel     : int ->  Parallel degree limit considered for GATHER_TABLE_STATS

      tables           : list -> Instead of scan the databases for tables, will consider only tables passed within
                                 the list ( no DBA_TAB_STATS_HISTORY or DBA_TAB_MODIFICATIONS check is performed )
                                 list format [ [ table_owner:str, table_name:str ] ]

      days             : int ->  Amount of days to be considered, -1 to ignore days

      output_dir       : str -> Directory to store the built scripts ( not supported when tables are specified )

    Returns:
      dict { con : { table_owner : { table : [ commands ] } } }

      If tables were passes to the function, it will assume that connection instead of a number ( sequence ),
        it will be called __none__


    '''
    ret = {}
    delta = datetime.datetime.now() - datetime.timedelta(days=days)

    def __make_list__(owner,op,table,pct,parallel) :
      rt = []
      if op in [ 'delete', 'both' ] :
        rt.append("exec dbms_stats.delete_table_stats( ownname => '%s', TABNAME => '%s', cascade_indexes=> TRUE)"%(owner,table))
      if op in [ 'gather', 'both' ] :
        rt.append("exec dbms_stats.GATHER_TABLE_STATS( ownname => '%s', method_opt => 'for all columns size AUTO', estimate_percent=> %d, cascade=>TRUE, TABNAME => '%s', DEGREE=>%d)"%(owner,pct,table,parallel))
      return(rt)


    if len(tables) == 0 :
      for con_seq,con_data in  self.__standard_query__('ve_stats_history.sql', expires=60).items() :
        ret[con_seq] = {}
        for tbs in con_data  :
          if days != -1 or ( tbs['modification_time'] > tbs['stats_update_time'] < delta ) :
            to_add = __make_list__(tbs['owner'],op,tbs['table_name'],estimate_percent,max_parallel)
            try :
              ret[con_seq][tbs['owner']][tbs['table_name']] = to_add
            except :
              ret[con_seq][tbs['owner']] = { tbs['table_name'] : to_add }

    else :
      ret['__none__'] = {}
      for tbs in tables :
        try :
          ret['__none__'][tbs[0]][tbs[1]] = __make_list__(tbs[0],op,tbs[1],estimate_percent,max_parallel)
        except :
          ret['__none__'][tbs[0]] = { tbs[1] : __make_list__(tbs[0],op,tbs[1],estimate_percent,max_parallel) }

    if len(output_dir) > 0 :
      for con_seq, usr_data in ret.items() :
        db_name = self.database_name(con_seq)
        for usr, tables in usr_data.items() :
          for table, script in tables.items() :
            output_file = os.path.join(output_dir, '%s_%s_%s_stats.sql'%(db_name,usr,table))
            if not os.path.exists(output_file) :
              with open(output_file, 'w+') as fptr :
                for c in script :
                  if len(c) > 0 :
                    fptr.write('%s;\n'%c)
    return(ret)



#######################################################################################################################
  def build_defrag_script(self, reclaimable_treshold:int=50, from_cache:bool=True, max_parallel:int=4, estimate_percent:int=60, output_dir:str="") -> dict :
    '''
    Build a script file to execute table defrag and index rebuild
    '''
    ret = {}

    all_indexes = self.__standard_query__('ve_indexes.sql', expires=60, from_cache=from_cache)

    for con,con_data in self.ve_table_fragmentation(reclaimable_treshold=reclaimable_treshold,from_cache=from_cache).items() :
      ret[con] = { 'stats' : [], 'pre_stats' : [], 'pos_stats': [] }
      indexes_con = {}

      # Organize all indexes on this database
      for v in all_indexes[con] :
        try :
          indexes_con[v['owner']][v['table_name']].append((v['index_name'], v['degree']))
        except :
          try :
            indexes_con[v['owner']][v['table_name']] = [ (v['index_name'], v['degree']) ]
          except :
            indexes_con[v['owner']] = { v['table_name'] : [ (v['index_name'], v['degree']) ] }

      # Build command dict for this database
      to_stats = []
      for table_data in con_data :
        try :
          for idx in indexes_con[table_data['owner']][table_data['table_name']] :
            rpl = [ [ 'INDEX_OWNER.INDEX_NAME', '%s.%s'%(table_data['owner'], idx[0]) ],
                    [ 'MAX_PARALLEL' , '%s'%max_parallel ],
                    [ 'STD_PARALLEL' , '%s'%idx[1] ]
                  ]
            pre_stats = self.load_sqlfile(os.path.join(self.query_dir,'alter_idx_pre_stats.sql'),
                                          notdefined=True, specific_replacements=rpl).split('\n')
            ret[con]['pre_stats'] += pre_stats
        except :
          # No index on on this table ( weird )
          pass
        # Append table to the list of tables that will go through stats gather
        to_stats.append([table_data['owner'],table_data['table_name']])

        # Inject actions prior statistics
        rpl = [ [ 'TABLE_OWNER.TABLE_NAME', '%s.%s'%(table_data['owner'],table_data['table_name']) ]]
        ret[con]['pre_stats'] += self.load_sqlfile(os.path.join(self.query_dir,'alter_tbl_pre_stats.sql'),
                                                   notdefined=True, specific_replacements=rpl).split('\n')

        # Inject actions after statistics
        ret[con]['pos_stats'] += self.load_sqlfile(os.path.join(self.query_dir,'alter_tbl_pos_stats.sql'),
                                                   notdefined=True, specific_replacements=rpl).split('\n')

      for tables in self.build_stats_script(-1, tables=to_stats, max_parallel=max_parallel, estimate_percent=estimate_percent)['__none__'].values() :
        for cmds in tables.values() :
          ret[con]['stats'] += cmds

    if len(output_dir) > 0 :
      for con_seq,stats in ret.items() :
        db_name = self.database_name(con_seq)
        for st in [ 'stats', 'pre_stats', 'pos_stats'] :
          output_file = os.path.join(output_dir, '%s_%s.sql'%(db_name,st))
          if not os.path.exists(output_file) :
            with open(output_file, 'w+') as fptr :
              for c in stats[st] :
                if len(c) > 0 :
                  fptr.write('%s;\n'%c)

    return(ret)


#######################################################################################################################
  def ve_table_fragmentation(self, specific_user:str = '', reclaimable_treshold:int=50, from_cache:bool=True) -> dict:
    '''
    Get Fragmentation level from all tables within database
    '''
    ret = {}

    for con_seq, con_data in self.__standard_query__('ve_table_frag.sql', expires=60).items() :
      for table in con_data :
        if table['owner'] not in self.ora_users_to_ignore and table['pct_reclaimable'] >= reclaimable_treshold :
          try :
            ret[con_seq].append(table)
          except :
            ret[con_seq] = [ table ]
    return(ret)

#######################################################################################################################
  def ve_sql_monitor(self, from_cache:bool=True) :
    '''
    Get top queries running on the system

    Returns:
        dict { con_seq : { 'top_queries' : [],
                           'current'     : [ { 'status', 'username', 'sid', 'module',
                                               'service_name', 'sql_id', 'tot_time' } ]
                         }
             }
    '''
    ret = {}
    top = self.__standard_query__('ve_sql_top_200.sql', from_cache=from_cache)
    query_mon = self.__standard_query__('ve_sql_monitor.sql', from_cache=from_cache)

    for con_seq,con_data in top.items() :
      if con_seq not in ret:
        ret[con_seq] = { 'top_queries' : [], 'current' : [] }
      for data in con_data :
        if data['sql_id'] not in ret[con_seq]['top_queries'] :
          ret[con_seq]['top_queries'].append(data['sql_id'])

    for con_seq,con_data in query_mon.items() :
      if con_seq not in ret :
        ret[con_seq] = { 'top_queries' : [] }
      ret[con_seq]['current'] = con_data

    return(ret)


#######################################################################################################################
  def ve_with_work(self, from_cache:bool=True) :
    '''
    Get queries with longops and it's current statu within the database

    Returns :
      dict ->
        { }
    '''
    ret = {}
    with_work = self.__standard_query__('ve_with_work.sql', from_cache=from_cache)
    instance_info = self.ve_instance_info(from_cache=from_cache)

    for con_seq,con_data in  self.__standard_query__('ve_with_work.sql', from_cache=from_cache).items() :
      for data in con_data :
        dct = {
            'server' : instance_info[con_seq][data['inst_id']]['hostname'],
            'inst_name' : instance_info[con_seq][data['inst_id']]['name'],
            'user' : data['usr'],              'session_id' : data['sid'],
            'pct_completed' : data['pct'],     'runtime' : data['runtime'],
            'hash_value' : data['hash_value'], 'sql_id' : data['sql_id'],
            'sqltext' : data['sqltext'] }
        try :
          ret[con_seq].append(dct)
        except :
          ret[con_seq] = [ dct ]

    return(ret)

#######################################################################################################################
  def ve_log(self, from_cache:bool=True) -> dict:
    '''
    '''
    ret = {}
    ve_log     = self.__standard_query__('ve_log.sql', from_cache=from_cache)
    instance_info = self.ve_instance_info(from_cache=from_cache)

    # Get log switches per minute
    for con_seq,con_data in self.__standard_query__('ve_loghist.sql', from_cache=from_cache).items() :
      database_name = self.database_name(con_seq)
      ret[database_name] = { }
      for l_entry in con_data :
        inst_name = instance_info[con_seq][l_entry['inst_id']]['name']
        dct = {
            'datetime' : datetime.datetime.strptime(l_entry['char_datetime'], '%Y-%m-%d  %H:%M'),
            'count' : l_entry['count'] }
        try :
          ret[database_name][inst_name]['log_switches'].append(dct)
        except :
          try :
            ret[database_name][inst_name]['log_switches'] = [ dct ]
          except :
            ret[database_name][inst_name] = { 'log_switches' : [ dct ] }

    for con_seq,con_data in self.__standard_query__('ve_logfile.sql', from_cache=from_cache).items() :
      database_name = self.database_name(con_seq)
      for l_entry in con_data :
        inst_name = instance_info[con_seq][l_entry['inst_id']]['name']
        dct = { }
        for k in [ 'group', 'status', 'type', 'member', 'is_recovery_dest_file' ] :
          dct[k] = l_entry[k]
        try :
          ret[database_name][inst_name]['logfiles'].append(dct)
        except :
          try :
            ret[database_name][inst_name]['logfiles'] = [ dct ]
          except :
            ret[database_name][inst_name] = { 'logfiles' : [ dct ] }

    return(ret)

#######################################################################################################################
  def ve_active_sessions(self, from_cache:bool=True) :
    '''
    Get active sessions along with information about what its being done
    '''
    ret = {}
    tmp_ret = self.__get_cache__('ve_active_sessions.sql')
    if tmp_ret and from_cache:
      ret = tmp_ret
    else :
      instance_info = self.ve_instance_info()
      for con_seq, ( usr, status, lockwait, cmd, sid, serial, inst_id, hash_value, sql_id, sqltext ) \
          in self.get_remote_query('ve_active_sessions.sql') :
        hostname, inst_name = instance_info[con_seq][inst_id]['hostname'], instance_info[con_seq][inst_id]['name']

        dct = { 'server' : hostname, 'inst_name' : inst_name,
            'user' :usr, 'status' : status, 'lockwait' : lockwait, 'cmd' : cmd, 'session_id' : sid, 'serial' : serial,
            'hash_value' : hash_value, 'sql_id' : sql_id, 'sqltext' : sqltext }

        try :
          try :
            w = [ True if i['inst_name'] == inst_name and i['session_id'] == sid else False for i in ret[con_seq]]
            if not any(w) :
              ret[con_seq].append(dct)
          except :
            ret[con_seq].append(dct)
        except :
          ret[con_seq] = [ dct ]

      self.__add_cache__('ve_active_sessions.sql', ret)

    return(ret)


#######################################################################################################################
  def ve_instance_info(self, from_cache = True) -> dict:
    '''
    Get a dict with information about all instances

    Returns:
      dict ->
        { con_sequence : instance_id { **data } }
    '''
    ret = {}
    tmp_ret = self.__get_cache__('ve_instance_info.sql')

    if tmp_ret and from_cache:
      ret = tmp_ret
    else :
      for data in self.get_remote_query('ve_instance_info.sql') :
        rw = data[1]
        try :
          ret[data[0]][rw[0]] = { 'id' :rw[0], 'number' :rw[1], 'name' :rw[2], 'hostname' :rw[3], 'status' :rw[4],
                                  'parallel' :rw[5], 'thread' :rw[6], 'archiver' :rw[7], 'log_switch' :rw[8],
                                  'logins' :rw[9], 'state' :rw[10], 'edition' :rw[11], 'type' :rw[12], }
        except :
          ret[data[0]]= { rw[0] : { 'id' :rw[0], 'number' :rw[1], 'name' :rw[2], 'hostname' :rw[3], 'status' :rw[4],
                                  'parallel' :rw[5], 'thread' :rw[6], 'archiver' :rw[7], 'log_switch' :rw[8],
                                  'logins' :rw[9], 'state' :rw[10], 'edition' :rw[11], 'type' :rw[12], }}

      self.__add_cache__('ve_instance_info.sql', ret)
    return(ret)

#######################################################################################################################
  def ve_database_info(self, from_cache=True) :
    ret = {}
    tmp_ret = self.__get_cache__('ve_database_info.sql')

    if tmp_ret and from_cache:
      ret = tmp_ret
    else :
      for con_seq, ( inst_id, name, log_mode, controlfile_type, open_resetlogs, open_mode, protection_mode, \
                     protection_level, remote_archive, database_role, platform_id, platform_name ) \
        in self.get_remote_query('ve_database_info.sql') :

        try :
          ret[con_seq][name]['inst_id'].append(inst_id)
          ret[con_seq][name]['log_mode'].append(log_mode)
          ret[con_seq][name]['controlfile_type'].append(controlfile_type)
          ret[con_seq][name]['open_resetlogs'].append(open_resetlogs)
          ret[con_seq][name]['open_mode'].append(open_mode)
          ret[con_seq][name]['protection_mode'].append(protection_mode)
          ret[con_seq][name]['protection_level'].append(protection_level)
          ret[con_seq][name]['remote_archive'].append(remote_archive)
          ret[con_seq][name]['database_role'].append(database_role)
          ret[con_seq][name]['platform_id'].append(platform_id)
          ret[con_seq][name]['platform_name'].append(platform_name)
        except :
          if con_seq not in ret :
            ret[con_seq] = {}
          ret[con_seq][name] = { 'inst_id' : [ inst_id ], 'log_mode' : [ log_mode ],
                                 'controlfile_type' : [ controlfile_type ],
                                 'open_resetlogs' : [ open_resetlogs ] , 'open_mode' : [ open_mode ],
                                 'protection_mode' : [ protection_mode ], 'protection_level' : [ protection_level ],
                                 'remote_archive,' : [ remote_archive ], 'platform_id,' : [ platform_id ],
                                 'platform_name' : [ platform_name ] }
      self.__add_cache__('ve_database_info.sql', ret)
    return(ret)

#######################################################################################################################
  def ve_user_object_count(self, from_cache=True) :
    '''
    Get a dict with a list of amount of valid,invalid objects per user

    Returns:
      dict ->
      { con_sequence : [ { owner, status, count } ]
    '''
    ret = {}
    tmp_ret = self.__get_cache__('ve_users_with_objets.sql')
    if tmp_ret and from_cache:
      ret = tmp_ret
    else :
      for con_seq, ( owner,status,count ) in self.get_remote_query('ve_users_with_objets.sql') :
        try :
          ret[con_seq][owner][status] = count
        except :
          try :
            ret[con_seq][owner] = { status : count }
          except :
            ret[con_seq] = { owner : { status : count } }

      self.__add_cache__('ve_users_with_objets.sql', ret)
    return(ret)


#######################################################################################################################
  def ve_wait_hist(self, from_cache=True) -> dict :
    '''
    '''
    ret = {}
    tmp_ret = self.__get_cache__('ve_wait_hist.sql')
    if tmp_ret and from_cache:
      ret = tmp_ret
    else :
      instance_info = self.ve_instance_info()
      for con_seq, ( inst_id, SQL_ID, SESSION_ID, USERNAME, module, program, machine, SESSION_STATE,time_waited, cnt, \
          event, PGA_ALLOCATED, TEMP_SPACE_ALLOCATED ) \
        in self.get_remote_query('ve_wait_hist.sql') :

        hostname, inst_name   = instance_info[con_seq][inst_id]['hostname'], instance_info[con_seq][inst_id]['name']
        dct = { 'server' : hostname, 'inst_name' : inst_name,
            'SQL_ID' : SQL_ID, 'SESSION_ID' : SESSION_ID, 'USERNAME' : USERNAME, 'module' : module,
            'program' : program, 'machine' : machine, 'SESSION_STATE' : SESSION_STATE, 'time_waited' : time_waited ,
            'cnt' : cnt, 'event': event, 'PGA_ALLOCATED' : PGA_ALLOCATED, 'TEMP_SPACE_ALLOCATED' : TEMP_SPACE_ALLOCATED }
        try :
          ret[con_seq].append(dct)
        except :
          ret[con_seq] = [ dct ]
      self.__add_cache__('ve_wait_hist.sql', ret)
    return(ret)

#######################################################################################################################
  def ve_wait_events(self, from_cache=True) -> dict:
    '''
    Get current wait events on the database instances

    Returns :
      dict ->
        { con_sequence : [ { server,inst_name,event,event_class,count } ]
    '''
    ret = {}

    tmp_ret = self.__get_cache__('ve_wait_event.sql')
    if tmp_ret and from_cache:
      ret = tmp_ret
    else :
      instance_info = self.ve_instance_info()
      for evt in self.get_remote_query('ve_wait_event.sql') :
        con_seq, (inst_id, event, WAIT_CLASS, sample_count) = evt
        hostname   = instance_info[con_seq][inst_id]['hostname']
        inst_name  = instance_info[con_seq][inst_id]['name']
        dct = {'server' : hostname, 'inst_name' : inst_name, 'event' : event, 'class' : WAIT_CLASS,
               'count' : sample_count}
        try :
          ret[con_seq].append(dct)
        except :
          ret[con_seq] = [ dct ]

      self.__add_cache__('ve_wait_event.sql', ret)
    return(ret)
