# All imports used
from ..Stats_Parser import StatsParser
from ..utils.avg_list import avg_list
from ..utils.debug_post_msg import debug_post_msg
from ..utils.pq_round_number import pq_round_number
import datetime

class parser(StatsParser) :
  def __init__(self, logger = None, samples = 2, interval = 1, cwd = '/tmp', bos_data = None) :
    super().__init__(logger = logger, cwd = cwd, bos_data = bos_data)

    comms = { 'aix' : "vmstat -sv",
              'linux' : "vmstat -sS B"
              }

    self.commands[self.bos_data['bos']['os']]['stats'] = comms[self.bos_data.data['bos']['os']]

    self.functions['aix'] = { 'stats' : self.parse_vmstat_s }
    self.functions['linux'] = { 'stats' : self.parse_vmstat_s }

    self.file_sources = {
        'vmstat_sSB' : self.parse_vmstat_s,
        'vmstat_sv' : self.parse_vmstat_s
        }


    # Internal list to hold all keys used when parsing stats data
    self.__stats_keys__ = []

    return(None)

#######################################################################################################################
  def update_commands(self) :
    comms = { 'aix' : [ 'stats', "vmstat -sv" ],
              'linux' : [ 'stats', "vmstat -sS B" ] }
    self.commands = { k : { v[0] : v[1] } for k,v in comms.items() }
    return(None)

#######################################################################################################################
  def get_measurements(self, elements = [ 'stats' ], consolidate_function = avg_list, update_from_system:bool=True) :
    ret = []
    cur_time = datetime.datetime.utcnow().isoformat()
    if update_from_system :
      self.update_from_system(elements = elements)

    if self.bos_data['bos']['os'] == 'linux' :
      pct_calc = round((1 - (self.data['stats']['b_total_memory'] - ( self.data['stats']['b_used_memory'] + self.data['stats']['b_buffer_memory'] ))/self.data['stats']['b_total_memory'])*100,2)
      self.data['stats']['percentage_of_memory_used_for_computational_pages'] = pct_calc

    ret.append({'measurement' : 'vmstat',
      'tags' : { 'host' : self.bos_data['bos']['hostname'], 'os' : self.bos_data['bos']['os'] },
                'fields' : self.data['stats'],
                'time' : cur_time
                })
    return(ret)


#######################################################################################################################
  def parse_vmstat_s(self, data:list, os='') :
    self.data['stats'] = {}
    for ln in data :
      ln = ln.strip().replace('.', '').replace('/', '').split(' ')
      self.data['stats']['_'.join(ln[1:]).lower()] = float(ln[0].replace('.',','))

    return(self.data['stats'])


#######################################################################################################################
#######################################################################################################################
