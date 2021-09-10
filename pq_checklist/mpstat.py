#!/opt/freeware/bin/python3

# All imports used
from .stats_parser import StatsParser
from . import avg_list
import datetime

class parser(StatsParser) :
  def __init__(self, logger = None, ansible_module = None, samples = 2, interval = 1, rundir = '/tmp', preserv_stats = False, lparstat_data = None) :
    super().__init__()

    self.lparstat_data = lparstat_data
    self.preserv_stats = preserv_stats
    self.commands = {
        'stats' : "mpstat -a %d %d"%(self.interval, self.samples)
        }
    self.functions = {
        'stats' : self.parse_mpstat_stats
        }

    # Internal list to hold all keys used when parsing stats data
    self.__stats_keys__ = []

    return(None)


  def get_latest_measurements(self, elements = [ 'stats' ], consolidate_function = avg_list, use_existent:bool=True) :
    if not use_existent or len(self.__stats_keys__) < 1 :
      self.collect(elements = elements)
    if self.lparstat_data :
      to_be_added = {'measurement' : 'mpstat', 'tags' : { 'host' : self.lparstat_data.collect(elements=['info'])['info']['node_name'] }, 'fields' : { 'time' : int(datetime.datetime.now().timestamp()) } }
    else :
      to_be_added = {'measurement' : 'mpstat', 'tags' : { }, 'fields' : { 'time' : int(datetime.datetime.now().timestamp()) } }

    tmp_dict = self.data['stats']
    tmp_dict.pop('cpu')
    for key in tmp_dict.keys() :
      to_be_added['fields'][key] = consolidate_function(tmp_dict[key])

    return(to_be_added)


  def parse_mpstat_stats(self, data:list) :
    if not self.preserv_stats :
      if len(self.__stats_keys__) > 0 :
        for k in self.data['stats'].keys() :
          self.data['stats'][k] = []
    self.data['stats'],self.__stats_keys__ = self.parse_sar_stats(data, key_heading='cpu', specific_reading={ 'key_position' : 0, 'key_value' : 'ALL' })
    return(self.data['stats'])

#######################################################################################################################
#######################################################################################################################
