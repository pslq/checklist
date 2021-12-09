from . import debug_post_msg
from .ioscli import parser as ioscli_parser
from .Base_collector import Base_collector
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

    self.providers = { 'ioscli' : ioscli_parser(**self.general_parameters)
        }

    self.file_sources = {
        'vnicstat'  : self.providers['ioscli'].parse_vnicstat_d,
        'seastat'  : self.providers['ioscli'].parse_seastat_d
        }
    return(None)

#######################################################################################################################
  def health_check(self,update_from_system:bool = True, db=None) -> list :
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

    # Load previous entries from DB
    if db :
      now = datetime.datetime.utcnow()
      start_analysis = now - datetime.timedelta(days=1)
      extra_filters = [ '|> filter(fn: (r) => r["host"] == "%s")'%(self.bos_data.data['bos']['hostname']) ]
      for i in db.query("vnicstat", start_analysis.timestamp(), now.timestamp(), extra_filters=extra_filters) :
        if i['_field'] in [ 'low_memory', 'error_indications', 'device_driver_problem', 'adapter_problem',
                            'command_response_errors', 'reboots', 'client_completions_error', 'vf_completions_error' ] :
          tdev = i['client_device_location_code']
          lkey = i['_field']
          lval = i['_value']

          if 'crq' in i :
            if 'crq' not in values_from_db[tdev] :
              values_from_db[tdev]['crq'] = {}
            if i['crq'] not in values_from_db[tdev]['crq'] :
              values_from_db[tdev]['crq'][i['crq']] = { 'rx' : {}, 'tx' : {} }

            try :
              values_from_db[tdev]['crq'][i['crq']][i['direction']][lkey].append(lval)
            except :
              values_from_db[tdev]['crq'][i['crq']][i['direction']][lkey] = [ lval ]
          else :
            try :
              values_from_db[tdev][lkey].append(lval)
            except :
              values_from_db[tdev][lkey] = [ lval ]

    # Handle vnicstat
    for adpt,adpt_stat in self.providers['ioscli'].data['vnicstat'] :
      for st in [ 'state', 'failover_state' ] :
        if adpt_stat[st] != 'active' :
          messages += [ "The device %s has %s running as %s instead of active"%(adpt,st,adpt_stat[st]) ]

      for crq, crq_data in adpt_stat['crq'].items() :
        for md,md_data in crq_data.items() :
          for cnt in [ 'low_memory', 'error_indications', 'device_driver_problem', 'adapter_problem',
                       'command_response_errors', 'reboots', 'client_completions_error', 'vf_completions_error' ] :
            if cnt in md_data :
              if md_data[cnt] > 0 :
                try :
                  if values_from_db[adpt_stat['client_device_location_code']]['crq'][crq][md][cnt][-1] != md_data[cnt] :
                    messages += [ "The device %s under crq %s : %s incremented counter %s"%(adpt,crq,md,cnt) ]
                except :
                  messages += [ "The device %s under crq %s : %s incremented counter %s and was not possible to check within the database"%(adpt,crq,md,cnt) ]


    return(messages)
