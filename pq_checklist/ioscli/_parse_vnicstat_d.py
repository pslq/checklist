from .. import try_conv_complex

def cleanup(st,swap=False) :
  rm = ( '\n', '\t' )
  sw = ( ( ' ', '_' ), )
  ret = ''.join([ c for c in st if c not in rm ])
  ret = ret.strip()
  for sws in sw :
    ret = ret.replace(sws[0],sws[1])
  return(try_conv_complex(ret))

def parse_vnicstat_d(data:list) :
  ret = { }
  cur_dev = ''
  crq_session = ''

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
          if key0 != 'tx' :
            ret[cur_dev]['crq'][crq_session]['tx'][key0] = val0
        if len(key1) > 0 :
          ret[cur_dev]['crq'][crq_session]['rx'][key1] = val1
    else :
      nothing_done = False
  return(ret)

