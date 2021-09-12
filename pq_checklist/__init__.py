
#####################################################################################################################################################
## logging related functions ########################################################################################################################
#####################################################################################################################################################
def pq_logger(log_level:int=10, stdout:bool=False, name:str=__name__, to_dev_log:bool=True, dst_file = None) :
  '''
  Create and return a logger object used for logging across the program
  '''
  import importlib.util, logging, logging.handlers, os.path
  logger = logging.getLogger(name)
  if dst_file :
    if os.path.exists(os.path.dirname(dst_file)) :
      logger.addHandler(logging.handlers.RotatingFileHandler(dst_file, maxBytes=10485760, backupCount=90))
    else :
      debug_post_msg(None, 'Error when trying to use %s as logfile'%dst_file, err=True, screen_only=True, flush=True)
  if stdout == True :
    logger.addHandler(logging.StreamHandler())

  logger.setLevel(log_level)


  if to_dev_log :
    if os.path.exists('/dev/log') :
      logger.addHandler(logging.handlers.SysLogHandler(address = '/dev/log'))

    if importlib.util.find_spec('systemd') is not None :
      from systemd import journal
      logger.addHandler(journal.JournalHandler())

  return(logger)

#######################################################################################################################
def debug_post_msg(logger, msg:str, err:bool=False, screen_only:bool=False, no_screen:bool = False, \
                   end:str='\n', flush:bool=False, raise_type:bool=None) -> None:
  '''
  Parameters :
    logger      = pq_logger class or None
    msg         = Message to be send
    err         = If the message is a error or not
    screen_only = If the message shall not be sent to logger... but to stdout instead
    no_screen   = False

  Helper function to either send messages to the correct logging destionation or....
    write to a file without logger assistance

  If raise_type is defined to something different than None, it will assume that a "raise" call must be called
    at end of the function and the parameter itself is the raise parameter, tested raise_types:
      TypeError
      ValueError
      Exception
  '''
  from sys import stderr as sys_stderr
  from sys import stdout as sys_stdout

  if msg :
    if logger and not screen_only :
      if err :
        logger.error(msg)
      else :
        logger.info(msg)

    if no_screen :
      if err == True :
        dst = sys_stderr
      else :
        dst = sys_stdout

      print(msg, file=dst, end=end, flush=flush)

    if raise_type :
      raise raise_type(msg)
  return(None)


#######################################################################################################################
def try_conv_complex(string:str, avoid_complex=True) :
  '''
  Type to convert a string to a number
  If the convertion fails, return the original string
  It will try on the following order:
    int -> float -> complex

  Parameters :
    string        = String to be converted
    avoid_complex = True or False, if as last attempt try to convert to a complex type number

  Returns :
    int or float or complex or string

  '''
  try :
    return(int(string))
  except ValueError:
    try :
      return(float(string))
    except ValueError:
      try :
        if avoid_complex == False :
          return(complex(string))
        else :
          return(string)
      except ValueError:
        return(string)


#######################################################################################################################
def line_cleanup(iterable, split=False, delimiter='', cleanup = True, remove_endln = False) :
  '''
  Cleanup the contents of a iterable of a string in order to facilitate processing
  Parameters:
    iterable  : iterable or string to be processed
    split     : if attempt to split the cleaned string into a list
    delimiter : delimiter to be used when tryping to split the output string
    cleanup   : if really try to cleanup duplicated spaces and tabs
    remove_endln : If line terminator will be removed along with the cleanup ( no cr, just lf )

  Returns :
    Iterable
  '''
  import unicodedata
  ret = iterable

  for ln in iterable :
    if isinstance(ln, bytes) :
      ln = ln.decode()
    try :
      if cleanup :
        ln = ''.join(c for c in ln if not unicodedata.category(c).startswith('C'))
        while '  ' in ln :
          ln = ln.strip().replace('\t',' ').replace('  ', ' ')
      if remove_endln :
        lp = ln.split('\n')
        ln = ''.join(lp)
      if split :
        yield(ln.split(delimiter))
      else :
        yield(ln)
    except :
      yield(ln)


