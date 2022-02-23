from ..utils.debug_post_msg import debug_post_msg
from ..utils.get_list_avg_and_diff import get_list_avg_and_diff
from .vmstat import parser as vmstat_parser
from ..Base_collector import Base_collector
import collections

class collector(Base_collector) :
  def __init__(self, config = None, logger = None, bos_data = None ) :
    '''
    General net data collector
    Parameters:
      config -> obj : config object with all configuration ( from __init__ )
      logger -> obj : pq_logger object with all logging setup
    '''
    super().__init__( config = config, logger = logger, bos_data = bos_data)

    self.providers = { 'vmstat' : vmstat_parser(**self.general_parameters) }

    self.file_sources = self.providers['vmstat'].file_sources

    return(None)

#######################################################################################################################
  def load_from_db(self, db, days_to_fetch:int=1, append_dict:dict={}) -> dict :
    '''
    Returned data for each field:
      just_changes,avg_list(just_changes), change_rate
        [ difference between elements in list ], average_value, rate_in_which_elements changed, [ raw values within the database ]
    '''
    values_from_db = {}

    try :
      now = datetime.datetime.utcnow()
      start_analysis = now - datetime.timedelta(days=days_to_fetch)
      extra_filters = [ '|> filter(fn: (r) => r["host"] == "%s")'%(self.bos_data.data['bos']['hostname']) ]
      for i in db.query("vmstat", start_analysis.timestamp(), now.timestamp(), extra_filters=extra_filters) :
        try :
          values_from_db[i['_field']][3].append(i['_value'])
        except :
          values_from_db[i['_field']] = [ [], 0, 0, [ i['_value'] ] ]

      for k,v in values_from_db.items() :
        try :
          v[3] += append_dict[k]
        except :
          pass
        v[0], v[1], v[2] = get_list_avg_and_diff(v[3])
    except :
      pass
    if len(values_from_db) == 0 :
      values_from_db = append_dict
    return(values_from_db)

#######################################################################################################################
  def health_check(self, update_from_system:bool = True, db=None, stationary_treshold:float=0.5, days_to_fetch_back:int=45, \
      just_check_groups:bool=True, change_tolerance:float=0.1, debug:bool=False) -> list :
    '''
    Send health messages into server's syslog for diag purposes

    Parameters :
      update_from_system : bool = Get latest data from the local system before give any measurement
    '''
    messages = []
    values_from_db = collections.defaultdict(dict)

    # update stored stats
    if update_from_system :
      self.update_from_system()

    vmstat = { k : [ [], 0, 0, [ v ] ] for k,v in self.providers['vmstat']['stats'].items() }
    values_from_db = self.load_from_db(db,days_to_fetch=days_to_fetch_back, append_dict=vmstat)

    if self.bos_data['bos']['os'] == 'aix' :
      if values_from_db['pending_disk_ios_blocked_with_no_pbuf'][3][-1] > 0 :
        msg_to_append = ''
        base_msg = "Blocked lvm IO, please check pv_pbuf_count under lvmo "
        ana_val = values_from_db['pending_disk_ios_blocked_with_no_pbuf'][3]
        if len(values_from_db['pending_disk_ios_blocked_with_no_pbuf'][3]) > 1 :
          base_reading = values_from_db['pending_disk_ios_blocked_with_no_pbuf']
          change_value = base_reading[3][-1] - base_reading[3][-2]
          if change_value < stationary_treshold :
            msg_to_append = '%s, pending_disk_ios_blocked_with_no_pbuf moved out of stationary state'%base_msg
          elif abs(change_value[1]/change_value[0][-1]) > change_tolerance :
            msg_to_append = '%s, pending_disk_ios_blocked_with_no_pbuf incrementing faster than usual'%base_msg
          elif debug :
            msg_to_append = '%s, actual counters: %s'%(base_msg,str(base_reading))
        else :
          msg_to_append = '%s, no history to evaluate pending_disk_ios_blocked_with_no_pbuf '%base_msg
        if len(msg_to_append) > 0 :
          messages.append(msg_to_append)
      if values_from_db['filesystem_ios_blocked_with_no_fsbuf'][3][-1] > 0 :
        reading = values_from_db['filesystem_ios_blocked_with_no_fsbuf']
        base_msg = "Blocked JFS IO, possible slow storage backend or lack of numfsbufs"
        if len(reading[3]) > 1 :
          if reading[3][-1] - reading[3][-2] > 0 :
            messages.append(base_msg)
        else :
          messages.append(base_msg)
      if values_from_db['external_pager_filesystem_ios_blocked_with_no_fsbuf'][3][-1] > 0 :
        reading = values_from_db['external_pager_filesystem_ios_blocked_with_no_fsbuf']
        base_msg = "Possible blocked JFS2 IO, please check vmo tunings"

    return(messages)
