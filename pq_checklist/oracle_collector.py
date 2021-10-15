#!/opt/freeware/bin/python3

# All imports used
from .Stats_Parser import StatsParser
from .cache import pq_cache
from . import avg_list, debug_post_msg, pq_round_number
from ast import literal_eval
import importlib, datetime, os.path, time


# echo "select 1 from dual; " | su - oracle -c "export ORACLE_SID=tasy21 ; export ORACLE_HOME=/oracle/database/dbhome_1 ;  /oracle/database/dbhome_1/bin/sqlplus / as sysdba @/tmp/login.sql"

class collector() :
  def __init__(self, logger = None, ansible_module = None, config = None, bos_data = None) :
    '''
    Get performance and health metrics from oracle database instances
    '''
    self.logger         = logger
    self.ansible_module = ansible_module
    self.config         = config
    self.conn_type      = self.config['ORACLE']['conn_type'].strip().lower()
    self.remote_conns   = None
    self.bos_data       = bos_data
    self.query_dir      = os.path.join(os.path.dirname(os.path.abspath(__file__)),"oracle")
    self.nodename       = os.uname().nodename

    self.ora_users_to_ignore = literal_eval(config['ORACLE']['ora_users_to_ignore']) if 'ora_users_to_ignore' in config['ORACLE'] else []
    self.check_statistics_days = int(config['ORACLE']['check_statistics_days']) if 'check_statistics_days' in config['ORACLE'] else -1

    self.monitor_sample = 200
    self.queries = [ "ve_temp_usage.sql", "ve_active_sessions.sql", "ve_cons_per_user.sql",
                     "ve_with_work.sql",  "ve_wait_event.sql", 've_instance_info.sql',   've_users_with_objets.sql',
                     "ve_wait_hist.sql", "ve_database_info.sql", "ve_tablespace_usage.sql", "ve_table_frag.sql",
                     've_indexes.sql', 've_stats_history.sql' ]

    # helper to avoid convert the list to a string that will be used within Oracle multiple times
    __PQ_NOTOWNERS_str__ = str(self.ora_users_to_ignore).replace('[','').replace(']','')

    self.query_replacements = { 've_wait_event.sql' : [ [ 'PQ_SECONDS_MONITOR', self.config['LOOP']['interval'].strip() ] ],
                                've_wait_hist.sql'  : [ [ 'PQ_SECONDS_MONITOR', self.config['LOOP']['interval'].strip() ] ],
                                've_indexes.sql'    : [ [ 'PQ_NOTOWNERS', __PQ_NOTOWNERS_str__ ]],
                                've_table_frag.sql' : [ [ 'PQ_NOTOWNERS', __PQ_NOTOWNERS_str__ ]],
                                've_stats_history.sql' : [ [ 'PQ_NOTOWNERS', __PQ_NOTOWNERS_str__ ]]
                              }

    self.query_result_sequence = {
        've_table_frag.sql' : ( 'owner', 'table_name', 'table_size', 'actual_size', 'wasted_space', 'pct_reclaimable' ),
        've_tablespace_usage.sql' : ( 'tablespace', 'total', 'total_physical_cap', 'free', 'free_pct' ),
        've_temp_usage.sql' : ( 'tablespace', 'usage' ),
        've_with_work.sql' : ( 'usr', 'inst_id', 'sid', 'pct', 'runtime', 'hash_value', 'sql_id', 'sqltext'),
        've_indexes.sql' : ( 'owner','index_name','index_type','table_owner','table_name','table_type','compression','degree','generated','visibility' ),
        've_stats_history.sql' : ( 'owner', 'table_name', 'stats_update_time', 'modification_time' )
    }


    self.query_cache_results = pq_cache(logger = self.logger)

    self.__remote_connections__ = [ ]
    self.only_on_localhost = False

    if self.conn_type != "none" :
      self.conn_data      = {}
      for conf_key in ('ora_user', 'ora_sid', 'ora_home', 'ora_pass', 'ora_dsn', 'ora_logon', 'ora_role' ) :
        if conf_key in config['ORACLE'] :
          self.conn_data[conf_key] = literal_eval(config['ORACLE'][conf_key])
        else :
          self.conn_data[conf_key] = None
      if isinstance(self.conn_data['ora_home'],list) :
        self.oracle_bin = [ '%s/bin/sqlplus'%v for v in self.conn_data['ora_home'] ]
      else :
        self.oracle_bin = None
    else :
      self.conn_data,self.oracle_bin = None, None
      debug_post_msg(self.logger,'No connection method defined')
    if isinstance(self.conn_data['ora_dsn'], list) and \
        self.conn_type == 'remote' and \
          len(self.conn_data['ora_user']) == \
          len(self.conn_data['ora_pass']) == \
          len(self.conn_data['ora_dsn']) == \
          len(self.conn_data['ora_role']) > 0 :
      self.__remote_connections__ = [ None for i in range(len(self.conn_data['ora_user'])) ]
      self.remote_connectall()
      self.only_on_localhost = True

    return(None)

