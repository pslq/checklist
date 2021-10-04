#!/opt/freeware/bin/python3

# All imports used
from .Stats_Parser import StatsParser
from . import avg_list
import datetime
from ast import literal_eval
import importlib
import os.path

# echo "select 1 from dual; " | su - oracle -c "export ORACLE_SID=tasy21 ; export ORACLE_HOME=/oracle/database/dbhome_1 ;  /oracle/database/dbhome_1/bin/sqlplus / as sysdba @/tmp/login.sql"

class collector() :
  def __init__(self, logger = None, ansible_module = None, config = None) :
    '''
    Get performance and health metrics from oracle database instances
    '''
    self.logger         = logger
    self.ansible_module = ansible_module
    self.config         = config
    self.conn_type      = self.config['ORACLE']['conn_type'].strip().lower()
    self.remote_conns   = None
    self.query_dir      = os.path.join(os.path.dirname(os.path.abspath(__file__)),"oracle")
    self.monitor_sample = 200
    self.queries = [ "ve_query_wait.sql",  "ve_temp_usage.sql",  "ve_active_sessions.sql", "ve_cons_per_user.sql", "ve_with_work.sql", "ve_wait_event.sql" ]
    self.query_replacements = { 've_wait_event.sql' : ( 'PQ_SECONDS_MONITOR', self.config['LOOP']['interval'].strip() ) }

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
        self.conn_type == 'remote' and len(self.conn_data['ora_user']) == len(self.conn_data['ora_pass']) == len(self.conn_data['ora_dsn']) == len(self.conn_data['ora_role']) > 0 :
      if importlib.util.find_spec('cx_Oracle') :
        import cx_Oracle
        self.remote_conns = [ cx_Oracle.connect(user=usr,password=pas,dsn=dsn, mode=role, encoding="UTF-8") for usr,pas,dsn,role in zip(self.conn_data['ora_user'], self.conn_data['ora_pass'], self.conn_data['ora_dsn'], self.conn_data['ora_role']) ]
      else :
        debug_post_msg(self.logger,'Oracle python module not found')

    return(None)


  def get_remote_query(self,query_file:str='') -> tuple :
    '''
    Load one of the query files listed at self.queries and return it's result in a list for each connection stablished within the class

    Parameters:
        query_file : str -> query file to be loaded ( the query file must be present at self.queries before use )

    Returns:
      tuple with results
        1st element is the connection position ( relative to self.remote_conns)
        2nd element is a row with data
    '''
    query = ''
    # Load query file
    if query_file in self.queries :
      with open(os.path.join(self.query_dir,query_file), 'r') as fptr :
        query = fptr.read()

    # Replace strings if any replacement defined
    if query_file in self.query_replacements :
      for r in self.query_replacements[query_file] :
        query = query.replace(r[0],r[1])

    for p,conn in enumerate(self.remote_conns) :
      with conn.cursor() as cur :
        cur.execute(query)
        try_count = 0
        while True :
          try :
            if try_count < self.monitor_sample :
              for row in cur.fetchmany(self.monitor_sample) :
                try :
                  yield((p, row ))
                except :
                  break
              else :
                try_count += 1
            else :
              break
          except :
            break

#######################################################################################################################
#######################################################################################################################
