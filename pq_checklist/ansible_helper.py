import os, os.path, shutil, importlib, sys
'''
Helper functions to run remote commands through Ansible using ansible_runner module
'''

if not importlib.util.find_spec('ansible_runner') :
  raise Exception('ansible_runner module not found')
  sys.exit(1)
else :
  import ansible_runner

#######################################################################################################################
#######################################################################################################################

def __cleanup_artifacts__(private_data_dir:str) -> None :
  '''
  Cleanup artifacts after they're not needed anymore

  Parameters:
      private_data_dir: str -> Ansible private dir which holds the artifacts
  '''
  target_dir = os.path.join(private_data_dir, "artifacts")
  if os.path.exists(target_dir):
    for d in os.scandir(target_dir) :
      shutil.rmtree(d.path)
  return(None)


#######################################################################################################################
def script_runner(script_name = None, host_target = None, private_data_dir:str = 'playbooks', \
                  quiet:bool = True, cleanup_artifacts:bool = True) -> dict :
  '''
  Run local scripts on target host group

  Parameters:
     script_name       : Name of the shell script, can be a single script or a list of scripts
     host_target       : target host group where the script will be executed
     private_data_dir  : Ansible private dir ( base directory to look for scripts and ansible config
     quiet -> bool     : [True,False] If run on quiet mode or not
     cleanup_artifacts : [True,False] Cleanup artifacts after completed

  Returns:
    dict with contents:
     { 'runner' : ansible_runner object that was used to execute the script,
       'results' : dict with host keys and in each key a list of of results
     }
  '''
  ret = { 'results' : {} }
  if isinstance(script_name, str) :
    script = [ script_name ]
  else :
    script = script_name

  for s in script :
    ret['runner'] = ansible_runner.run(
      host_pattern=host_target,
      private_data_dir=private_data_dir,
      module='script',
      quiet=quiet,
      module_args=s
    )
    for ro in ret['runner'].events :
      if ro['event'] == 'runner_on_ok' :
        try :
          try :
            ret['results'][ro['event_data']['host']].append(
                { 'script_name' : s,
                  'end' : ro['event_data']['end'],
                  'rc' : ro['event_data']['res']['rc'], 'out' : ro['event_data']['res']['stdout_lines']
                })
          except :
            ret['results'][ro['event_data']['host']] = [
                { 'script_name' : s, 'end' : ro['event_data']['end'],
                  'rc' : ro['event_data']['res']['rc'], 'out' : ro['event_data']['res']['stdout_lines']
                } ]
        except :
          pass
  if cleanup_artifacts :
    __cleanup_artifacts__(private_data_dir)

  return(ret)

#######################################################################################################################
#######################################################################################################################
def playbook_runner(playbook = None, host_limit = None, private_data_dir:str = 'playbooks', quiet:bool = True, \
                    wanted_outputs:list = [], cleanup_artifacts:bool = True, output_specific_data:dict = {} ) :
  '''
  Run a Ansible playbook on a group of hosts presented on either the playbook or limited by the host_group

  Parameters:
    playbook          : playbook file to be executed
    host_limit        : limit execution to a certain amount of hosts within the ansible hosts
    private_data_dir  : ansible private dir
    quiet             : Run on quiet mode or not
    wanted_outputs    : Which outputs of the playbook will be stored within the results return dict
    cleanup_artifacts : If artifacts should be cleaned up after playbook execution
    output_specific_data : dict with a list of objects expected by each task

  Returns:
    dict with contents:
     { 'runner' : ansible_runner object that was used to execute the script,
       'results' : dict with host keys and in each key a list of of results
     }

  '''
  ret = { 'results' : {}, 'rc' : -1 }
  parms = { 'playbook' : playbook, 'private_data_dir' : private_data_dir, 'quiet' : quiet }
  if host_limit :
    parms['limit'] = host_limit

  ret['runner'] = ansible_runner.run(**parms)
  ret['rc'] = ret['runner'].rc
  if ret['runner'].rc == 0 :
    for ro in ret['runner'].events :
      if ro['event'] == 'runner_on_ok' :
        if ro['event_data']['task'] in wanted_outputs or len(wanted_outputs) == 0 :
          expected_keys = [ 'stdout_lines' ]
          if ro['event_data']['task']  in output_specific_data.keys() :
            expected_keys += output_specific_data[ro['event_data']['task']]

          try :
            data = { 'task' : ro['event_data']['task'] , 'rc' : ro['event_data']['res']['rc'], 'end' : ro['event_data']['end'] }
          except :
            data = { 'task' : ro['event_data']['task'] , 'rc' : -1,                            'end' : '' }

          for k in expected_keys :
            try :
              data[k] = ro['event_data']['res'][k]
            except :
              pass
          try :
            ret['results'][ro['event_data']['host']].append(data)
          except :
            ret['results'][ro['event_data']['host']] = [ data ]

  if cleanup_artifacts :
    __cleanup_artifacts__(private_data_dir)
  return(ret)

#######################################################################################################################
def ping(host_target = None, private_data_dir:str = 'playbooks', \
         quiet:bool = True, cleanup_artifacts:bool = True) -> dict :
  '''
  Run local scripts on target host group

  Parameters:
     host_target       : target host group where the script will be executed
     private_data_dir  : Ansible private dir ( base directory to look for scripts and ansible config
     quiet -> bool     : [True,False] If run on quiet mode or not
     cleanup_artifacts : [True,False] Cleanup artifacts after completed

  Returns:
    dict with contents:
     { 'runner' : ansible_runner object that was used to execute the script,
       'results' : dict with host keys and in each key a list of of results
     }
  '''
  ret = { 'results' : {} }

  ret['runner'] = ansible_runner.run(
    host_pattern=host_target,
    private_data_dir=private_data_dir,
    module='script',
    quiet=quiet,
    module_args=s
  )
  for ro in ret['runner'].events :
    if ro['event'] == 'runner_on_ok' :
      try :
        try :
          ret['results'][ro['event_data']['host']].append(
              { 'script_name' : s,
                'end' : ro['event_data']['end'],
                'rc' : ro['event_data']['res']['rc']
              })
        except :
          ret['results'][ro['event_data']['host']] = [
              { 'script_name' : s, 'end' : ro['event_data']['end'],
                'rc' : ro['event_data']['res']['rc']
              } ]
      except :
        pass
  if cleanup_artifacts :
    __cleanup_artifacts__(private_data_dir)

  return(ret)

