#!/opt/freeware/bin/python3

# All imports used
from . import debug_post_msg, try_conv_complex, avg_list
import csv, datetime, os.path



# All imports used
from .Stats_Parser import StatsParser

class parser(StatsParser) :
  def __init__(self, logger = None, cwd = '/tmp', bos_data = None):
    '''
    '''
    super().__init__(logger = logger, cwd = cwd, bos_data = bos_data)
    self.commands = { }
    self.functions = { }

    self.data = { 'vnicstat' : {} }

    self.file_sources = {
        'vnicstat' : self.parse_vnicstat_d,
    }

    self.ioscli = '/usr/ios/cli/ioscli'
    self.vnicstat = '/usr/sbin/vnicstat'

    return(None)

  def update_commands(self) :
    '''
    Update commands and functions dict
    '''
    if os.path.exists(self.ioscli) :
      self.commands['aix']['stats_fcstat_client'] = "%s fcstat -client"%self.ioscli
      self.commands['aix']['lsmap_net_all'] = "%s lsmap -net -all -fmt ':'"%self.ioscli
      self.commands['aix']['lsmap_vscsi_cust'] = "%s ioscli lsmap -fmt ':' -field svsa physloc clientid vtd lun backing -all"%self.ioscli

      for dev in self.bos_data['dev_class']['if'] :
        key = 'sea_%s'%dev
        self.commands['aix'][key] = "%s seastat -d %s -n"%(self.ioscli,dev)
        self.functions['aix'][key] = self.parse_seastat_d
      for dev in self.bos_data['dev_class']['adapter'] :
        if 'ent' in dev :
          key = 'sea_%s'%dev
          if key not in self.commands['aix'] :
            self.commands['aix'][key] = "%s seastat -d %s -n"%(self.ioscli,dev)
            self.functions['aix'][key] = self.parse_seastat_d
        elif 'vnicserver' in dev :
          self.commands['aix']['vnic_d_%s'%dev] = "%s -d %s"%(self.vnicstat, dev)
          self.functions['aix']['vnic_d_%s'%dev] = self.parse_vnicstat_d
          self.commands['aix']['vnic_b_%s'%dev] = "%s -b %s"%(self.vnicstat, dev)

    return(None)
#######################################################################################################################

  def get_measurements(self, update_from_system:bool=False) :
    ret = []
    l_time = datetime.datetime.utcnow().isoformat()
    if update_from_system :
      self.update_from_system()

    for adpt,adpt_stat in self.data['vnicstat'].items() :
      base = {  'host' : self.bos_data['bos']['hostname'] }
      base.update({ st : adpt_stat[st] for st in [ 'backing_device_name', 'client_partition_id',
                                                   'client_partition_name', 'client_operating_system',
                                                   'client_device_name', 'client_device_location_code' ]})
      for crq, crq_data in adpt_stat['crq'].items() :
        for md,md_data in crq_data.items() :
          l_tags = { **base, **{ 'crq' : crq, 'direction' : md }}
          ret.append({'measurement' : 'vnicstat', 'tags' : l_tags, 'fields' : md_data, 'time' : l_time })

    return(ret)
#######################################################################################################################
  def parse_vnicstat_d(self, data:list) :
    ret = { }
    cur_dev = ''
    crq_session = ''

    def cleanup(st,swap=False) :
      rm = ( '\n', '\t' )
      sw = ( ( ' ', '_' ), )
      ret = ''.join([ c for c in st if c not in rm ])
      ret = ret.strip()
      for sws in sw :
        ret = ret.replace(sws[0],sws[1])
      return(try_conv_complex(ret))

    for lines in data :
      nothing_done = False
      sp = lines.lower().rstrip().split(':')
      if len(sp) == 2 :
        if sp[0] == 'vnic server statistics' :
          cur_dev = cleanup(sp[1])
          ret[cur_dev] = { 'crq' : {} }
        elif sp[0] == 'state' :
          ret[cur_dev][sp[0]] = cleanup(sp[1])
        elif sp[0] in ( 'backing device name', 'failover readiness', 'failover priority', 'client partition id',
                        'client partition name', 'client operating system', 'client device name'
                        'client device location code', 'failover state', 'client device name', ) or \
              sp[0] == 'client device location code' :
          ret[cur_dev][cleanup(sp[0],swap=True)] = cleanup(sp[1])
        elif 'main crq statistics' == sp[0] :
          crq_session = 'main'
          ret[cur_dev]['crq'] = { 'main' : { 'tx' : {}, 'rx' : {} } }
        elif sp[0] in ( 'commands received', 'reboots', 'max vf descriptors queued', 'tce passed to vf ' ) :
          ret[cur_dev]['crq'][crq_session]['tx'][cleanup(sp[0],swap=True)] = cleanup(sp[1])
        elif '                                        buffer size' == sp[0] :
          ret[cur_dev]['crq'][crq_session]['rx']['buffer_size'] = cleanup(sp[1])
        else :
          nothing_done = True
      elif len(sp) == 3 :
        if 'tx sub-crq' in sp[0] :
          crq_session = sp[0].split(' ')[-1].strip() if sp[0][-1].isnumeric() else 'main'
          if crq_session not in ret[cur_dev]['crq'] :
            ret[cur_dev]['crq'][crq_session] = { 'tx' : {}, 'rx' : {} }
        else :
          sp1 = sp[1].strip().split(' ')

          val0 = cleanup(sp1[0])
          key1 = cleanup(' '.join(sp1[1:]),swap=True)
          val1 = cleanup(sp[2],swap=True)
          key0 = cleanup(sp[0],swap=True)

          if len(key0) > 0 :
            ret[cur_dev]['crq'][crq_session]['tx'][key0] = val0
          if len(key1) > 0 :
            ret[cur_dev]['crq'][crq_session]['rx'][key1] = val1

      else :
        nothing_done = False

    self.data['vnicstat'].update(ret)
    return(ret)


#######################################################################################################################
