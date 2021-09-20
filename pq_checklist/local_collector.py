from . import pq_logger, debug_post_msg, conv_bash_var_to_dict, net_collector, cpu_collector
import importlib,json
from datetime import datetime

def __pq_main_loop__() :
  from . import get_config
  import time
  config,logger = get_config(log_start=False)
  coll_class = collector(config = config, logger = logger)
  while True :
    coll_class.collect_all()
    time.sleep(int(config['LOOP']['interval']))

  return(None)


def loop() :
  from multiprocessing import Process
  p = Process(target=__pq_main_loop__)
  p.start()
  return(p)


class collector :
  def __init__(self, config = None, logger = None ) :
    self.rundir = '/tmp'
    self.config = config
    self.logger = logger
    self.write_to_dump = False
    self.healthcheck = False

    # Load collectors
    self.net_collector = net_collector.collector(config = config, logger = logger)
    self.cpu_collector = cpu_collector.collector(config = config, logger = logger)
    self.collectors    = ( self.net_collector, self.cpu_collector )

    # Check if we do healthchecks
    if "healthcheck" in self.config['MODE'] :
      if self.config['MODE']['healthcheck'].lower().strip() == 'true' :
        self.healthcheck = True

    debug_post_msg(self.logger,'Starting local collector')
    return(None)

  def __del__(self) :
    return(None)

  def __exit__(self, exc_type, exc_value, exc_traceback):
    return(None)


  def collect_all(self, debug=False) :
    from time import time
    from .db_client import db_client
    st = time()
    data = []
    for measurement_povider in self.collectors :
      data += measurement_povider.get_latest_measurements(debug = debug)
      if self.healthcheck :
        try :
          measurement_povider.health_check()
        except :
          pass


    with db_client(self.config,self.logger) as db :
      db.write(data)

    duration = time() - st
    debug_post_msg(self.logger,'Collect Task Duration: %d seconds'%int(duration))

    return(None)
