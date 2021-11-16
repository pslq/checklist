from . import pq_logger, debug_post_msg, conv_bash_var_to_dict
import importlib,json,os
from datetime import datetime
from .Base_collector import Base_collector
from . import ansible_helper
from time import time
from .db_client import db_client
from . import net_collector, cpu_collector, dio_collector, oracle_collector


#######################################################################################################################
def loop(config_file) :
  '''
  main loop that will refresh
  '''
  from multiprocessing import Process

  # Inner function that will run in loop
  def __pq_main_loop__(config_file) :
    from . import get_config
    import time
    if len(config_file) > 0 :
      config,logger = get_config(log_start=False, config_path=config_file)
    else :
      config,logger = get_config(log_start=False)

    hc_loop_count_from_config = int(config['LOOP']['hc_loop_count'])
    hc_loop_count = 1
    interval = int(config['LOOP']['interval'])

    while True :
      if hc_loop_count == hc_loop_count_from_config :
        collector(config = config, logger = logger).collect_all(get_hc=True)
        hc_loop_count = 1
      else :
        collector(config = config, logger = logger).collect_all(get_hc=False)
        hc_loop_count += 1

      time.sleep(interval)
    return(None)

  # Main function body
  p = Process(target=__pq_main_loop__, args=(config_file,))
  p.start()
  return(p)

#######################################################################################################################
class collector(Base_collector) :
  def __init__(self, config = None, logger = None ) :
    super().__init__(config = config, logger = logger)
    return(None)


#######################################################################################################################
  def load_collectors_for_host(self,nodename:str, local_only=False) -> None :
    '''
    Load collectors for each host that will go through data collection

    Parameters :
      nodename : str -> hostname to be analyzed
      only_local_node : bool -> [True,False]  Load only collectors that should be running on the local machine

    Returns :
      None
    '''
    self.collectors[nodename] = {}
    ret = []

    cols = { 'net' : net_collector.collector,
             'cpu' : cpu_collector.collector,
             'dio' : dio_collector.collector,
             'oracle' : oracle_collector.collector
             }

    def look_for_bos(nodename) :
      '''
      Reuse bos information for another class to avoid memory waste
      '''
      ret = None
      try :
        for c in self.collectors[nodename].value() :
          if 'bos_data' in c.__dir__() :
            ret = c.bos_data
            break
      except :
        pass
      return(ret)

    def l_check(pos,l_col,nodename, local_only=False) :
      '''
      Helper to define if the collector should be loaded
      '''
      ret = True
      if ( nodename == l_col.nodename and l_col.only_on_localhost == local_only == True ) or \
         not l_col.only_on_localhost :
        self.collectors[nodename][pos] = l_col
        ret = l_col.only_on_localhost
      return(ret)

    for ck in self.checks_to_perform :
      lparms = dict(config = self.config, logger = self.logger, bos_data = look_for_bos(nodename))
      ret.append(l_check(ck,cols[ck](**lparms),nodename, local_only))

    return(any(ret))

#######################################################################################################################
  def collect_all(self, debug=False, get_hc:bool = True) -> None:
    '''
    Main function that consolidate all data from collectors
    '''
    st = time()
    data = []
    mode = self.config['MODE']['mode'].strip().lower()
    update_data_on_measurement = True if mode == 'local' else False

    if mode == 'local' :
      if self.nodename not in self.collectors :
        self.load_collectors_for_host(self.nodename)
    elif mode == 'ansible' :
      self.update_all_ansible_playbook(debug=debug)

    # Get all information from hosts defined into the collectors
    for hosts in self.collectors.keys() :
      for measurement_povider in self.collectors[hosts].values() :
        data += measurement_povider.get_latest_measurements(debug = debug, update_from_system=update_data_on_measurement)
        # Get Health Check routines and send to syslog
        if self.healthcheck and get_hc :
          for msg in measurement_povider.health_check(update_from_system=update_data_on_measurement) :
            debug_post_msg(self.logger,'MGS FROM %s : %s'%(hosts,msg))

    # Write information metrics to influxdb
    with db_client(self.config,self.logger) as db :
      if not db.write(data) :
        debug_post_msg(self.logger,'Error when writting data into DB')

    duration = time() - st
    debug_post_msg(self.logger,'Collect Task Duration: %d seconds'%int(duration))

    return(None)

#######################################################################################################################
  def update_all_ansible_playbook(self, debug=False) -> dict :
    '''
    Update all collectors within this class using the ansible playbook defined within the config

    WARNING:
      The playbook have to report specific variables in order to be feed to the providers,
        otherwise the data from ansible will be ignored

    Returns:
      dict -> A dict with data feed to the collectors
    '''
    tasks_output = {}
    playbook = self.config['ANSIBLE']['playbook'].strip()
    to_collect = [ 'uname_a', 'lsdev_class', 'smtctl_c'] # bos stuff

    collector_types = {
        'cpu' : [
          [ "mpstat_AIX", "mpstat_LINUX", "lparstat_i", "lparstat_s" ],
          []
          ],
        'net' : [
          [ 'entstat', 'netstat_s'  ],
          [ [ 'entstat', 'adapters' ] ]
          ],
        'dio' : [
          [ 'iostat_LINUX', 'iostat_AIX', 'fcstat' ],
          [ [ 'fcstat', 'adapters' ] ]
          ],
        'oracle' : [[],[]]
        }

    for coll in self.checks_to_perform :
      to_collect += collector_types[coll][0]
      tasks_output.update({ dt[0] : dt[1] for dt in collector_types[coll][1] })


    runner_parms = { 'playbook' : self.config['ANSIBLE']['playbook'].strip(),
                     'host_limit' : self.config['ANSIBLE']['host_target'].strip(),
                     'private_data_dir' : self.config['ANSIBLE']['private_data_dir'].strip(),
                     'quiet' : debug, 'cleanup_artifacts' : False if debug else True,
                     'wanted_outputs' : set(to_collect), 'output_specific_data' : tasks_output}

    data_from_ansible = ansible_helper.playbook_runner(**runner_parms)

    try :
      for host,data in data_from_ansible['results'].items() :
        if host not in self.collectors :
          if self.load_collectors_for_host(host) :
            self.load_collectors_for_host(self.nodename, local_only=True)
        for check in self.checks_to_perform :
          if check in self.collectors[host] :
            self.collectors[host][check].update_from_dict(data)
    except Exception as e :
      debug_post_msg(self.logger,'Error when updating collectors with ansible data : %s'%e, raise_type=Exception)

    return(data_from_ansible)

