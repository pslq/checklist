#!/opt/freeware/bin/python3

# All imports used
from .. import avg_list, debug_post_msg, pq_round_number
from ast import literal_eval
import importlib, datetime, os.path, time, os, json
from .OracleConnection import OracleConnection
# Local functions
from ._get_latest_measurements import get_latest_measurements
from ._health_check import health_check


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
    return(get_latest_measurements(self, debug=debug, update_from_system=update_from_system))


#######################################################################################################################
  def health_check(self,update_from_system:bool = True) -> list :
    return(health_check(self,update_from_system=update_from_system))

#######################################################################################################################
  def ve_sqltxt(self,sql_id:str, position:int, dst_dir:str, dump_only_if_fts:bool, \
                     problem_plan_limit:int = 10000) -> dict :
    '''
    Fetch a SQL text from the database

    Returns :
      dict -> { 'hash_value' : '', 'sqltxt' : '', 'plan' : '' }
    '''
    ret = { 'hash_value' : '', 'sqltxt' : '', 'plan' : [], 'has_fts' : False,
            'problem_with_plan_analysis' : False, 'in_previous_report' : False }
    database_name = self.database_name(position)
    dst_plan = ''

    if len(dst_dir) > 0 :
      dst_plan = os.path.join(dst_dir,'%s_%s_plan.txt'%(database_name,sql_id))
      dst_txt = os.path.join(dst_dir,'%s_%s_txt.sql'%(database_name,sql_id))
      if os.path.exists(dst_plan) and os.path.exists(dst_txt) :
        ret['in_previous_report'] = True


    if not ret['in_previous_report'] :
      rpl = [ [ 'PQ_SQLID', sql_id ] ]
      query_str = self.load_sqlfile(os.path.join(self.query_dir,'ve_sqltxt.sql'),
                                    notdefined=True, specific_replacements=rpl)

      for _, dt in self.get_remote_query('', query_string=query_str, specific_pos = position, \
                                         from_cache=False, as_dict=False).items() :
        for row in dt['data'] :
          ret['hash_value'], ret['sqltxt']  = str(row[0]), row[1]

      if len(ret['hash_value']) > 0 :
        rpl = [[ 'PQ_HASH_VALUE', ret['hash_value']]]
        query_str = self.load_sqlfile(os.path.join(self.query_dir,'ve_plan.sql'),
                                      notdefined=True, specific_replacements=rpl)
        if len(dst_dir) > 0 :
          dst_plan = os.path.join(dst_dir,'%s_%s_plan.txt'%(database_name,sql_id))
          if not os.path.exists(dst_plan) :
            dst_plan_fptr = open(os.path.join(dst_dir,'%s_%s_plan.csv'%(database_name,sql_id)), 'a+')
            dst_plan_fptr.write('oid,parent_id,operation,object_name,byts,rows,cost\n')
          else :
            dst_plan_fptr = None
        else :
          dst_plan_fptr = None
        for _, dt in self.get_remote_query('', query_string=query_str, specific_pos = position, \
                                           as_dict=False, rows_limit=problem_plan_limit).items() :
          try :
            for ( oid, parent_id, operation, object_name, byts, rows, cost ) in dt['data'] :
              if "FULL" in operation :
                ret['has_fts'] = True
              if dst_plan_fptr :
                dst_plan_fptr.write(str(( oid, parent_id, operation, object_name, byts, rows, cost ))+'\n')
          except Exception as e :
            debug_post_msg("Error unpacking query: %s | returned data: %s"%(query_str,str(dt)))

          if 'all_rows' in dt :
            ret['problem_with_plan_analysis'] = True if not dt['all_rows'] else False

        if dst_plan_fptr :
          dst_plan_fptr.close()

        if dump_only_if_fts and ret['has_fts'] or ( not dump_only_if_fts ) or ret['problem_with_plan_analysis'] :
          dst_txt = os.path.join(dst_dir,'%s_%s_txt.sql'%(database_name,sql_id))
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
      for con_seq,con_data in  self.get_remote_query('ve_stats_history.sql', expires=60).items() :
        ret[con_seq] = {}
        for tbs in con_data['data']  :
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
  def build_defrag_script(self, reclaimable_treshold:int=50, from_cache:bool=True, max_parallel:int=4, \
                                estimate_percent:int=60, output_dir:str="") -> dict :
    '''
    Build a script file to execute table defrag and index rebuild
    '''
    ret = {}

    all_indexes = self.get_remote_query('ve_indexes.sql', expires=60, from_cache=from_cache)

    for con,con_data in self.ve_table_fragmentation(reclaimable_treshold=reclaimable_treshold,from_cache=from_cache).items() :
      ret[con] = { 'stats' : [], 'pre_stats' : [], 'pos_stats': [] }
      indexes_con = {}

      # Organize all indexes on this database
      for v in all_indexes[con]['data'] :
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

    for con_seq, con_data in self.get_remote_query('ve_table_frag.sql', expires=60, from_cache=from_cache).items() :
      for table in con_data['data'] :
        if table['owner'] not in self.ora_users_to_ignore and table['pct_reclaimable'] >= reclaimable_treshold :
          try :
            ret[con_seq].append(table)
          except :
            ret[con_seq] = [ table ]
    return(ret)

