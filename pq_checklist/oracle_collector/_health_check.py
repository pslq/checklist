import datetime
import os.path, os
import concurrent.futures


def health_check(self,update_from_system:bool = True) -> list :
  '''
  '''
  ret = []
  instance_info = self.ve_instance_info()

  cur_time = datetime.datetime.utcnow()

  # Measure logswitches
  if self.log_switches_hour_alert > 0 :
    databases = {}
    for con_seq,ldb_info in self.ve_log(fields=['log_switches']).items() :
      database_name = self.database_name(con_seq)
      databases[database_name] = {}
      for inst_id,inst_data in ldb_info.items() :
        instance_name = instance_info[con_seq][inst_id]['name']
        databases[database_name][instance_name] = {}
        for lswitch in inst_data['log_switches'] :
          lkh = lswitch['datetime'] - datetime.timedelta(minutes=lswitch['datetime'].minute) # hour
          try :
            databases[database_name][instance_name][lkh] += lswitch['count']
          except :
            databases[database_name][instance_name][lkh] = lswitch['count']
    for db,data in databases.items() :
      for instance,dates in data.items() :
        for dt,cnt in dates.items() :
          #if cnt > self.log_switches_hour_alert and dt > datetime.datetime.utcnow()- datetime.timedelta(minutes=60) :
          if cnt > self.log_switches_hour_alert :
            ret.append('The instance %s of database %s switched logs %d times at : %s'%(instance,db,cnt,str(dt)))

  # Placeholder to store sql_ids
  sql_ids = {}
  fts_count = 0
  # Dump directory
  dst_dir = os.path.join(self.script_dumpdir,'dumped_queries')

  for con_seq, longops in self.ve_with_work().items() :
    database_name = self.database_name(con_seq)
    sql_ids[con_seq] = []
    for lgop in longops :
      sql_ids[con_seq].append(lgop['sql_id'])
    ids = list(set(sql_ids[con_seq]))
    sql_ids[con_seq] = ids
    if len(ids) > 0 :
      ret.append('The database %s has a total of %d longops happening, please check dumped queries'%(database_name,len(ids)))

  if self.dump_longops or self.dump_running_ids :
    try :
      os.mkdir(dst_dir)
    except :
      pass

    ids = {}
    if self.dump_running_ids :
      for con_seq,queries in sql_ids.items() :
         for sql_id in queries :
           try:
             ids[con_seq].append(sql_id)
           except :
             ids[con_seq] = [ sql_id ]

    if self.dump_running_ids :
      for con_seq,data in self.ve_sql_monitor().items() :
        for sql_id in data['top_queries'] :
          try:
            ids[con_seq].append(sql_id)
          except :
            ids[con_seq] = [ sql_id ]

    ids = { con_seq : list(set(ids[con_seq])) for con_seq in ids.keys() }
    biggest = max([ len(i) for i in ids.values() ])
    run_tasks = []
    run_data  = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.__remote_connections__)) as executor:

      for _ in range(max([ len(i) for i in ids.values() ])) :
        for dbs,sql_ids in ids.items() :
          if len(sql_ids) > 0 :
            run_id = sql_ids.pop(0)
            run_tasks.append(executor.submit(self.ve_sqltxt,run_id, dbs, dst_dir, True))
            run_data.append([run_id, dbs])

      for p,fut in enumerate(concurrent.futures.as_completed(run_tasks)) :
        cur_result = fut.result()
        if not cur_result['in_previous_report'] :
          if cur_result['problem_with_plan_analysis'] :
            db_name = database_name = self.database_name(run_data[p][1])
            ret.append('The Query %s from database %s has a execution plan too long, possible problems'%(run_data[p][0],db_name))
          if cur_result['has_fts'] :
            db_name = database_name = self.database_name(run_data[p][1])
            ret.append('The Query %s from database %s has a full table scan, please check'%(run_data[p][0],db_name))
            fts_count += 1
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
