#!/opt/freeware/bin/python3

# All imports used
from . import debug_post_msg, try_conv_complex, line_cleanup



# All imports used
from .stats_parser import StatsParser

class bos(StatsParser) :
  def __init__(self, logger = None, ansible_module = None, cwd = '/tmp', preserv_stats = False) :
    '''
    Class with Basic OS information
    '''
    super().__init__()
    self.preserv_stats  = preserv_stats
    self.commands = {
        'lsdev_class' : "lsdev -C -H -S a -F name:class:subclass:type",
        'lsdev_loc'   : "lsdev -C -c adapter -F 'name class location physloc'",
        'lscfg'       : "lscfg",
        'oslevel_r'   : "oslevel -s",
        'oslevel_s'   : "oslevel -r",
        'uptime'      : "uptime",
        'uname'       : "uname -a",
        "instfix"     : "instfix -i",
        "lslpp_l"     : "lslpp -l",
        "lslpp_h_bos" : "lslpp -h bos.mp*",
        "emgr"        : "emgr -l",
        "lppchk"      : "lppchk -vm3",
        "audit"       : "audit query",
        "bootlist"    : "bootlist -m normal -o",
        "lssecattr"   : "lssecattr -c -F ALL",
        "lsrole"      : "lsrole -f ALL",
        "ipl_varyon"  : "ipl_varyon -i",
        "bootinfo_b"  : "bootinfo -b",
        "bootinfo_r"  : "bootinfo -r",
        "ctctrl"      : "ctctrl -q",
        "rpm_qa"      : "rpm -qa",
        "lsrsrc"      : "lsrsrc",
        "lsmcode"     : "lsmcode -A",
        "lssrc"       : "lssrc -a",
        "errpt"       : "errpt"
        }

    self.functions = {
        'lsdev_class' : self.parse_lsdev_class,
        'uname' : self.parse_uname_a
        }

    self.data = { 'dev' : {}, 'dev_class' : {}, 'bos' : {}  }
    return(None)

  def parse_uname_a(self, data:list) -> dict :
    for l in line_cleanup(data, remove_endln=True, split=True, delimiter=' ') :
      if len(l) > 4 :
        self.data['bos']['os']             = l[0].strip().lower()
        self.data['bos']['hostname']       = l[1].strip().lower()
        if self.data['bos']['os'] == "aix" :
          self.data['bos']['kernel_version'] = l[2]+l[3]
        else :
          self.data['bos']['kernel_version'] = l[2]
    return(self.data['bos'])


  def parse_lsdev_class(self, data:list) -> dict :
    for l in line_cleanup(data, remove_endln=True, split=True, delimiter=':') :
      if len(l) == 4 :
        if l[0] != "name" and l[1] != "class" :
          try :
            self.data['dev'][l[0]].update({ 'class' : l[1], 'subclass' : l[2], 'type' : l[3] })
          except :
            self.data['dev'][l[0]] = { 'class' : l[1], 'subclass' : l[2], 'type' : l[3] }
          try :
            self.data['dev_class'][l[1]].append(l[0])
          except :
            self.data['dev_class'][l[1]] = [ l[0] ]
    return(self.data['dev'])

#######################################################################################################################
#######################################################################################################################