#######################################################################################################################
  def ve_sql_monitor(self, fields:list = [ 'top_queries', 'current' ], from_cache:bool=True) :
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
    top = self.get_remote_query('ve_sql_top_200.sql', from_cache=from_cache)
    query_mon = self.get_remote_query('ve_sql_monitor.sql', from_cache=from_cache)


    if 'top_queries' in fields :
      for con_seq,con_data in top.items() :
        ret[con_seq] = { 'top_queries' : [], 'current' : [] }
        for data in con_data['data'] :
          if data['sql_id'] not in ret[con_seq]['top_queries'] :
            ret[con_seq]['top_queries'].append(data['sql_id'])

    if 'current' in fields :
      for con_seq,con_data in query_mon.items() :
        if con_seq not in ret :
          ret[con_seq] = { 'top_queries' : [], 'current' : [] }
        ret[con_seq]['current'] = con_data['data']

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
    instance_info = self.ve_instance_info(from_cache=from_cache)

    for con_seq,con_data in  self.get_remote_query('ve_with_work.sql', from_cache=from_cache).items() :
      for data in con_data['data'] :
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
  def ve_log(self, fields:list = [ 'log_switches', 'logfile', 'log' ], from_cache:bool=True) -> dict:
    '''
    Returns :
      dict -> { con_seq : { instance_id : { log_switches :  [{datetime , count }], logfiles : [list], log : [list] }
    '''
    ret = {}

    # Get log switches per minute
    if 'log_switches' in fields :
      for con_seq,con_data in self.get_remote_query('ve_loghist.sql', from_cache=from_cache).items() :
        ret[con_seq] = { }
        for l_entry in con_data['data'] :
          dct = {
              'datetime' : datetime.datetime.strptime(l_entry['char_datetime'], '%Y-%m-%d  %H:%M'),
              'count' : l_entry['count'] }
          try :
            ret[con_seq][l_entry['inst_id']]['log_switches'].append(dct)
          except :
            ret[con_seq][l_entry['inst_id']] = { 'log_switches' : [ dct ] }

    if 'logfile' in fields :
      for con_seq,con_data in self.get_remote_query('ve_logfile.sql', from_cache=from_cache).items() :
        if con_seq not in ret :
          ret[con_seq] = {}
        for l_entry in con_data['data'] :
          dct = { k : l_entry[k] for k in [ 'group', 'status', 'type', 'member', 'is_recovery_dest_file' ] }
          try :
            ret[con_seq][l_entry['inst_id']]['logfiles'].append(dct)
          except :
            try :
              ret[con_seq][l_entry['inst_id']]['logfiles'] = [ dct ]
            except :
              ret[con_seq][l_entry['inst_id']] = { 'logfiles' : [ dct ] }

    if 'log' in fields :
      for con_seq,data in self.get_remote_query('ve_log.sql', from_cache=from_cache).items() :
        if con_seq not in ret :
          ret[con_seq] = {}
        for row in data['data'] :
          inst_id = row['inst_id']
          row.pop('inst_id')
          try :
            ret[con_seq][inst_id]['log'].append(row)
          except :
            try :
              ret[con_seq][inst_id] = { 'log' : [ row ] }
            except :
              ret[con_seq] = { inst_id : { 'log' : [ row ] } }

    return(ret)

#######################################################################################################################
  def ve_active_sessions(self, from_cache:bool=True) :
    '''
    Get active sessions along with information about what its being done
    '''
    ret = {}
    instance_info = self.ve_instance_info()
    for con_seq, data in self.get_remote_query('ve_active_sessions.sql', from_cache=from_cache).items() :
      ret[con_seq] = []
      for row in data['data'] :
        hostname = instance_info[con_seq][row['inst_id']]['hostname']
        inst_name =  instance_info[con_seq][row['inst_id']]['name']
        to_check = [ True if i['inst_name'] == inst_name and \
                             i['session_id'] == row['session_id'] \
                          else \
                     False \
                     for i in ret[con_seq]]
        if not any(to_check) :
          ret[con_seq].append({ **{ 'server' : hostname, 'inst_name' : inst_name }, **row })
    return(ret)


#######################################################################################################################
  def ve_instance_info(self, from_cache = True) -> dict:
    '''
    Get a dict with information about all instances

    Returns:
      dict ->
        { con_sequence : instance_id { **data } }
    '''
    ret = { con_seq : { row['id'] : row for row in data['data'] } for con_seq, data in \
        self.get_remote_query('ve_instance_info.sql', from_cache=from_cache).items() }
    return(ret)

