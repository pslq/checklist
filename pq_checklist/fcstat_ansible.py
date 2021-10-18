#!/opt/freeware/bin/python3

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
  Simple module to get fcstat for all interfaces on the server
'''

EXAMPLES = r'''
  No parameter is needed
'''

RETURN = r'''
  Return a list of adapters and a dict with all stats
'''

def main():
  from ansible.module_utils.basic import AnsibleModule
  import os
  module = AnsibleModule( supports_check_mode=False, argument_spec = {})
  result = {
      'changed' : False,
      'rc' : 0,
      'stdout_lines' : {},
      'adapters' : []
      }

  if 'aix' in os.sys.platform :
    # Get Adapter list
    rc, stdout, stderr = module.run_command("lsdev -C -H -S a -F name:class:subclass:type")
    if rc == 0 :
      for l in stdout.split('\n') :
        lp = l.strip().split(':')
        if len(lp) == 4 :
          if any([ True for st in ( 'fcs' ) if st in lp[0]]) and lp[1] in ( "adapter" ) :
            result['adapters'].append(lp[0])

    # Get Stats for these adapters
    for adpt in result['adapters'] :
      rc, stdout, stderr = module.run_command("fcstat -e %s"%adpt)
      if rc == 0 :
        result['stdout_lines'][adpt] = stdout
    if len(result['stdout_lines']) == 0 :
      result['msg'] = 'No adapter with stats found'
      result['rc'] = -1
  else :
    result['rc'] = -1

  # Return data
  if result['rc'] != 0 :
    module.fail_json(**result)
  else :
    result['changed'] = True
    result['msg'] = 'ok'
  module.exit_json(**result)


if __name__ == '__main__':
    main()
