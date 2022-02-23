# All imports used
from ..Stats_Parser import StatsParser
from ..utils.avg_list import avg_list
from ..utils.line_cleanup import line_cleanup
import datetime

class parser(StatsParser) :
  def __init__(self, logger = None, samples = 2, interval = 1, cwd = '/tmp', bos_data = None) :
    super().__init__(logger = logger, cwd = cwd, bos_data = bos_data)

    self.file_sources = {
        'mpstat_AIX' : self.parse_mpstat_stats,
        'mpstat_LINUX' : self.parse_mpstat_stats
        }


    # Internal list to hold all keys used when parsing stats data
    self.__stats_keys__ = []

    return(None)

#######################################################################################################################
  def update_commands(self) :
    comms = { 'aix' : ['stats', "mpstat -a %d %d"%(self.interval, self.samples) ],
              'linux' : [ 'stats', "mpstat -A %d %d"%(self.interval, self.samples) ]}
    func  = { 'aix' : [ 'stats', self.parse_mpstat_stats ],
              'linux' : ['stats', self.parse_mpstat_stats ] }


    self.commands = { k : { v[0] : v[1] } for k,v in comms.items() }
    self.functions = { k : { v[0] : v[1] } for k,v in func.items() }
    return(None)

#######################################################################################################################
  def get_measurements(self, elements = [ 'stats' ], consolidate_function = avg_list, update_from_system:bool=True) :
    if update_from_system :
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
    if self.bos_data.data['bos']['os'] == "aix" :
      self.data['stats'],self.__stats_keys__ = self.parse_sar_stats(data, key_heading='cpu', specific_reading={ 'key_position' : 0, 'key_value' : 'ALL' })
    elif self.bos_data.data['bos']['os'] == "linux" :
      if 'stats' not in self.data :
        self.data['stats'] = {}
      for dt in line_cleanup(data, remove_endln=True) :
        if len(dt) == 0 :
          l_keys = []
        else :
          sp = dt.split(' ')
          if sp[0] == 'Average:' :
            if sp[1] in [ 'CPU', 'NODE' ] :
              l_keys = [ l.lower().replace('%','').replace('/','_') for l in sp ]
            elif len(l_keys) > 0 :
              for key_pos in range(2,len(l_keys)) :
                try :
                  self.data['stats'][l_keys[1]][sp[1]][l_keys[key_pos]].append(sp[key_pos])
                except :
                  try :
                    self.data['stats'][l_keys[1]][sp[1]] = { l_keys[key_pos] : [ sp[key_pos] ] }
                  except :
                    self.data['stats'][l_keys[1]] = { sp[1] : { l_keys[key_pos] : [ sp[key_pos] ] } }
    return(self.data['stats'])

#######################################################################################################################
#######################################################################################################################
