from .. import try_conv_complex

def cleanup(st,swap=False) :
  rm = ( '\n', '\t' )
  sw = ( ( ' ', '_' ), )
  ret = ''.join([ c for c in st if c not in rm ])
  ret = ret.strip()
  for sws in sw :
    ret = ret.replace(sws[0],sws[1])
  return(try_conv_complex(ret))


def parse_seastat_d(data:list, debug:bool=False) -> dict :
  ret = {}
  cur_dev = ''
  hwaddr = ''
  vlans = {}

  for line in data :
    if ':' in line :
      sp = line.strip().split(':')
      key = sp[0].strip()
      if key == 'Device Name' :
        cur_dev = sp[1].strip()
        ret[cur_dev] = { 'vlan' : {}, 'mac' : {} }
      elif sp[0] == "MAC" :
        hwaddr = line.split(' ')[1].strip().lower()
        if hwaddr not in ret[cur_dev]['mac'] :
          ret[cur_dev]['mac'][hwaddr] = { 'tx' : { 'pkg' : 0, 'bytes' : 0},
                                          'rx' : { 'pkg' : 0, 'bytes' : 0},
                                          'ipaddr' : None, 'hostname' : None, 'vlan' : 1, 'vlan_prio' : 0 }
      elif sp[0] == "VLAN" :
        ret[cur_dev]['mac'][hwaddr]['vlan'] = cleanup(sp[1])
      elif sp[0] == "VLAN Priority" :
        ret[cur_dev]['mac'][hwaddr]['vlan_prio'] = cleanup(sp[1])
      elif sp[0] == "Hostname" :
        ret[cur_dev]['mac'][hwaddr]['hostname'] = sp[1].strip()
      elif sp[0] == "IP" :
        ret[cur_dev]['mac'][hwaddr]['ipaddr'] = sp[1].strip()
      elif sp[0] in [ "Packets", "Bytes" ] :
        if sp[0] == "Packets" :
          tgt = 'pkg'
        elif sp[0] == "Bytes" :
          tgt = 'bytes'

        v1 = cleanup(sp[1].strip().split(' ')[0].strip())
        v2 = cleanup(sp[2].strip())
        ret[cur_dev]['mac'][hwaddr]['tx'][tgt] += v1
        ret[cur_dev]['mac'][hwaddr]['rx'][tgt] += v2
      elif debug :
        print(sp)

  for dev,dev_data in ret.items() :
    for mac,mac_data in dev_data['mac'].items() :
      tgt_vlan = mac_data['vlan']
      for mode in [ 'tx', 'rx' ] :
        if tgt_vlan not in ret[cur_dev]['vlan'] :
          ret[cur_dev]['vlan'][tgt_vlan] = { 'tx' : {'pkg' : 0, 'bytes' : 0 }, 'rx' : {'pkg' : 0, 'bytes' : 0 } }
        ret[cur_dev]['vlan'][tgt_vlan][mode]['pkg'] += mac_data[mode]['pkg']
        ret[cur_dev]['vlan'][tgt_vlan][mode]['bytes'] += mac_data[mode]['bytes']

  return(ret)
