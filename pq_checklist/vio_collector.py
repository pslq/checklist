from . import debug_post_msg
from .ioscli import parser as ioscli_parser
from .Base_collector import Base_collector

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
  def health_check(self,update_from_system:bool = True) -> list :
    '''
    Send health messages into server's syslog for diag purposes

    Parameters :
      update_from_system : bool = Get latest data from the local system before give any measurement
    '''
    messages = []
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
          for cnt in [ 'command_response_errors', 'reboots', 'client_completions_error', 'vf_completions_error' ] :
            if cnt in md_data :
              if md_data[cnt] > 0 :
                messages += [ "The device %s under crq %s : %s incremented counter %s"%(adpt,crq,md,cnt) ]


    return(messages)
