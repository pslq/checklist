from . import debug_post_msg, get_command_output, avg_list
from .bos_info import bos as bos_info
from .entstat import parser as entstat_parser
from .netstat import parser as netstat_parser
from .bos_info import bos as bos_parser

import concurrent.futures
from datetime import datetime
from time import time

class collector :
  def __init__(self, config = None, logger = None ) :
    '''
    General cpu data collector
    Parameters:
      config -> obj : config object with all configuration ( from __init__ )
      logger -> obj : pq_logger object with all logging setup
    '''
    self.config        = config
    self.logger        = logger
    self.cwd           = '/tmp'
    self.bos           = bos_info()
    self.to_collectors = dict(logger = self.logger, cwd=self.cwd, bos_info=self.bos)
    self.entstat       = entstat_parser(**self.to_collectors)
    self.netstat       = netstat_parser(**self.to_collectors)

    # objects that provide measurements
    self.measurement_providers = [ self.entstat, self.netstat ]

    return(None)

  def __del__(self) :
    return(None)

  def __exit__(self, exc_type, exc_value, exc_traceback):
    return(None)

  def update_data(self) :
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
      for i in self.measurement_providers :
        executor.submit(i.collect)
    return(None)

#######################################################################################################################
  def health_check(self) :
    '''
    Send health messages into server's syslog for diag purposes
    '''
    # update stored stats
    self.update_data()

    return(None)


#######################################################################################################################
  def get_latest_measurements(self, debug=False) :
    '''
    Get in influxdb format latest cpu utilization measurements from the lpar

    Parameters:
      debug : bool -> [True,False] Log into syslog amount of time that took to get the measurements

    Returns:
      list of measurements
    '''
    from time import time
    ret = []
    st = time()
    self.update_data()
    for measurement_provider in self.measurement_providers :
      ret += measurement_provider.get_latest_measurements()
    if debug :
      duration = time() - st
      debug_post_msg(self.logger,'NET Collect Task Duration: %d seconds'%int(duration), err= False)

    return(ret)
