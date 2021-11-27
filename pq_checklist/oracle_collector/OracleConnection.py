from .. import debug_post_msg, load_file
from ..cache import pq_cache
import importlib, datetime, os.path, time, os, json
from ast import literal_eval

import multiprocessing as mp


def __pq_connection_queue_handler__(dsn,user,password,mode,encoding,retry_count,input_queue,output_queue) :
  import cx_Oracle
  conn = None
  ret = 0

  if input_queue and output_queue :
    try :
      conn = cx_Oracle.connect(user=user,password=password, dsn=dsn, mode=mode, encoding=encoding)
      while True :
        output_data = (None,None,None)

        cmd = input_queue.get()
        if not cmd :
          break
        else :
          try :
            if cmd[0] == 'close' :
              if conn :
                conn.close()
            if cmd[0] == 'query' : # ( operation, sql_query, max_rows_to_return )
              all_done = False
              ret_rows = []
              all_rows = True
              for _ in range(retry_count) :
                if not all_done :
                  try :
                    if not conn.ping() :
                      with conn.cursor() as cur :
                        try :
                          for p,row in enumerate(cur.execute(cmd[1])) :
                            if p < cmd[2]:
                              ret_rows.append([ i.strip() if isinstance(i,str) else i for i in row ])
                            else :
                              all_rows = False
                              break
                          all_done = True
                          break
                        except Exception as e :
                          debug_post_msg(None, 'Oracle Error when executing cursor for %s : %s'%(dsn,e), screen_only=True)
                          debug_post_msg(None, 'Oracle query being executed %s'%(cmd[1]), screen_only=True)
                          if conn :
                            conn.close()
                          conn = cx_Oracle.connect(user=user,password=password, dsn=dsn, mode=mode, encoding=encoding)
                    else :
                      if conn :
                        conn.close()
                      conn = cx_Oracle.connect(user=user,password=password, dsn=dsn, mode=mode, encoding=encoding)
                  except Exception as e :
                    debug_post_msg(None, 'Oracle Error for %s : %s'%(dsn,e), screen_only=True)
                    if conn :
                      conn.close()
                    conn = cx_Oracle.connect(user=user,password=password, dsn=dsn, mode=mode, encoding=encoding)
              output_data = (ret_rows,all_rows,all_done)
          except Exception as e :
            debug_post_msg(None, 'Oracle error on command loop %s : %s'%(dsn,e), screen_only=True)
            ret = 254
            break
        output_queue.put(output_data)
      if conn :
        conn.close()
        ret = 0
    except Exception as e :
      debug_post_msg(None, 'Oracle error opening initial connection for %s : %s'%(dsn,e), screen_only=True)
      ret = 255
  return(ret)


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


    self.queries = [ "ve_temp_usage.sql", "ve_active_sessions.sql", "ve_cons_per_user.sql", 've_users_with_objets.sql',
                     "ve_with_work.sql",  "ve_session_wait_hist.sql", 've_instance_info.sql',
                     "ve_wait_hist.sql", "ve_database_info.sql", "ve_tablespace_usage.sql", "ve_table_frag.sql",
                     've_indexes.sql', 've_stats_history.sql', 've_log.sql', 've_logfile.sql', 've_loghist.sql',
                     've_sql_top_200.sql', 've_sql_monitor.sql', 've_system_wait_class.sql', 've_osstat.sql',
                     've_sum_datafile.sql', 've_instance_recovery.sql', 've_object_type_size.sql', 've_open_cursor.sql',
                     've_asm_dg.sql', 've_asm_disk_stat.sql' ]


    # helper to avoid convert the list to a string that will be used within Oracle multiple times
    __PQ_NOTOWNERS_str__ = str(self.ora_users_to_ignore).replace('[','').replace(']','')
    __PQ_SECONDS_MONITOR__ = self.config['LOOP']['interval'].strip()

    self.query_replacements = { 've_session_wait_hist.sql' : [ [ 'PQ_SECONDS_MONITOR', __PQ_SECONDS_MONITOR__ ] ],
                                've_wait_hist.sql'         : [ [ 'PQ_SECONDS_MONITOR', __PQ_SECONDS_MONITOR__ ] ],
                                've_indexes.sql'           : [ [ 'PQ_NOTOWNERS',       __PQ_NOTOWNERS_str__ ]],
                                've_table_frag.sql'        : [ [ 'PQ_NOTOWNERS',       __PQ_NOTOWNERS_str__ ]],
                                've_object_type_size.sql'  : [ [ 'PQ_NOTOWNERS',       __PQ_NOTOWNERS_str__ ]],
                                've_stats_history.sql'     : [ [ 'PQ_NOTOWNERS',    __PQ_NOTOWNERS_str__ ]]
                              }

    self.query_result_sequence = {
        've_table_frag.sql'        : ( 'owner', 'table_name', 'table_size', 'actual_size',
                                       'wasted_space', 'pct_reclaimable' ),
        've_tablespace_usage.sql'  : ( 'tablespace', 'total', 'total_physical_cap', 'free', 'free_pct' ),
        've_temp_usage.sql'        : ( 'tablespace', 'usage' ),
        've_with_work.sql'         : ( 'usr', 'inst_id', 'sid', 'pct', 'runtime', 'hash_value', 'sql_id', 'sqltext'),
        've_indexes.sql'           : ( 'owner', 'index_name', 'index_type', 'table_owner', 'table_name',
                                       'table_type','compression', 'degree', 'generated', 'visibility' ),
        've_stats_history.sql'     : ( 'owner', 'table_name', 'stats_update_time', 'modification_time' ),
        've_log.sql'               : ( 'inst_id', 'group', 'thread', 'sequence', 'bytes', 'blocksize',
                                       'members', 'status', 'first_time', 'next_time' ),
        've_logfile.sql'           : ( 'inst_id', 'group', 'status', 'type', 'member', 'is_recovery_dest_file' ),
        've_loghist.sql'           : ( 'char_datetime', 'inst_id', 'count' ),
        've_sql_top_200.sql'       : ( 'sql_id', 'tot_time' ),
        've_sql_monitor.sql'       : ( 'status', 'username', 'sid', 'module', 'service_name', 'sql_id', 'tot_time' ),
        've_session_wait_hist.sql' : ( 'inst_id', 'event', 'wait_class', 'count' ),
        've_system_wait_class.sql' : ( 'inst_id', 'wait_class', 'total_waits', 'time_waited', 'total_waits_fg',
                                       'time_waited_fg' ),
        've_wait_hist.sql'         : ( 'inst_id', 'sql_id', 'session_id', 'user', 'module', 'program', 'machine',
                                       'session_state', 'time_waited', 'count', 'event', 'pga_allocated',
                                       'temp_space_allocated' ),
        've_database_info.sql'     : ( 'inst_id', 'name', 'log_mode', 'controlfile_type', 'open_resetlogs', 'open_mode',
                                       'protection_mode', 'protection_level', 'remote_archive', 'database_role',
                                       'platform_id', 'platform_name'),
        've_users_with_objets.sql' : ( 'owner','status','count' ),
        've_instance_info.sql'     : ( 'id', 'number', 'name', 'hostname', 'status', 'parallel', 'thread', 'archiver',
                                       'log_switch', 'logins', 'state', 'edition', 'type' ),
        've_active_sessions.sql'   : ( 'user', 'status', 'lockwait', 'cmd', 'session_id', 'serial', 'inst_id',
                                       'hash_value', 'sql_id', 'sqltext' ),
        've_osstat.sql'            : ( 'inst_id', 'stat_name', 'value', 'cumulative', 'comments' ),
        've_sum_datafile.sql'      : ( 'dbsize' ),
        've_object_type_size.sql'  : ( 'segment_type', 'size' ),
        've_open_cursor.sql'       : ( 'parameter', 'size', 'usage' ),
        've_asm_dg.sql'            : ( 'inst_id', 'dgname', 'state', 'redundancy_level', 'sector_size', 'block_size',
                                       'allocation_unit_size', 'compatibility', 'database_compatibility', 'dg_size',
                                       'dg_used_size', 'dg_free_size' ),
        've_asm_disk_stat.sql'     : ( 'grp_number', 'dg_name', 'path', 'disk_size', 'free_disk_space' )

    }


    self.query_cache_results = pq_cache(logger = self.logger, qlen=64)

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
    else :
      self.__remote_connections__ = [ ]

    return(None)

  #######################################################################################################################
  def remote_closeall(self) :
    '''
    Close all connections
    '''
    for i in self.__remote_connections__ :
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
        if 'conn' in self.__remote_connections__[position] :
          self.__remote_connections__[position]['in'].put(['close',None])
          self.__remote_connections__[position]['in'].join()
          self.__remote_connections__[position]['conn'].join()
          self.__remote_connections__[position]['conn'].terminate()
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
      dct = { 'in' : mp.Queue(), 'out' : mp.Queue(), 'conn' : None }
      l_proc = mp.Process(target=__pq_connection_queue_handler__, args=(
        self.conn_data['ora_dsn'][position],self.conn_data['ora_user'][position],
        self.conn_data['ora_pass'][position],self.conn_data['ora_role'][position],"UTF-8",3,dct['in'],dct['out'],))
      dct['conn'] = l_proc
      dct['conn'].start()

      self.__remote_connections__[position] = dct
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
  def load_sqlfile(self, query_file:str, notdefined:bool=False, specific_replacements:list=[]) -> str:
    '''
    Load and parse sqlfiles
    '''
    tgt = None
    if query_file in self.queries :
      tgt = os.path.join(self.query_dir,query_file)
    elif notdefined :
      tgt = query_file

    # Replace strings if any replacement defined
    replacements = specific_replacements
    if query_file in self.query_replacements.keys() :
      replacements += self.query_replacements[query_file]

    return(load_file(self.logger,tgt,replacements))

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
                            query_string:str='', specific_pos = -1, as_dict:bool=True, rows_limit:int=10000, \
                            from_cache:bool = True, expires:int=10) -> tuple :
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
        as_dict : yield query results as a dict
        rows_limit : maximum amount of rows to return

    Returns:
      dict { position : { data : [dct,row], all_rows : bool, all_done : bool} }
       position   : the connection position ( relative to self.remote_conns)
       [dct,row]  : either a dict or a tuple with data
       all_rows   : If all rows will be returned or if the data stream will be breach after rows_limit is reached
       all_done   : If the data fetch process finished OK
    '''
    ret = None
    query_to_execue = ''
    if len(query_file) > 0 :
      query_to_execue = self.load_sqlfile(query_file)
      if as_dict and not query_file in self.query_result_sequence :
        as_dict = False
      if from_cache :
        ret = self.__get_cache__(query_file, expires=expires)
    elif len(query_string) > 0 :
      query_to_execue = query_string

    if len(query_to_execue) > 0 and not ret :
      ret = {}
      ranged_val = range(len(self.__remote_connections__)) if int(specific_pos) == -1 else [ specific_pos ]
      for position in ranged_val :
        if self.__remote_connections__[position] :
          if 'conn' in self.__remote_connections__[position] :
            self.__remote_connections__[position]['in'].put(('query',query_to_execue,rows_limit))
      for position in reversed(ranged_val) :
        ret[position] = { 'data' : [], 'all_done' : True, 'all_rows' : True }
        out_data = self.__remote_connections__[position]['out'].get()
        for row in out_data[0] :
          if as_dict :
            ret[position]['data'].append({ k:v for k,v in zip(self.query_result_sequence[query_file],row) })
          else :
            ret[position]['data'].append(row)
          ret[position]['all_done'],ret[position]['all_rows'] = out_data[2],out_data[1]

    if len(query_file) > 0 and from_cache :
      self.__add_cache__(query_file,ret)
    return(ret)

#######################################################################################################################
