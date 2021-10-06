#!/opt/freeware/bin/python3

# All imports used
from . import debug_post_msg, try_conv_complex, avg_list, line_cleanup
import datetime
from collections import defaultdict



# All imports used
from .Stats_Parser import StatsParser

class parser(StatsParser) :
  def __init__(self, logger = None, ansible_module = None, samples = 2, interval = 1, cwd = '/tmp', bos_data = None) :
    '''
    '''
    super().__init__(logger = logger, ansible_module = ansible_module, cwd = cwd)
    self.bos_data = bos_data
    self.commands = {
        'info' : "lparstat -i",
        'stats' : "lparstat %d %d"%(self.interval, self.samples)
        }
    self.functions = {
        'info' : self.parse_lparstat_i,
        'stats' : self.parse_lparstat_stats
        }

    self.data = { 'info' : {}, 'stats' : {} }

    self.file_sources = {
        'lparstat_i' : self.parse_lparstat_i,
        'lparstat_s' : self.parse_lparstat_stats,
        }

    return(None)

#######################################################################################################################
  def get_measurements(self, elements = [ 'info', 'stats' ], consolidate_function = avg_list, update_from_system:bool=True) :
    if update_from_system or len(self.__stats_keys__) < 1 :
      self.update_from_system(elements = elements)

    to_be_added = {'measurement' : 'lparstat', 'tags' : { 'host' : self.data['info']['node_name'] }, 'fields' : { },  'time' : datetime.datetime.utcnow().isoformat()  }
    for key in self.data['stats'].keys() :
      to_be_added['fields'][key] = consolidate_function(self.data['stats'][key])

    return([to_be_added])

#######################################################################################################################
  def parse_lparstat_i(self, data:list) :
    lns = []
    for dt in data :
      if dt.count('\n') > 1 :
        lns += dt.split('\n')
      else :
        lns += [ dt ]
    for dt in line_cleanup(lns, split=True, delimiter=':', cleanup=True, remove_endln=True) :
      if len(dt) == 2 :
        key_name = dt[0].lower().strip(' ').replace(' ', '_').replace('/', '_')
        key_value = dt[1].lower().strip(' ').replace(',','.').replace('%','')
        if key_value[-2:].upper() == "MB" :
          key_value = try_conv_complex(key_value.split(' ')[0])
        elif key_value[-2:] == "GB" :
          key_value = try_conv_complex(key_value.split(' ')[0])
          if not isinstance(key_value, str) :
            key_value = key_value*1024
        else :
          if key_value == '-' :
            key_value = 0
          else :
            key_value = try_conv_complex(key_value)
        self.data['info'][key_name] = key_value
    return(self.data['info'])

#######################################################################################################################
  def parse_lparstat_stats(self, data:list) :
    self.data['stats'],self.__stats_keys__ = self.parse_sar_stats(data, key_heading='%user', specific_reading={})
    return(self.data['stats'])

#######################################################################################################################
#######################################################################################################################
