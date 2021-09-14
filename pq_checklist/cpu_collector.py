from . import debug_post_msg, get_command_output, avg_list
from .lparstat import parser as lparstat_parser
from .mpstat import parser as mpstat_parser

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
    self.config = config
    self.logger = logger
    self.cwd = '/tmp'
    # Stuff from config
    self.involuntarycontextswitch_ratio_target     = float(self.config['CPU']['involuntarycontextswitch_ratio'].split(' ')[0])
    self.involuntarycorecontextswitch_ratio_target = float(self.config['CPU']['involuntarycorecontextswitch_ratio'].split(' ')[0])
    self.cpu_max_usage_warn = float(self.config['CPU']['max_usage_warn'])
    self.cpu_min_usage_warn = float(self.config['CPU']['min_usage_warn'])
    self.rq_relative_100pct = float(self.config['CPU']['rq_relative_100pct'])
    self.min_core_pool_warn = float(self.config['CPU']['min_core_pool_warn'])
    self.samples            = self.config['CPU']['samples']
    self.interval           = self.config['CPU']['interval']
    self.to_collectors      = dict(logger = self.logger, samples = self.config['CPU']['samples'],
                                   interval = self.config['CPU']['interval'], cwd = self.cwd)
    self.__smtlevel__       = { 'cpu_count' : 0, 'thread_count' : 0, 'latest_read' : 0 }

    # objects that provide measurements
    self.bos           = bos_info(logger = self.logger, cwd=self.cwd)

    self.lparstat_parser = lparstat_parser(**self.to_collectors)
    self.mpstat_parser   = mpstat_parser(**self.to_collectors, bos_data = self.bos)
    self.measurement_providers = [ self.lparstat_parser, self.mpstat_parser ]
    self.measurement_type = [ [ 'stats' ], [ 'stats' ]]


    return(None)

  def __del__(self) :
    return(None)

  def __exit__(self, exc_type, exc_value, exc_traceback):
    return(None)

  def update_data(self) :
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
      for i,j in zip(self.measurement_providers, self.measurement_type) :
        executor.submit(i.collect, j)
    return(None)

  def get_smtlevel(self):
    '''
    Get smt level of the server

    Returns:
      int,int
      amount of vcpu on the server, amount of threads currently on the server
    '''
    now = int(datetime.now().timestamp())
    if now - self.__smtlevel__['latest_read'] > 600 :
      cmd_out = get_command_output(command='smtctl', cwd=self.cwd, pq_logger = self.logger)
      cpu_count = 0
      thread_count = 0
      if cmd_out['retcode'] == 0 :
        for ln in cmd_out['stdout'] :
          if ln.startswith('proc') :
            sp = ln.split(' ')
            cpu_count += 1
            thread_count += int(sp[2])
      self.__smtlevel__  = { 'cpu_count' : cpu_count, 'thread_count' : thread_count, 'latest_read' : now }
    return(self.__smtlevel__['cpu_count'], self.__smtlevel__['thread_count'])

#######################################################################################################################
  def health_check(self) :
    '''
    Send health messages into server's syslog for diag purposes
    '''
    # update stored stats
    self.update_data()

    # Process mpstat health
    involuntarycontextswitch_ratio     = avg_list(self.mpstat_parser.data['stats']['ics'])/avg_list(self.mpstat_parser.data['stats']['cs'])
    if 'ilcs' in self.mpstat_parser.data['stats'] :
      involuntarycorecontextswitch_ratio = avg_list(self.mpstat_parser.data['stats']['ilcs'])/avg_list(self.mpstat_parser.data['stats']['vlcs'])
    else :
      involuntarycorecontextswitch_ratio = -1

    # Calculate peak cpu utilization
    cur_cpu_utilization = max([sum([ avg_list(self.lparstat_parser.data['stats'][v]) for v in [ 'sys', 'wait', 'user' ] ]), sum([ avg_list(self.mpstat_parser.data['stats'][v]) for v in [ 'sy', 'wa', 'us' ] ])])

    if cur_cpu_utilization >= self.cpu_max_usage_warn and self.cpu_max_usage_warn != -1 :
      if 'shared' in self.lparstat_parser.data['info']['type'] and \
          self.involuntarycorecontextswitch_ratio_target != -1 and \
          involuntarycorecontextswitch_ratio != -1 and \
          involuntarycorecontextswitch_ratio > self.involuntarycorecontextswitch_ratio_target :
        debug_post_msg(self.logger,
            'High CPU utilization detected along with possible core starvation of the lpar, due high ilcs vs vlcs ratio, values : %f %f'%(cur_cpu_utilization,involuntarycorecontextswitch_ratio),
            err= False)
      if self.involuntarycontextswitch_ratio_target != -1 and involuntarycontextswitch_ratio <= involuntarycontextswitch_ratio :
        debug_post_msg(self.logger,
            'High CPU utilization detected along with possible cpu starvation of the lpar, due high cs vs ics ratio, values : %f %f'%(cur_cpu_utilization,involuntarycontextswitch_ratio),
            err= False)
      else :
        debug_post_msg(self.logger,'High CPU utilization detected, values : %f'%(cur_cpu_utilization), err= False)
    elif self.cpu_min_usage_warn != -1 and cur_cpu_utilization <= self.cpu_min_usage_warn :
      debug_post_msg(self.logger,'LOW CPU utilization detected, values : %f'%(cur_cpu_utilization), err= False)

    if self.rq_relative_100pct != -1 :
      _, thread_count = self.get_smtlevel()
      actual_rq = avg_list(self.mpstat_parser.data['stats']['rq'])
      if actual_rq / thread_count > self.rq_relative_100pct :
        debug_post_msg(self.logger,'High run queue detected on the server, value %f'%(actual_rq), err= False)

    if 'app' in self.lparstat_parser.data['stats'].keys() :
      actual_app = avg_list(self.lparstat_parser.data['stats']['app'])
      if actual_app <= self.min_core_pool_warn and self.min_core_pool_warn != -1 :
        debug_post_msg(self.logger,'Shared processor pool near its capacity limit, value %f'%(actual_app), err= False)

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
    st = time()
    self.update_data()
    ret = [ i.get_latest_measurements() for i in [ self.lparstat_parser, self.mpstat_parser ] ]
    duration = time() - st
    debug_post_msg(self.logger,'CPU Collect Task Duration: %d seconds'%int(duration), err= False)

    return(ret)
