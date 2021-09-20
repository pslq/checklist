#!/opt/freeware/bin/python3

# All imports used
from . import debug_post_msg, try_conv_complex, avg_list
import csv, datetime



# All imports used
from .stats_parser import StatsParser

class parser(StatsParser) :
  def __init__(self, logger = None, ansible_module = None, cwd = '/tmp', bos_info = None):
    '''
    '''
    super().__init__()
    self.bos_info = bos_info
    self.commands = { }
    self.functions = { }

    self.data = { 'stats' : {} }

    return(None)



  def update_commands(self, collect=False) :
    '''
    Update commands and functions dict
    '''
    # In case device list is empty, populate it
    if len(self.bos_info['dev_class']) == 0 :
      self.bos_info.collect()

    # In case self.commands and self.functions hasn't been populated yet
    for dev in self.bos_info['dev_class']['if'] :
      key = 'stats_%s'%dev
      self.commands[key] = "entstat -d %s"%dev
      self.functions[key] = self.parse_entstat_d
    for dev in self.bos_info['dev_class']['adapter'] :
      if 'ent' in dev :
        key = 'stats_%s'%dev
        self.commands[key] = "entstat -d %s"%dev
        self.functions[key] = self.parse_entstat_d
    if collect :
      self.collect(elements = list(self.commands.keys()))
    return(None)

  def get_latest_measurements(self) :
    ret = []
    self.collect()
    for ent, ent_data in self.data['stats'].items() :
      for tag in ( 'transmit_packets', 'general_stats', 'dev_stats' ) :
        if tag in ent_data :
          ret.append({'measurement' : 'entstat', 'tags' : { 'host' : self.bos_info['bos']['hostname'], 'stats_type' : tag, 'interface' : ent }, 'fields' : { **ent_data[tag],  **{ 'time' : int(datetime.datetime.now().timestamp()) } }})
    return(ret)


  def parse_entstat_d(self, data:list) :
    try :
      self.data['stats'].update(self.parse_entstat_stats(data))

    except Exception as e:
      debug_post_msg(self.logger, 'Error parsing info : %s'%e)
    return(self.data['stats'])


#######################################################################################################################
#######################################################################################################################
