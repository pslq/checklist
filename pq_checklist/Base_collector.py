import os
from ast import literal_eval
from .bos_info import bos as bos_parser
from . import debug_post_msg

#######################################################################################################################
class Base_collector :
  def __init__(self, config = None, logger = None, bos_data = None ) :
    '''
    General data collector class
    Parameters:
      config -> obj : config object with all configuration ( from __init__ )
      logger -> obj : pq_logger object with all logging setup
    '''
    self.config            = config
    self.logger            = logger
    self.nodename          = os.uname().nodename
    self.cwd               = '/tmp'
    self.write_to_dump     = False
    self.only_on_localhost = False


    # Reuse bos in case some info has been passed
    self.bos_data          = bos_parser() if not bos_data else bos_data

    # If healthcheck functions should be called from within the collectors
    self.healthcheck       = False

    # General parameters to send to load collectors or providers
    self.general_parameters     = dict(logger = self.logger, cwd=self.cwd, bos_data=self.bos_data)

    # Collectors to be loaded which general collector
    self.checks_to_perform = literal_eval(self.config['MODE']['collectors'])

    # Sub collectors tied to this one
    self.collectors = { }

    # Specific providers tied to this collector
    self.providers  = { }

    # Check if we do healthchecks
    try :
      if self.config['MODE']['healthcheck'].lower().strip() == 'true' :
        self.healthcheck = True
    except :
      pass

    return(None)


#######################################################################################################################
  def keys(self) :
    return({'providers' : self.providers, 'collectors' : self.collectors})

#######################################################################################################################
  def __getitem__(self,key):
    '''
    Return dict like results
    '''
    rc = { 'collectors' : self.collectors, 'providers' : self.providers }

    ret = rc[key] if key in rc else None

    return(ret)

#######################################################################################################################
  def __del__(self) :
    return(None)

#######################################################################################################################
  def __exit__(self, exc_type, exc_value, exc_traceback):
    return(None)

#######################################################################################################################
  def update_from_dict(self, data:dict) -> None:
    '''
    Feed a data dict to all providers loaded within this collector
    Returns:
      None
    '''
    for provider in  [ self.bos_data ] + list(self.providers.values()) :
      try :
        provider.update_from_dict(data)
      except Exception as e :
        debug_post_msg(self.logger,'Error updating %s : %s'%(str(provider),e), raise_type=Exception)

    return(None)

#######################################################################################################################
  def update_from_system(self) -> None:
    '''
    Load data from local system to update the providers
    '''
    for provider in list(self.providers.values()) + [ self.bos_data ]  :
        provider.update_from_system()

    return(None)


#######################################################################################################################
  def __load_collectors_for_host__(self,nodename:str, local_only=False) -> None :
    '''
    Load collectors for each host that will go through data collection

    Parameters :
      nodename : str -> hostname to be analyzed
      only_local_node : bool -> [True,False]  Load only collectors that should be running on the local machine

    Returns :
      None
    '''

    def look_for_bos() :
      '''
      Reuse bos information for another class to avoid memory waste
      '''
      ret = None
      for n,c in self.collectors.items() :
        try :
          if 'bos' in c.__dir__() :
            ret = self.collectors[n].bos
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
         ( local_only == l_col.only_on_localhost == False and nodename != l_col.nodename ) :
        self.collectors[nodename][pos] = l_col
        ret = l_col.only_on_localhost
      return(ret)

    self.collectors[nodename] = {}
    ret = []

    if 'net' in self.checks_to_perform :
      from . import net_collector
      ret.append(l_check('net', net_collector.collector(config = self.config, logger = self.logger, bos_data = look_for_bos() ), nodename, local_only))

    if 'cpu' in self.checks_to_perform :
      from . import cpu_collector
      ret.append(l_check('cpu', cpu_collector.collector(config = self.config, logger = self.logger, bos_data = look_for_bos() ), nodename, local_only))

    if 'dio' in self.checks_to_perform :
      from . import dio_collector
      ret.append(l_check('dio', dio_collector.collector(config = self.config, logger = self.logger, bos_data = look_for_bos() ), nodename, local_only))

    if 'oracle' in self.checks_to_perform :
      from . import oracle_collector
      ret.append(l_check('oracle', oracle_collector.collector(config = self.config, logger = self.logger, bos_data = look_for_bos() ), nodename, local_only))

    return(any(ret))


#######################################################################################################################
  def get_latest_measurements(self, debug:bool=False, update_from_system:bool=False) :
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
    if update_from_system :
      self.update_from_system()

    for provider in self.providers.values() :
      try :
        ret += provider.get_measurements(update_from_system = update_from_system)
      except :
        ret += [ provider.get_measurements(update_from_system = update_from_system) ]

    if debug :
      duration = time() - st
      debug_post_msg(self.logger,'Collect Task Duration: %d seconds'%int(duration))

    return(ret)
