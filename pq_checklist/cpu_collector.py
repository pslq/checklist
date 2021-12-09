from . import debug_post_msg, get_command_output, avg_list
from .lparstat import parser as lparstat_parser
from .mpstat import parser as mpstat_parser
from .Base_collector import Base_collector

from datetime import datetime

class collector(Base_collector) :
  def __init__(self, config = None, logger = None, bos_data = None ) :
    '''
    General cpu data collector
    Parameters:
      config -> obj : config object with all configuration ( from __init__ )
      logger -> obj : pq_logger object with all logging setup
    '''
    super().__init__( config = config, logger = logger, bos_data = bos_data)
    # Stuff from config
    self.involuntarycontextswitch_ratio_target     = float(self.config['CPU']['involuntarycontextswitch_ratio'].split(' ')[0])
    self.involuntarycorecontextswitch_ratio_target = float(self.config['CPU']['involuntarycorecontextswitch_ratio'].split(' ')[0])
    self.cpu_max_usage_warn                        = float(self.config['CPU']['max_usage_warn'])
    self.cpu_min_usage_warn                        = float(self.config['CPU']['min_usage_warn'])
    self.rq_relative_100pct                        = float(self.config['CPU']['rq_relative_100pct'])
    self.min_core_pool_warn                        = float(self.config['CPU']['min_core_pool_warn'])
    self.samples                                   = self.config['CPU']['samples']
    self.interval                                  = self.config['CPU']['interval']



    self.providers = { 'lparstat' : lparstat_parser(**self.general_parameters),
                       'mpstat'   : mpstat_parser(**self.general_parameters) }


    return(None)

#######################################################################################################################

#######################################################################################################################
  def health_check(self, update_from_system:bool = True, db=None) -> list:
    '''
    Send health messages into server's syslog for diag purposes

    Parameters :
      update_from_system : bool = Get latest data from the local system before give any measurement
    '''
    ret_messages = []
    # update stored stats
    if update_from_system:
      self.update_from_system()

    # Local variable naming ( facilitate coding )
    mpstat, lparstat = self.providers['mpstat'], self.providers['lparstat']

    involuntarycorecontextswitch_ratio = -1
    # Process mpstat health
    if 'ics' in mpstat.data['stats'] :
      involuntarycontextswitch_ratio     = avg_list(mpstat.data['stats']['ics'])/avg_list(mpstat.data['stats']['cs'])
    else :
      # On Linux:
      # find [0-9]* -maxdepth 1 -name "status"  -exec egrep 'voluntary_ctxt_switches|nonvoluntary_ctxt_switches' {} \;
      involuntarycontextswitch_ratio     = -1

    if 'ilcs' in mpstat.data['stats'] :
      involuntarycorecontextswitch_ratio = avg_list(mpstat.data['stats']['ilcs'])/avg_list(mpstat.data['stats']['vlcs'])
    elif 'CPU' in mpstat.data['stats'] :
      if 'steal' in mpstat.data['stats']['CPU']['all'] :
        involuntarycorecontextswitch_ratio = mpstat.data['stats']['CPU']['all']['steal']

    # Calculate peak cpu utilization
    if 'sy' in mpstat.data['stats'] :
      cur_cpu_utilization = max([sum([ avg_list(lparstat.data['stats'][v]) for v in [ 'sys', 'wait', 'user' ] ]), sum([ avg_list(mpstat.data['stats'][v]) for v in [ 'sy', 'wa', 'us' ] ])])
    else :
      cur_cpu_utilization =  100-avg_list(mpstat.data['stats']['CPU']['all']['idle'])

    if cur_cpu_utilization >= self.cpu_max_usage_warn and self.cpu_max_usage_warn != -1 :
      if 'shared' in lparstat.data['info']['type'] and \
          self.involuntarycorecontextswitch_ratio_target != -1 and \
          involuntarycorecontextswitch_ratio != -1 and \
          involuntarycorecontextswitch_ratio > self.involuntarycorecontextswitch_ratio_target :
        ret_messages.append('High CPU utilization detected along with possible core starvation of the lpar, due high ilcs vs vlcs ratio, values : %f %f'%(cur_cpu_utilization,involuntarycorecontextswitch_ratio))
      if self.involuntarycontextswitch_ratio_target != -1 and involuntarycontextswitch_ratio <= involuntarycontextswitch_ratio :
        ret_messages.append('High CPU utilization detected along with possible cpu starvation of the lpar, due high cs vs ics ratio, values : %f %f'%(cur_cpu_utilization,involuntarycontextswitch_ratio))
      else :
        ret_messages.append('High CPU utilization detected, values : %f'%(cur_cpu_utilization))
    elif self.cpu_min_usage_warn != -1 and cur_cpu_utilization <= self.cpu_min_usage_warn :
      ret_messages.append('LOW CPU utilization detected, values : %f'%(cur_cpu_utilization))

    if self.rq_relative_100pct != -1 :
      thread_count = self.bos_data['smt']['thread_count']
      actual_rq = avg_list(mpstat.data['stats']['rq'])
      if actual_rq / thread_count > self.rq_relative_100pct :
        ret_messages.append('High run queue detected on the server, value %f'%(actual_rq))

    if 'app' in lparstat.data['stats'] :
      actual_app = avg_list(lparstat.data['stats']['app'])
      if actual_app <= self.min_core_pool_warn and self.min_core_pool_warn != -1 :
        ret_messages.append('Shared processor pool near its capacity limit, value %f'%(actual_app))

    return(ret_messages)

