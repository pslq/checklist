#!/opt/freeware/bin/python3

from .. import debug_post_msg, try_conv_complex, avg_list
import csv, datetime, os.path

# All imports used
from ..Stats_Parser import StatsParser
from ._parse_vnicstat_d import parse_vnicstat_d
from ._parse_seastat_d import parse_seastat_d

class parser(StatsParser) :
  def __init__(self, logger = None, cwd = '/tmp', bos_data = None, samples = 2, interval = 1):
    '''
    '''
    super().__init__(logger = logger, cwd = cwd, bos_data = bos_data)

    self.data = { 'vnicstat' : {}, 'seastat' : {} }

    self.file_sources = {
        'vnicstat' : self.parse_vnicstat_d,
        'seastat' : self.parse_seastat_d,
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

    # Handle seastat
    for adpt,adpt_stat in self.data['seastat'].items() :
      for vlan,vlan_data in adpt_stat['vlan'].items() :
        ret.append({'measurement' : 'seastat_vlan',
          'tags' : { 'host' : self.bos_data['bos']['hostname'], 'adapter' : adpt, 'vlan' : vlan },
          'fields' : { 'tx_pkg' : vlan_data['tx']['pkg'], 'tx_bytes' : vlan_data['tx']['bytes'],
                       'rx_pkg' : vlan_data['rx']['pkg'], 'rx_bytes' : vlan_data['rx']['bytes'] },
          'time' : l_time })
      for mac,mac_data in adpt_stat['mac'].items() :
        l_tags = { 'host' : self.bos_data['bos']['hostname'], 'adapter' : adpt, 'mac' : mac }
        if mac_data['hostname'] :
          l_tags['hostname'] = mac_data['hostname']
        if mac_data['ipaddr'] :
          l_tags['ipaddr'] = mac_data['ipaddr']

        ret.append({'measurement' : 'seastat_mac', 'tags' : l_tags,
          'fields' : { 'tx_pkg' : mac_data['tx']['pkg'], 'tx_bytes' : mac_data['tx']['bytes'],
                       'rx_pkg' : mac_data['rx']['pkg'], 'rx_bytes' : mac_data['rx']['bytes'] },
          'time' : l_time })


    return(ret)
#######################################################################################################################
  def parse_seastat_d(self, data:list) :
    ret = parse_seastat_d(data)
    self.data['seastat'].update(ret)
    return(self.data['seastat'])
#######################################################################################################################
  def parse_vnicstat_d(self, data:list) :
    ret = parse_vnicstat_d(data)
    self.data['vnicstat'].update(ret)
    return(self.data['vnicstat'])
#######################################################################################################################
