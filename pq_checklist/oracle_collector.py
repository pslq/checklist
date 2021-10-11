#!/opt/freeware/bin/python3

# All imports used
from .Stats_Parser import StatsParser
from .cache import pq_cache
from . import avg_list, debug_post_msg
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

    self.monitor_sample = 200
    self.queries = [ "ve_temp_usage.sql", "ve_active_sessions.sql", "ve_cons_per_user.sql",
                     "ve_with_work.sql",  "ve_wait_event.sql", 've_instance_info.sql',   've_users_with_objets.sql',
                     "ve_wait_hist.sql", "ve_database_info.sql" ]
    self.query_replacements = { 've_wait_event.sql' : [ [ 'PQ_SECONDS_MONITOR', self.config['LOOP']['interval'].strip() ] ],
                                've_wait_hist.sql'  : [ [ 'PQ_SECONDS_MONITOR', self.config['LOOP']['interval'].strip() ] ]
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
  def __get_cache__(self, query_id) :
    ret = None
    cur_time = time.time()
    cache_dt = self.query_cache_results[query_id]
    if cache_dt :
      if cache_dt['ts'] - cur_time < 10 :
        ret = cache_dt['result']
    return(ret)

#######################################################################################################################
  def __add_cache__(self, query_id, data) :
    cur_time = time.time()
    return(self.query_cache_results.add(query_id, { 'ts' : cur_time, 'result' : data }, overwrite_value=True))

#######################################################################################################################
  def get_latest_measurements(self, debug=False, update_from_system:bool = True) :

    ret = []
    current_time = datetime.datetime.utcnow().isoformat()
    active_sessions = self.ve_active_sessions()      # OK
    temp_usage = self.ve_temp_usage()                # OK
    object_count = self.ve_user_object_count()       # OK
    wait_events = self.ve_wait_events()              # OK
    queries_with_pending_work = self.ve_with_work()  #

    # Helper functions ( not exposed outside
    def __database_name__(con_seq) :
      '''
      Function to get database name tied to a specific connection
      '''
      databases = [ i for i in self.ve_database_info()[con_seq].keys() ]
      if len(set(databases)) > 1 :
        debug_post_msg(self.logger,'More than 01 database for connection %d, something odd is happening: %s'%(con_seq,str(databases)))
        return(databases)
      else :
        return(databases[-1])


    # Measure wait events
    for con_seq, events in wait_events.items() :
      for event in events :
        ret.append({'measurement' : 'oracle_wait_events',
          'tags' : { 'server' : event['server'] , 'instance' : event['inst_name'], 'event' : event['event'] },
          'fields' : { 'count' : event['count'] },
          'time' : current_time })




    # Measure temporary tablespace usage
    for con_seq, tablespaces in temp_usage.items() :
      database = __database_name__(con_seq)
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
      target_db = __database_name__(con_seq)
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
  def ve_temp_usage(self, from_cache:bool = True) :
    '''
    Get temporary tablespace usage from connected databases
    '''
    ret = {}
    tmp_ret = self.__get_cache__('ve_temp_usage.sql')
    if tmp_ret and from_cache :
      ret = tmp_ret
    else :
      for con_seq, ( tablespace, space_usage ) in self.get_remote_query('ve_temp_usage.sql') :
        dct = { 'tablespace' : tablespace, 'usage' : space_usage }
        try :
          ret[con_seq].append(dct)
        except :
          ret[con_seq] = [ dct ]
      self.__add_cache__('ve_temp_usage.sql', ret)
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
    tmp_ret = self.__get_cache__('ve_with_work.sql')
    if tmp_ret and from_cache :
      ret = tmp_ret
    else :
      instance_info = self.ve_instance_info()
      for con_seq, ( usr, inst_id, sid, pct, runtime, hash_value, sql_id, sqltext ) \
          in self.get_remote_query('ve_with_work.sql') :
        hostname, inst_name = instance_info[con_seq][inst_id]['hostname'], instance_info[con_seq][inst_id]['name']

        dct = { 'server' : hostname, 'inst_name' : inst_name,
            'user' : usr, 'session_id' : sid, 'pct_completed' : pct, 'runtime' : runtime, 'hash_value' : hash_value,
            'sql_id' : sql_id, 'sqltext' : sqltext }

        try :
          ret[con_seq].append(dct)
        except :
          ret[con_seq] = [ dct ]

      self.__add_cache__('ve_with_work.sql', ret)

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
    query = ''
    conn_error, conn_ok = [], []
    outer_retry_count:int = 0
    # Load query file
    if query_file in self.queries :
      with open(os.path.join(self.query_dir,query_file), 'r') as fptr :
        query = fptr.read()

    # Replace strings if any replacement defined
    if query_file in self.query_replacements.keys() :
      for r in self.query_replacements[query_file] :
        query = query.replace(r[0],r[1])

    for attempts in range(connection_retry_count) :
      for position in range(len(self.__remote_connections__)) :
        if position in conn_error :
          self.remote_close(position)
          if self.remote_connect(position) :
            conn_error.pop(position)
        if position not in conn_error and self.__remote_connections__[position] :
          with self.__remote_connections__[position].cursor() as cur :
            try :
              cur.execute(query)
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
