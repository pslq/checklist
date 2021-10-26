import cx_Oracle
from .. import debug_post_msg
from ..cache import pq_cache
import importlib, datetime, os.path, time, os, json
from ast import literal_eval


class OracleConnection() :
  def __init__(self, logger = None, config = None) :
    '''
    Get performance and health metrics from oracle database instances
    '''

    self.logger         = logger
    self.config         = config
    self.conn_type      = self.config['ORACLE']['conn_type'].strip().lower()
    self.remote_conns   = None
    self.query_dir      = os.path.join(os.path.dirname(os.path.abspath(__file__)),"oracle")
    self.nodename       = os.uname().nodename
    self.only_on_localhost = False
    self.monitor_sample = 200
    self.ora_users_to_ignore        = literal_eval(config['ORACLE']['ora_users_to_ignore']) if 'ora_users_to_ignore' in config['ORACLE'] else []
    self.check_statistics_days      = int(config['ORACLE']['check_statistics_days']) if 'check_statistics_days' in config['ORACLE'] else -1
    self.log_switches_hour_alert    = int(config['ORACLE']['log_switches_hour_alert']) if 'log_switches_hour_alert' in config['ORACLE'] else -1
    self.table_reclaimable_treshold = int(config['ORACLE']['table_reclaimable_treshold']) if 'table_reclaimable_treshold' in config['ORACLE'] else -1
    self.stats_max_parallel         = int(config['ORACLE']['stats_max_parallel']) if 'stats_max_parallel' in config['ORACLE'] else -1
    self.stats_estimate_percent     = int(config['ORACLE']['stats_estimate_percent']) if 'stats_estimate_percent' in config['ORACLE'] else -1

    try :
      self.dump_longops          = True if config['ORACLE']['dump_longops'].lower().strip() == 'true' else False
    except :
      self.dump_longops          = False
    try :
      self.dump_running_ids      = True if config['ORACLE']['dump_running_ids'].lower().strip() == 'true' else False
    except :
      self.dump_running_ids      = False

    self.script_dumpdir          = config['ORACLE']['script_dumpdir'].strip() if 'script_dumpdir' in config['ORACLE'] else ''


    self.queries = [ "ve_temp_usage.sql", "ve_active_sessions.sql", "ve_cons_per_user.sql",
                     "ve_with_work.sql",  "ve_wait_event.sql", 've_instance_info.sql',   've_users_with_objets.sql',
                     "ve_wait_hist.sql", "ve_database_info.sql", "ve_tablespace_usage.sql", "ve_table_frag.sql",
                     've_indexes.sql', 've_stats_history.sql', 've_log.sql', 've_logfile.sql', 've_loghist.sql',
                     've_sql_top_200.sql', 've_sql_monitor.sql' ]

    # helper to avoid convert the list to a string that will be used within Oracle multiple times
    __PQ_NOTOWNERS_str__ = str(self.ora_users_to_ignore).replace('[','').replace(']','')
    __PQ_SECONDS_MONITOR__ = self.config['LOOP']['interval'].strip()

    self.query_replacements = { 've_wait_event.sql' : [ [ 'PQ_SECONDS_MONITOR', __PQ_SECONDS_MONITOR__ ] ],
                                've_wait_hist.sql'  : [ [ 'PQ_SECONDS_MONITOR', __PQ_SECONDS_MONITOR__ ] ],
                                've_indexes.sql'    : [ [ 'PQ_NOTOWNERS',       __PQ_NOTOWNERS_str__ ]],
                                've_table_frag.sql' : [ [ 'PQ_NOTOWNERS',       __PQ_NOTOWNERS_str__ ]],
                                've_stats_history.sql' : [ [ 'PQ_NOTOWNERS',    __PQ_NOTOWNERS_str__ ]]
                              }

    self.query_result_sequence = {
        've_table_frag.sql'       : ( 'owner', 'table_name', 'table_size', 'actual_size',
                                      'wasted_space', 'pct_reclaimable' ),
        've_tablespace_usage.sql' : ( 'tablespace', 'total', 'total_physical_cap', 'free', 'free_pct' ),
        've_temp_usage.sql'       : ( 'tablespace', 'usage' ),
        've_with_work.sql'        : ( 'usr', 'inst_id', 'sid', 'pct', 'runtime', 'hash_value', 'sql_id', 'sqltext'),
        've_indexes.sql'          : ( 'owner', 'index_name', 'index_type', 'table_owner', 'table_name',
                                      'table_type','compression', 'degree', 'generated', 'visibility' ),
        've_stats_history.sql'    : ( 'owner', 'table_name', 'stats_update_time', 'modification_time' ),
        've_log.sql'              : ( 'inst_id', 'group', 'thread', 'sequence', 'bytes', 'blocksize',
                                      'members', 'status', 'first_time', 'next_time' ),
        've_logfile.sql'          : ( 'inst_id', 'group', 'status', 'type', 'member', 'is_recovery_dest_file' ),
        've_loghist.sql'          : ( 'char_datetime', 'inst_id', 'count' ),
        've_sql_top_200.sql'      : ( 'sql_id', 'tot_time' ),
        've_sql_monitor.sql'      : ( 'status', 'username', 'sid', 'module', 'service_name', 'sql_id', 'tot_time' )
    }


    self.query_cache_results = pq_cache(logger = self.logger)

    self.__remote_connections__ = [ ]

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
  def database_name(self,con_seq:int) :
    '''
    Function to get database name tied to a specific connection
    '''
    databases = [ i for i in self.ve_database_info()[con_seq].keys() ]
    if len(set(databases)) > 1 :
      debug_post_msg(self.logger,
                     'More than 01 database for connection %d, something odd is happening: %s'%(
                        con_seq,str(databases)))
      return(databases)
    else :
      return(databases[-1])


  #######################################################################################################################
  def get_remote_query(self,query_file:str='', connection_retry_count:int = 2, strip_strings:bool=True, \
      query_string:str='', specific_pos = -1) -> tuple :
    '''
    Load one of the query files listed at self.queries and return it's result in a list for each connectio
      stablished within the class

    Parameters:
        query_file : str -> query file to be loaded ( the query file must be present at self.queries before use )
        query_string : str -> if query_file is empty ( len = 0 ) query_string will be used instead
        connection_retry_count : int -> Amount of times try to reconnect to the remote database
          in order to execute the query
        strip_strings : bool -> [True,False] Oracle  has a weird behavior of put spaces at end end beging of the string,
                        this will strip them out
        specific_pos : execute query only on a specific connection

    Returns:
      tuple with results
        1st element is the connection position ( relative to self.remote_conns)
        2nd element is a row with data
    '''
    conn_error, conn_ok = [], []
    outer_retry_count:int = 0
    query_to_execue = ''
    if len(query_file) > 0 :
      query_to_execue = self.load_sqlfile(query_file)
    elif len(query_string) > 0 :
      query_to_execue = query_string

    if len(query_to_execue) > 0 :
      for attempts in range(connection_retry_count) :
        for position in range(len(self.__remote_connections__)) if int(specific_pos) > -1 else [ specific_pos ] :
          if position in conn_error :
            self.remote_close(position)
            if self.remote_connect(position) :
              conn_error.pop(position)
          if position not in conn_error and self.__remote_connections__[position] :
            with self.__remote_connections__[position].cursor() as cur :
              try :
                cur.execute(query_to_execue)
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
              except Exception as e :
                debug_post_msg(self.logger,'Error on connection %d : %s'%(position,e))
                conn_error.append(position)
        if len(conn_error) > 0 :
          conn_error = list(set(conn_error))
        else :
          break
  #######################################################################################################################



