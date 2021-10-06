#!/opt/freeware/bin/python3

# All imports used
from .Stats_Parser import StatsParser
from . import avg_list
import datetime

class parser(StatsParser) :
  def __init__(self, logger = None, ansible_module = None, samples = 2, interval = 1, cwd = '/tmp', bos_data = None) :
    super().__init__(logger = logger, ansible_module = ansible_module, cwd = cwd)

    self.bos_data = bos_data
    self.commands = {
        'stats' : "mpstat -a %d %d"%(self.interval, self.samples)
        }
    self.functions = {
        'stats' : self.parse_mpstat_stats
        }

    self.file_sources = {
        'mpstat_a' : self.parse_mpstat_stats
        }


    # Internal list to hold all keys used when parsing stats data
    self.__stats_keys__ = []

    return(None)


#######################################################################################################################
  def get_measurements(self, elements = [ 'stats' ], consolidate_function = avg_list, update_from_system:bool=True) :
    if update_from_system or len(self.__stats_keys__) < 1 :
      self.update_from_system(elements = elements)

    to_be_added = {'measurement' : 'mpstat', 'tags' : { }, 'fields' : {},  'time' : datetime.datetime.utcnow().isoformat() }
    if self.bos_data :
      to_be_added['tags']['host'] = self.bos_data['bos']['hostname']

    tmp_dict = self.data['stats']
    # Remove CPU key from return, as it always comes with ALL ALL ALL
    try :
      tmp_dict.pop('cpu')
    except :
      pass
    for key in tmp_dict.keys() :
      to_be_added['fields'][key] = consolidate_function(tmp_dict[key])

    return([to_be_added])


#######################################################################################################################
  def parse_mpstat_stats(self, data:list) :
    self.data['stats'],self.__stats_keys__ = self.parse_sar_stats(data, key_heading='cpu', specific_reading={ 'key_position' : 0, 'key_value' : 'ALL' })
    return(self.data['stats'])

#######################################################################################################################
#######################################################################################################################
