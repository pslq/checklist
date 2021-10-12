from . import pq_logger, debug_post_msg, conv_bash_var_to_dict
import importlib,json,os
from datetime import datetime
from .Base_collector import Base_collector

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

    while True :
      collector(config = config, logger = logger).collect_all()
      time.sleep(int(config['LOOP']['interval']))
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
  def collect_all(self, debug=False) -> None:
    '''
    Main function that consolidate all data from collectors
    '''
    from time import time
    from .db_client import db_client
    st = time()
    data = []
    update_data_on_measurement = True
    mode = self.config['MODE']['mode'].strip().lower()

    if mode == 'local' :
      if self.nodename not in self.collectors :
        self.__load_collectors_for_host__(self.nodename)
    elif mode == 'ansible' :
      self.update_all_ansible_playbook(debug=debug)
      update_data_on_measurement = False

    # Get all information from hosts defined into the collectors
    for hosts in self.collectors.keys() :
      for measurement_povider in self.collectors[hosts].values() :
        data += measurement_povider.get_latest_measurements(debug = debug, update_from_system=update_data_on_measurement)
        # Get Health Check routines and send to syslog
        if self.healthcheck :
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
    from . import ansible_helper
    playbook = self.config['ANSIBLE']['playbook'].strip()
    to_collect = []
    tasks_output = {}
    if 'cpu' in self.checks_to_perform :
      to_collect += [ "smtctl_c", "lsdev_class", "mpstat_a", "lparstat_i", "lparstat_s", "uname_a" ]
    if 'net' in self.checks_to_perform :
      to_collect += [ 'entstat', 'netstat_s' ]
      tasks_output['entstat'] = [ 'adapters' ]

    runner_parms = { 'playbook' : self.config['ANSIBLE']['playbook'].strip(),
                     'host_limit' : self.config['ANSIBLE']['host_target'].strip(),
                     'private_data_dir' : self.config['ANSIBLE']['private_data_dir'].strip(),
                     'quiet' : debug, 'cleanup_artifacts' : False if debug else True,
                     'wanted_outputs' : to_collect, 'output_specific_data' : tasks_output}

    data_from_ansible = ansible_helper.playbook_runner(**runner_parms)

    try :
      for host,data in data_from_ansible['results'].items() :
        if host not in self.collectors :
          if self.__load_collectors_for_host__(host) :
            self.__load_collectors_for_host__(self.nodename, local_only=True)
        for check in ( 'cpu', 'net' ) :
          if check in self.checks_to_perform and check in self.collectors[host] :
            self.collectors[host][check].update_from_dict(data)
    except Exception as e :
      debug_post_msg(self.logger,'Error when updating collectors with ansible data : %s'%e, raise_type=Exception)

    return(data_from_ansible)
