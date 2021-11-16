#!/opt/freeware/bin/python3

# All imports used
from .Stats_Parser import StatsParser
from . import avg_list, debug_post_msg, pq_round_number, line_cleanup, try_conv_complex
import datetime

class parser(StatsParser) :
  def __init__(self, logger = None, samples = 2, interval = 1, cwd = '/tmp', bos_data = None) :
    super().__init__(logger = logger, cwd = cwd, bos_data=bos_data)

    self.file_sources = { 'fcstat' : self.parse_fcstat_e_from_dict }
    # Internal list to hold all keys used when parsing stats data
    self.data['stats'] = {}

    return(None)

#######################################################################################################################
  def update_commands(self) :
    '''
    Update commands and functions dict
    '''
    try :
      # In case self.commands and self.functions hasn't been populated yet
      if self.bos_data.data['bos']['os'] == "aix" :
        for dev in self.bos_data['dev_class']['adapter'] :
          if 'fcs' in dev :
            key = 'stats_%s'%dev
            self.commands['aix'][key] = "fcstat -e %s"%dev
            self.functions['aix'][key] = self.parse_fcstat_stats
    except Exception as e :
      debug_post_msg(self.logger, 'Error loading device specific commands, possibly bos_data not initialized : %s'%e, raise_type=Exception)


    return(None)


#######################################################################################################################
  def get_measurements(self, elements = [ 'stats' ], consolidate_function = avg_list, update_from_system:bool=True) :
    ret = []
    cur_time = datetime.datetime.utcnow().isoformat()
    if update_from_system :
      self.update_from_system(elements = elements)

    for adpt,adpt_data in self.data['stats'].items() :
      try :
        tmp_dct = {}
        for i in [ 'transmit_frames', 'receive_frames', 'transmit_words', 'receive_words', 'lip_count', 'nos_count',
                   'error_frames', 'dumped_frames', 'link_failure_count', 'loss_of_sync_count', 'loss_of_signal',
                   'primitive_seq_protocol_error_count', 'invalid_tx_word_count', 'invalid_crc_count' ] :
          tmp_dct[i] = adpt_data[i]
        ret.append({'measurement' : 'fcstat_general',
                    'tags' : { 'host' : self.bos_data['bos']['hostname'], 'adapter' : adpt },
                    'fields' : tmp_dct,
                    'time' : cur_time })
        for i in 'fc_scsi_adapter_driver_information', 'fc_scsi_traffic_statistics' :
          ret.append({'measurement' : 'fcstat_%s'%i,
                      'tags' : { 'host' : self.bos_data['bos']['hostname'], 'adapter' : adpt },
                      'fields' : adpt_data[i],
                      'time' : cur_time })
      except Exception as e :
        debug_post_msg('Error parsing fcstat data: %s'%e)
    return(ret)


#######################################################################################################################
  def parse_fcstat_e_from_dict(self, data:dict) :
    for adapter,adapter_data in data.items() :
      self.parse_fcstat_stats(adapter_data.split('\n'))
    return(None)


#######################################################################################################################
  def parse_fcstat_stats(self, data:list) :
    ret = {}
    lns = []
    adapter = ''
    inner_key = ''

    def __str_fix__(st:str) :
      '''
      Inner function to handle string cleanup
      '''
      rt = st.lower().strip(' ')
      for i in [ (' ', '_'), ('/', '_'), (',','.'), ('%',''), ('(', '_'), (')', '_') ] :
        rt = rt.replace(i[0],i[1])
      rt.strip('_')
      return(rt)

    for dt in data :
      if dt.count('\n') > 1 :
        lns += dt.split('\n')
      else :
        lns += [ dt ]
    for dt in line_cleanup(data, split=True, delimiter=':', cleanup=True, remove_endln=True) :
      if len(dt) == 1 :
        if dt[0] in [ 'FC SCSI Adapter Driver Information',
                      'FC SCSI Traffic Statistics' ] :
          inner_key = __str_fix__(dt[0])
          ret[adapter][inner_key] = {}
      if len(dt) == 2 :
        key = __str_fix__(dt[0])
        value = __str_fix__(dt[1])

        if len(value) > 0 :
          if 'FIBRE CHANNEL STATISTICS REPORT' in dt[0] :
            adapter = dt[1].strip()
            inner_key = ''
            ret[adapter] = {}
          elif dt[0] in [ 'Frames', 'Words' ] :
            i_dt = dt[1].strip().split(' ')
            k_0 = 'transmit_%s'%(__str_fix__(dt[0]))
            k_1 = 'receive_%s'%(__str_fix__(dt[0]))
            ret[adapter][k_0] = try_conv_complex(i_dt[0])
            ret[adapter][k_1] = try_conv_complex(i_dt[1])
          elif len(inner_key) > 0 :
            ret[adapter][inner_key][key] = try_conv_complex(value)
          else :
            ret[adapter][key] = try_conv_complex(value)
    self.data['stats'].update(ret)
    return(ret)


#######################################################################################################################
#######################################################################################################################
