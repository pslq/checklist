from .debug_post_msg import debug_post_msg
import subprocess as sp

def get_command_output(command=None, cwd=None, pq_logger = None, shell=False, timeout=30, \
                 default_env = { 'LC_ALL' : 'C', 'PATH' : '/sbin:/etc:/bin:/usr/bin:/usr/sbin:/usr/ios/cli', 'ODMDIR' : '/etc/objrepos' }) -> dict :
  '''
  This helper works around subprocess module to execute shell commands within python3
  It encapsulate the command output on a dict object, and will decode and split the command output into a list

  Parameters:
    command   = String with the command and arguments, or a list of the same
    cwd       = working directory to be used when the command is being executed
    pq_logger = Logging object to be used
    shell     = If a shell will be spawn to execute the command
    timeout   = for how long the command will be executed before assume it hanged

  Returns:
      dict with the following elements:
        { stdout  : command output, converted to a list
          stderr  : command stderr, converted to a list
          retcode : return code of the command }
  ''' 

  command_list = []
  ret = { 'stdout' : [], 'stderr' : [], 'retcode' : -1 }
  if command :                       
    if isinstance(command, str) :
      command_list = command.split(' ')
      command_string = command
    elif isinstance(command, list) :
      command_list = command
      command_string = ' '.join(command)
    if len(command_list) > 0 :
      try :
        out = sp.run(command_list, capture_output=True, shell=shell, cwd=cwd, timeout=timeout, env=default_env)
        ret['stdout'] = out.stdout.decode().split('\n')
        ret['stderr'] = out.stderr.decode().split('\n')
        ret['retcode'] = out.returncode
      except Exception as e :
        debug_post_msg(pq_logger, "Error when run : %s : msg : %s"%(command_string,e))
  return(ret)