########################################################################################################################
# Helper to execute shell commands
def get_command_output(command=None, cwd=None, pq_logger = None, shell=False, timeout=30, ansible_module = None, \
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
    ansible_module = Try to use internal ansible module structure to run command

  Returns:
      dict with the following elements:
        { stdout  : command output, converted to a list
          stderr  : command stderr, converted to a list
          retcode : return code of the command }
  '''

  import subprocess as sp
  command_list = []
  ret = None
  if command :
    if isinstance(command, str) :
      command_list = command.split(' ')
      command_string = command
    elif isinstance(command, list) :
      command_list = command
      command_string = ' '.join(command)
    if len(command_list) > 0 :
      if ansible_module :
        try :
          rc, stdout, stderr = ansible_module.run_command(command_string, cwd=cwd, environ_update=default_env)
          ret = { 'stdout' : stdout.decode().split('\n') if stdout else [], 'stderr' : stderr.decode().split('\n') if stderr else [], 'retcode' : rc}
          if rc != 0 :
            ansible_module.fail_json(msg='Error Running command: %s'%command_string, rc=rc, stdout=stdout, stderr=stderr)

        except Exception as e :
          debug_post_msg(pq_logger, "Error when run : %s : msg : %s"%(command_string,e), err=True)
      else :
        try :
          out = sp.run(command_list, capture_output=True, shell=shell, cwd=cwd, timeout=timeout, env=default_env)
          ret = { 'stdout' : out.stdout.decode().split('\n'), 'stderr' : out.stderr.decode().split('\n'), 'retcode' : out.returncode }
        except Exception as e :
          debug_post_msg(pq_logger, "Error when run : %s : msg : %s"%(command_string,e), err=True)
  return(ret)


#######################################################################################################################
def conv_bash_var_to_dict(string, try_conv_number=False, delimiter=" ") -> dict :
  '''
  Convert bash/shell style variables into a dictionary
    Convert:
      X=1 B=ASSA C=WWW
    Into:
      { 'X' : 1, 'B' : 'ASSA', 'C' : 'WWW }

  Parameters:
    string          -> str : String to be converted
    try_conv_number -> bool : if will try to convert the string values into numbers ( using the function try_conv_complex )
    delimiter       -> str  : Delimiter that will be used when spliting the strings to be analyzed

  Returns:
    dict of processed values
  '''
  ret = dict(x.split("=") for x in string.split(delimiter))
  if try_conv_number :
    for k,v in ret.items() :
      ret[k] = try_conv_complex(v)
  return(ret)

#######################################################################################################################
def avg_list(lst:list, ndigits:int=2) :
  '''
  Calculate average value of a list
  Parameters :
    lst -> List of numbers
    ndigits -> Number of digits to be considered when rounding the number, -1 means no rouding

  Returns:
    number -> float
  '''
  ret = sum(lst)/len(lst)
  if ndigits > 0 :
    ret=round(ret, ndigits)
  return(ret)

#######################################################################################################################
def get_config(log_start=False, default_config_file='pq_checklist.conf') :
  '''
  Function to get current logging and configuration parameters
  Parameters :
    log_start           -> [True,False] : write a message at log file, informing which config file is being used
    default_config_file -> str : Default filename used for checklist files

  Returns:
    Two variables:
    config, logger
      config -> configparser object
      logger -> pq_logger object
  '''
  import configparser, os.path, shutil, logging, importlib.util

  if importlib.util.find_spec('xdg.BaseDirectory') :
    import xdg.BaseDirectory
    search_path = [ xdg.BaseDirectory.xdg_config_home ]
  elif importlib.util.find_spec('xdg') :
    import xdg
    try :
      search_path = [ str(xdg.XDG_CONFIG_HOME) ]
    except :
      search_path = [ os.getenv('HOME') ]
  else :
    search_path = [ os.getenv('HOME') ]

  search_path = search_path + [ '/etc' , '/opt/freeware/etc' ]
  config_path = None

  for ph in search_path :
    full_path = os.path.join(ph,default_config_file)
    if os.path.exists(full_path) :
      config_path = full_path
      break

  if not config_path :
    new_config_path = os.path.join(search_path[0],default_config_file)
    template_file = os.path.join(os.path.dirname(importlib.util.find_spec('pq_checklist').origin),'pq_checklist.conf.template')
    try :
      shutil.copy(template_file,new_config_path)
      config_path = new_config_path
      debug_post_msg(None, 'Configuration not found at %s, writting new one at %s'%(' '.join(search_path), new_config_path), screen_only=True, flush=True)
    except Exception as e :
      raise SystemError(e)

  config = configparser.ConfigParser()
  if not config_path :
      raise SystemError('No config file could be either located or created, need at least be able to write a new one at %s'%search_path[0])
  else :
    config.read(config_path)

    # Logging configuration
    log_level = logging.INFO
    if config['LOG']['log_level'] == "DEBUG" :
      log_level = logging.DEBUG
    log_file = None
    to_dev_log = True
    if len(config['LOG']['log_file']) > 0 :
      log_file = config['LOG']['log_file']
      to_dev_log = False
    logger = pq_logger(log_level = log_level, stdout = False, name = 'pq_checklist', to_dev_log = to_dev_log, dst_file = log_file)

    if log_start :
      debug_post_msg(logger, 'Using config file: %s'%new_config_path, screen_only=True, flush=True)

  return(config,logger)


#######################################################################################################################
def main() -> int:
  '''
  Entry point for the checklist program
  '''
  config,logger = get_config(log_start=True)
  if config['MODE'] == 'ansible' :
    from .ansible_collector import loop
    loop()
  elif config['MODE'] == 'local' :
    from .local_collector import loop
    loop()
  return(0)

if __name__ == '__main__' :
  main()

