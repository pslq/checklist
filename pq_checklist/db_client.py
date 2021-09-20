from . import debug_post_msg
import json, importlib
#######################################################################################################################

class db_client() :
  def __init__(self, config = None, logger = None, auto_connect:bool=False) :
    '''
    Class to handle write off data into databases or dump-files

    Parameters :
        config       -> obj  : config object
        logger       -> obj  : pq_logger object
        auto_connect -> bool : Auto connect to the database
    '''
    self.config = config
    self.logger = logger
    self.db, self.db_write_api, self.output_file = None, None, None

    if auto_connect :
      self.connect()
    return(None)

  def __enter__(self) :
    self.connect()
    return(self)

  def __exit__(self, exc_type, exc_value, exc_traceback):
    self.disconnect()
    return(None)

  def disconnect(self) :
    if self.output_file :
      self.output_file.close()
    return(None)

  def connect(self) :
    '''
    Connect to the database using directives defined into the config file

    Returns:
       Bool -> True,False  If some kind of connection or write off mech have been defined
    '''
    if importlib.util.find_spec('influxdb_client') is not None and self.config['INFLUXDB']['url'] != "<influxdb_url>" and len(self.config['INFLUXDB']['url']) > 0 :
      from influxdb_client import InfluxDBClient, Point, WritePrecision
      try :
        self.db = InfluxDBClient(**dict(config.items('INFLUXDB')))
        self.db_write_api = self.db.write_api()
      except Exception as e :
        debug_post_msg(self.logger,'Error connecting to influxDB: %s'%e)
    if ( self.logger.getEffectiveLevel() <= 10 or not self.db_write_api ) and len(self.config['INFLUXDB']['dump_file']) :
      try :
        self.output_file = open(self.config['INFLUXDB']['dump_file'], 'a+')
      except Exception as e :
        debug_post_msg(self.logger,'Error opening dump file: %s'%e, raise_type=Exception)
      debug_post_msg(self.logger,'InfluxDB not configured or influxdb_client not installed, or loglevel set to debug. Queries will be saved at dumpfile')
    return(None)


  def write(self,msg:list, dumpfile_only = False, db_only = False) -> bool :
    '''
    Write data into influxdb or dumpfile in order to perform further analysis

    Parameters:
      msg : list -> list of messages that will be written
      dumpfile_only : bool -> write only to the dump file
      db_only : bool -> write only to the database

    Returns:
      bool -> True,False in case it works or not
    '''
    ret = False
    try :
      if self.db_write_api and not dumpfile_only :
        try :
          self.db_write_api.write(self.config['INFLUXDB']['bucket'],  self.config['INFLUXDB']['org'], msg)
          ret = True
        except Exception as e :
          debug_post_msg(self.logger, 'Error writing data to influxdb: %s'%e, raise_type=Exception)
      if self.output_file and not db_only :
        try :
          self.output_file.write(json.dumps(msg))
          if not ret and not self.db_write_api :
            ret = True
        except Exception as e :
          debug_post_msg(self.logger, 'Error writing data to dumpfile : %s'%e, raise_type=Exception)
    except Exception as e :
      debug_post_msg(self.logger, 'Error writing data : %s'%e, raise_type=Exception)
    return(ret)
