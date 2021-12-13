from . import debug_post_msg, get_list_avg_and_diff
from .ioscli import parser as ioscli_parser
from .Base_collector import Base_collector
import collections, datetime

class collector(Base_collector) :
  def __init__(self, config = None, logger = None, bos_data = None ) :
    '''
    General net data collector
    Parameters:
      config -> obj : config object with all configuration ( from __init__ )
      logger -> obj : pq_logger object with all logging setup
    '''
    super().__init__( config = config, logger = logger, bos_data = bos_data)

    self.providers = { 'ioscli' : ioscli_parser(**self.general_parameters)
        }

    self.file_sources = {
        'vnicstat'  : self.providers['ioscli'].parse_vnicstat_d,
        'seastat'  : self.providers['ioscli'].parse_seastat_d
        }
    self.check_fields_to_load = [ 'low_memory', 'error_indications', 'device_driver_problem', 'adapter_problem',
                            'command_response_errors', 'reboots', 'client_completions_error', 'vf_completions_error' ]
    return(None)

#######################################################################################################################
  def load_from_db(self, db, days_to_fetch:int=1) -> dict :
    '''
    Returned data for each field:
      just_changes,avg_list(just_changes), change_rate
        [ difference between elements in list ], average_value, rate_in_which_elements changed, [ raw values within the database ]
    '''
    values_from_db = collections.defaultdict(dict)
    # Load previous entries from DB
    if db :
      now = datetime.datetime.utcnow()
      start_analysis = now - datetime.timedelta(days=days_to_fetch)
      extra_filters = [ '|> filter(fn: (r) => r["host"] == "%s")'%(self.bos_data.data['bos']['hostname']) ]
      for i in db.query("vnicstat", start_analysis.timestamp(), now.timestamp(), extra_filters=extra_filters) :
        if i['_field'] in self.check_fields_to_load :
          tdev = i['client_device_location_code']
          lkey = i['_field']
          lval = i['_value']

          if 'crq' in i :
            if 'crq' not in values_from_db[tdev] :
              values_from_db[tdev]['crq'] = {}
            if i['crq'] not in values_from_db[tdev]['crq'] :
              values_from_db[tdev]['crq'][i['crq']] = { 'rx' : {}, 'tx' : {} }

            try :
              values_from_db[tdev]['crq'][i['crq']][i['direction']][lkey][3].append(lval)
            except :
              values_from_db[tdev]['crq'][i['crq']][i['direction']][lkey] = [ None, None, None, [ lval ] ]
          else :
            try :
              values_from_db[tdev][lkey][3].append(lval)
            except :
              values_from_db[tdev][lkey] = [ None, None, None, [ lval ] ]

      for dev, dev_data in values_from_db.items() :
        for stat_type,stats in dev_data.items() :
          if stat_type == 'crq' :
            for crq,crq_data in stats.items() :
              for direction,dir_data in crq_data.items() :
                if isinstance(dir_data,list) :
                  dir_data[0], dir_data[1], dir_data[2] = get_list_avg_and_diff(dir_data[3])
          elif isinstance(stats,list) :
            stats[0], stats[1], stats[2] = get_list_avg_and_diff(stats[3])


    return(values_from_db)


#######################################################################################################################
  def health_check(self,update_from_system:bool = True, db=None, debug:bool=False,\
                   stationary_treshold:float=0.5, just_check_groups:bool=True, change_tolerance:float=0.1) -> list :
    '''
    Send health messages into server's syslog for diag purposes

    Parameters :
      update_from_system : bool = Get latest data from the local system before give any measurement
    '''
    messages = []
    values_from_db = self.load_from_db(db)

    # update stored stats
    if update_from_system :
      self.update_from_system()


    # Handle vnicstat
    for adpt,adpt_stat in self.providers['ioscli'].data['vnicstat'] :
      for st in [ 'state', 'failover_state' ] :
        if adpt_stat[st] != 'active' :
          messages += [ "The device %s has %s running as %s instead of active"%(adpt,st,adpt_stat[st]) ]

      for crq, crq_data in adpt_stat['crq'].items() :
        for md,md_data in crq_data.items() :
          for cnt in self.check_fields_to_load :
            if cnt in md_data :
              if md_data[cnt] > 0 :
                try :
                  lval = values_from_db[adpt_stat['client_device_location_code']]['crq'][crq][md][cnt][3][-1]
                  if lval != md_data[cnt] :
                    msg = "The %s under crq-%s of device %s incremented from %d to %d"%(cnt,md,adpt,lval,md_data[cnt])
                    if values_from_db[adpt_stat['client_device_location_code']]['crq'][crq][md][cnt][2] < stationary_treshold :
                      messages += [ "%s and was supposed to be stationary (treshold %f)"%(msg,values_from_db[adpt_stat['client_device_location_code']]['crq'][crq][md][cnt][2]) ]
                    elif abs(values_from_db[adpt_stat['client_device_location_code']]['crq'][crq][md][cnt][1]/md_data[cnt][-1]) > change_tolerance :
                      messages += [ "%s above the usual increment rate of %d"%(msg,values_from_db[adpt_stat['client_device_location_code']]['crq'][crq][md][cnt][1]) ]
                    elif debug :
                      messages += [ "%s and counters are %s"%(msg,str(md_data[cnt])) ]
                except :
                  messages += [ "The device %s under crq %s : %s incremented counter %s and was not possible to check within the database"%(adpt,crq,md,cnt) ]

    return(messages)