#######################################################################################################################
  def remote_connectall(self) :
    if importlib.util.find_spec('cx_Oracle') :
      for i in range(len(self.conn_data['ora_user'])) :
        self.remote_connect(i)
    else :
      debug_post_msg(self.logger,'Oracle python module not found')
    return(None)


#######################################################################################################################
  def remote_connect(self,position:int) :
    '''
    Stablish a connection to a remote database

    Parameters :
      position -> Connection position within the configuration ( think as a list )

    Returns :
      Send back a database connection if ok, otherwise None
    '''
    ret = None
    import cx_Oracle
    try :
      self.__remote_connections__[position] = cx_Oracle.connect(user=self.conn_data['ora_user'][position],
                                                        password=self.conn_data['ora_pass'][position],
                                                        dsn=self.conn_data['ora_dsn'][position],
                                                        mode=self.conn_data['ora_role'][position], encoding="UTF-8")
      ret = self.__remote_connections__[position]
    except Exception as e :
      debug_post_msg(self.logger,'Oracle client error connecting to position %d : %s'%(position,str(e)))
    return(ret)

#######################################################################################################################
  def remote_closeall(self) :
    '''
    Close all connections
    '''
    for i in self.remote_conns :
      if i :
        i.close()
    return(None)
#######################################################################################################################
  def remote_close(self, position:int) :
    '''
    Close connection on a specific position
    '''
    if len(self.__remote_connections__) >= position :
      if self.__remote_connections__[position] :
        self.__remote_connections__[position].close()
    return(None)

#######################################################################################################################
  def write_ret_into_sqlfile(self,output_dir:str,ret_obj:dict, mode:str='w+') -> bool :
    '''
    Write a group of queries into it's sqlfiles

    Parameters :
      output_dir -> directory into the local system that will hold all files ( one per database )
      ret_obj    -> object to be written
      mode       -> write mode to be passed when opening the file ( see open() )

    Returns : bool -> [True,False]
    '''
    ret = True
    if len(output_dir) > 0 :
      for con_seq,data in ret_obj.items() :
        db_name = self.database_name(con_seq)
        for stat,cmds in data.items() :
          try :
            with open(os.path.join(output_dir,'%s_%s.sql'%(db_name,stat)), mode) as fptr :
              for cmd in cmds :
                try :
                  fptr.write('%s;\n'%cmd)
                except Exception as e :
                  debug_post_msg(self.logger,'Error writting sqlfile : %s'%str(e), raise_type=Exception)
          except Exception as e :
            debug_post_msg(self.logger,'Error writting sqlfile : %s'%str(e), raise_type=Exception)
      else :
        debug_post_msg(self.logger,'No output_dir defined')
        ret = False
    return(ret)