#######################################################################################################################
  def ve_database_info(self, from_cache=True) :
    ret = {}

    for con_seq, data in self.get_remote_query('ve_database_info.sql', from_cache=from_cache).items() :
      ret[con_seq] = {}
      for row in data['data'] :
        name = row['name']
        for k in [ 'inst_id', 'log_mode', 'controlfile_type', 'open_resetlogs', 'open_mode', 'protection_mode', \
                   'protection_level', 'protection_level', 'remote_archive', 'database_role', 'platform_id', \
                   'platform_name' ] :
          try :
            ret[con_seq][name][k].append(row[k])
          except :
            try :
              ret[con_seq][name] = { k : [ row[k] ] }
            except :
              ret[con_seq] = { name : { k : [ row[k] ] } }
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
    for con_seq, data in self.get_remote_query('ve_users_with_objets.sql', from_cache=from_cache).items() :
      ret[con_seq] = { row['owner'] : { row['status'] : row['count'] }  for row in data['data'] }
    return(ret)


#######################################################################################################################
  def ve_osstat(self, from_cache=True) :
    ret = {}
    for con_seq, data in self.get_remote_query('ve_osstat.sql', from_cache=from_cache).items() :
      ret[con_seq] = {}
      for row in data['data'] :
        ret[con_seq][row['stat_name']] = { k : row[k] for k in [ 'value', 'cumulative', 'comments' ] }
    return(ret)

#######################################################################################################################
  def ve_sum_datafile_size(self, from_cache=True) :
    ret = {}
    for con_seq, data in self.get_remote_query('ve_sum_datafile.sql', from_cache=from_cache).items() :
      ret[con_seq] = {}
      for row in data['data'] :
        ret[con_seq]['dbsize'] = row['dbsize']
    return(ret)

#######################################################################################################################
  def ve_object_type_size(self, from_cache=True) :
    ret = {}
    for con_seq, data in self.get_remote_query('ve_object_type_size.sql', from_cache=from_cache).items() :
      ret[con_seq] =  { row['segment_type'] : row['size'] for row in data['data'] }
    return(ret)

#######################################################################################################################
  def ve_open_cursor(self, from_cache=True) :
    ret = {}
    for con_seq, data in self.get_remote_query('ve_open_cursor.sql', from_cache=from_cache).items() :
      ret[con_seq] = { row['parameter'] : { k : row[k] for k in [ 'size', 'usage' ] } for row in data['data'] }
    return(ret)

#######################################################################################################################
  def ve_asm_dg(self, from_cache=True) :
    ret = {}
    for con_seq, data in self.get_remote_query('ve_asm_dg.sql', from_cache=from_cache).items() :
      ret[con_seq] = { }
      for row in data['data'] :
        ret[con_seq][row['dgname']] = { 'config' : {}, 'disks' : {} }
        for k in [ 'state', 'redundancy_level', 'sector_size', 'block_size', 'allocation_unit_size',
                   'compatibility', 'database_compatibility', 'dg_size', 'dg_used_size', 'dg_free_size' ] :
          ret[con_seq][row['dgname']]['config'][k] = row[k]
        if 'inst_id' in ret[con_seq][row['dgname']] :
          ret[con_seq][row['dgname']]['config']['inst_id'].append(row['inst_id'])
        else :
          ret[con_seq][row['dgname']]['config']['inst_id'] = [ row['inst_id'] ]
    for con_seq, data in self.get_remote_query('ve_asm_disk_stat.sql', from_cache=from_cache).items() :
      if con_seq not in ret :
        ret[con_seq] = {}
      for row in data['data'] :
        if row['dg_name'] not in ret[con_seq]:
          ret[con_seq][row['dg_name']]  = { 'config' : {}, 'disks' : {} }
        ret[con_seq][row['dg_name']]['disks'] = { row['path'] : { k1 : row[k1] for k1 in [ 'disk_size', 'free_disk_space' ] } }
    return(ret)

#######################################################################################################################
  def ve_wait_events(self, metrics = [ 'session_wait_event_history', 'system_wait_events', 'system_wait_history' ], \
                     from_cache=True) -> dict:
    '''
    Get current wait events on the database instances

    Returns :
      dict ->
        { con_sequence : { 'session_wait_event' : [], 'wait_hist' : [], 'system_waits' : [] }}'
    '''
    base_ret = { 'session_wait_event_history' : [], 'system_wait_events' : [], 'system_wait_history' : []}
    ret = { i : base_ret for i in range(len(self.__remote_connections__)) }

    if 'session_wait_event_history' in metrics :
      for con_seq, evts in self.get_remote_query('ve_session_wait_hist.sql', from_cache=from_cache).items() :
        ret[con_seq]['session_wait_event_history'] = evts['data']

    if 'system_wait_events' in metrics :
      for con_seq, evts in self.get_remote_query('ve_system_wait_class.sql', from_cache=from_cache).items() :
        ret[con_seq]['system_wait_events'] = evts['data']

    if 'system_wait_history' in metrics :
      for con_seq, evts in self.get_remote_query('ve_wait_hist.sql', from_cache=from_cache).items() :
        ret[con_seq]['system_wait_history'] = evts['data']

    return(ret)
