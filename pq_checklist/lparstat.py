#!/opt/freeware/bin/python3

# All imports used
from . import debug_post_msg, try_conv_complex, avg_list
import csv, datetime
from collections import defaultdict



# All imports used
from .stats_parser import StatsParser

class parser(StatsParser) :
  def __init__(self, logger = None, ansible_module = None, samples = 2, interval = 1, cwd = '/tmp', preserv_stats = False) :
    '''
    '''
    super().__init__()
    self.preserv_stats  = preserv_stats
    self.commands = {
        'info' : "lparstat -i",
        'stats' : "lparstat %d %d"%(self.interval, self.samples)
        }
    self.functions = {
        'info' : self.parse_lparstat_i,
        'stats' : self.parse_lparstat_stats
        }

    self.data = { 'info' : {}, 'stats' : {} }

    # Internal list to hold all keys used when parsing lparstat data
    self.__stats_keys__ = []

    return(None)


  def get_latest_measurements(self, elements = [ 'info', 'stats' ], consolidate_function = avg_list, update_data:bool=True) :
    if not update_data or len(self.__stats_keys__) < 1 :
      self.collect(elements = elements)

    to_be_added = {'measurement' : 'lparstat', 'tags' : { 'host' : self.data['info']['node_name'] }, 'fields' : { 'time' : int(datetime.datetime.now().timestamp()) } }
    for key in self.data['stats'].keys() :
      to_be_added['fields'][key] = consolidate_function(self.data['stats'][key])

    return(to_be_added)


  def parse_lparstat_i(self, data:list) :
    try :
      for dt in csv.reader(data, delimiter=':') :
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
    except Exception as e:
      debug_post_msg(self.logger, 'Error parsing info : %s'%e)
    return(self.data['info'])

  def parse_lparstat_stats(self, data:list) :
    if not self.preserv_stats :
      if len(self.__stats_keys__) > 0 :
        for k in self.data['stats'].keys() :
          self.data['stats'][k] = []

    self.data['stats'],self.__stats_keys__ = self.parse_sar_stats(data, key_heading='%user', specific_reading={})

    return(self.data['stats'])

#######################################################################################################################
#######################################################################################################################