#######################################################################################################################
  def load_sqlfile(self, query_file:str, notdefined:bool=False, specific_replacements:list=[]) -> str:
    '''
    Load and parse sqlfiles
    '''
    # Replace strings if any replacement defined
    query = ''
    tgt = None

    # Load query file
    if query_file in self.queries :
      tgt = os.path.join(self.query_dir,query_file)
    elif notdefined :
      tgt = query_file

    if tgt :
      try :
        with open(tgt, 'r') as fptr :
          query = fptr.read()
      except Exception as e :
        debug_post_msg(self.logger,'Error loading sqlfile : %s'%str(e), raise_type=Exception)

    # Replace strings if any replacement defined
    replacements = specific_replacements
    if query_file in self.query_replacements.keys() :
      replacements += self.query_replacements[query_file]

    for r in replacements :
      query = query.replace(r[0],r[1])

    return(query)


#######################################################################################################################
  def __get_cache__(self, query_id:str, expires:int=10, when_empty=None) :
    '''
    Store object into cache, if object is older than what is defined into expires,
    returns the value defined in when_empty

    Parameters :
      query_id :str -> Object to be stored ( usually a dict )
      expires  :int -> amount of seconds that will consider the object valid
      when_empty : obj -> what to report when nothing in cache or expired object

    Returns :
      object
    '''
    ret = when_empty
    cur_time = time.time()
    cache_dt = self.query_cache_results[query_id]
    if cache_dt :
      if cache_dt[0] - cur_time < expires :
        ret = cache_dt[1]
    return(ret)

#######################################################################################################################
  def __add_cache__(self, query_id:str, data) :
    '''
    Store data referenced by query_id into cache
    '''
    return(self.query_cache_results.add(query_id, ( time.time(), data ), overwrite_value=True))

#######################################################################################################################
  def __standard_query__(self,query_id:str, from_cache:bool = True, expires:int=10) -> dict:
    '''
    Process a query_id, return it's data in a dict format and store into cache
    '''
    ret = {}
    tmp_ret = self.__get_cache__(query_id, expires=expires)
    if tmp_ret and from_cache :
      ret = tmp_ret
    else :
      for con_seq, row in self.get_remote_query(query_id) :
        dct = {}
        for p,k in enumerate(self.query_result_sequence[query_id]) :
          dct[k] = row[p]
        try :
          ret[con_seq].append(dct)
        except :
          ret[con_seq] = [ dct ]
      self.__add_cache__(query_id,ret)
    return(ret)

#######################################################################################################################
  def database_name(self,con_seq:int) :
    '''
    Function to get database name tied to a specific connection
    '''
    databases = [ i for i in self.ve_database_info()[con_seq].keys() ]
    if len(set(databases)) > 1 :
      debug_post_msg(self.logger,'More than 01 database for connection %d, something odd is happening: %s'%(con_seq,str(databases)))
      return(databases)
    else :
      return(databases[-1])

