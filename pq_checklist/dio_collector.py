from . import debug_post_msg
from .iostat import parser as iostat_parser
from .fcstat import parser as fcstat_parser
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

    self.providers = { 'iostat' : iostat_parser(**self.general_parameters),
                       'fcstat' : fcstat_parser(**self.general_parameters)
        }

    self.file_sources = {
        'iostat_AIX'  : self.providers['iostat'].parse_iostat_stats
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

    iostat = self.providers['iostat']

    if 'disk' in iostat.data['stats'] :
      # Checks for io fail
      dsk_f_w = []
      for ck in ( 'r_timeouts', 'r_fail', 'w_timeouts', 'w_fail' ) :
        if ck in iostat.data['stats'] :
          dsk_f_w += [ dsk for p,dsk in enumerate(iostat.data['stats']['disk']) if sum(iostat.data['stats'][ck][p]) > 0 ]
      messages += [ 'Disk %s presented either an io timeout or fail through iostat, check is needed'%dsk for dsk in set(dsk_f_w) ]

    return(messages)