#######################################################################################################################
  def get_latest_measurements(self, debug=False, update_from_system:bool = True) :

    ret = []
    current_time = datetime.datetime.utcnow().isoformat()
    active_sessions = self.ve_active_sessions()      # OK
    temp_usage = self.__standard_query__('ve_temp_usage.sql') # OK
    object_count = self.ve_user_object_count()       # OK
    wait_events = self.ve_wait_events()              # OK
    queries_with_pending_work = self.ve_with_work()  # OK

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
          'fields' : { 'total': pq_round_number(tbs['total']), 'total_physical_cap' : pq_round_number(tbs['total_physical_cap']),
                       'free' : pq_round_number(tbs['free']), 'free_pct' :  pq_round_number(tbs['free_pct']) },
          'time' : current_time })


    # Measure longops
    for con_seq, longops in queries_with_pending_work.items() :
      me = {}
      database_name = self.database_name(con_seq)
      for lgop in longops :
        srv,inst,usr = lgop['server'], lgop['inst_name'], lgop['user']

        ret.append({'measurement' : 'oracle_longops',
          'tags' : { 'database' : database_name, 'server' : server, 'instance' : instance, 'user' : user },
          'fields' : { 'hash_value' : lgop['hash_value'], 'sql_id' : lgop['sql_id']  },
          'time' : current_time })

    # Measure wait events
    for con_seq, events in wait_events.items() :
      for event in events :
        ret.append({'measurement' : 'oracle_wait_events',
          'tags' : { 'server' : event['server'] , 'instance' : event['inst_name'], 'event' : event['event'] },
          'fields' : { 'count' : event['count'] },
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
    return([])


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

      if len(output_dir) > 0 :
        self.write_ret_into_sqlfile(output_dir,ret,mode='w+')

    else :
      ret['__none__'] = {}
      for tbs in tables :
        try :
          ret['__none__'][tbs[0]][tbs[1]] = __make_list__(tbs[0],op,tbs[1],estimate_percent,max_parallel)
        except :
          ret['__none__'][tbs[0]] = { tbs[1] : __make_list__(tbs[0],op,tbs[1],estimate_percent,max_parallel) }
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
        to_stats.append([table_data['owner'],table_data['table_name']])

        to_add = [ 'alter table %s.%s enable row movement'%(table_data['owner'],table_data['table_name']), \
                   'alter table %s.%s shrink space cascade'%(table_data['owner'],table_data['table_name']), \
                   'alter table %s.%s deallocate unused space'%(table_data['owner'],table_data['table_name']) ]
        ret[con]['pre_stats'] += to_add
        ret[con]['pos_stats'] += [ 'ALTER TABLE %s.%s DISABLE ROW MOVEMENT'%(table_data['owner'],table_data['table_name']) ]

      for tables in self.build_stats_script(-1, tables=to_stats, max_parallel=max_parallel, estimate_percent=estimate_percent)['__none__'].values() :
        for cmds in tables.values() :
          ret[con]['stats'] += cmds



    if len(output_dir) > 0 :
      self.write_ret_into_sqlfile(output_dir,ret,mode='w+')

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

    for con_seq,con_data in with_work.items() :
      for data in con_data :
        dct = {
            'server' : instance_info[con_seq][con_data['inst_id']]['hostname'],
            'inst_name' : instance_info[con_seq][con_data['inst_id']]['name'],
            'user' : con_data['usr'],              'session_id' : con_data['sid'],
            'pct_completed' : con_data['pct'],     'runtime' : con_data['runtime'],
            'hash_value' : con_data['hash_value'], 'sql_id' : con_data['sql_id'],
            'sqltext' : con_data['sqltext'] }
        try :
          ret[con_seq].append(dct)
        except :
          ret[con_seq] = [ dct ]

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


#######################################################################################################################
  def get_remote_query(self,query_file:str='', connection_retry_count:int = 2, strip_strings:bool=True) -> tuple :
    '''
    Load one of the query files listed at self.queries and return it's result in a list for each connectio
      stablished within the class

    Parameters:
        query_file : str -> query file to be loaded ( the query file must be present at self.queries before use )
        connection_retry_count : int -> Amount of times try to reconnect to the remote database
          in order to execute the query
        strip_strings : bool -> [True,False] Oracle  has a weird behavior of put spaces at end end beging of the string,
                        this will strip them out

    Returns:
      tuple with results
        1st element is the connection position ( relative to self.remote_conns)
        2nd element is a row with data
    '''
    conn_error, conn_ok = [], []
    outer_retry_count:int = 0

    for attempts in range(connection_retry_count) :
      for position in range(len(self.__remote_connections__)) :
        if position in conn_error :
          self.remote_close(position)
          if self.remote_connect(position) :
            conn_error.pop(position)
        if position not in conn_error and self.__remote_connections__[position] :
          with self.__remote_connections__[position].cursor() as cur :
            try :
              cur.execute(self.load_sqlfile(query_file))
              inner_retry_count:int = 0
              while True :
                try :
                  if inner_retry_count < self.monitor_sample :
                    for row in cur.fetchmany(self.monitor_sample) :
                      try :
                        if not strip_strings :
                          yield((position, row ))
                        else :
                          yield((position, [ i.strip() if isinstance(i,str) else i for i in row ] ))
                      except :
                        break
                    else :
                      inner_retry_count += 1
                  else :
                    break
                except :
                  break
              conn_ok.append(position)
            except :
              conn_error.append(position)
      if len(conn_error) > 0 :
        conn_error = list(set(conn_error))
      else :
        break

#######################################################################################################################
