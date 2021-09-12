#!/opt/freeware/bin/python3

# All imports used
from . import debug_post_msg, try_conv_complex, line_cleanup



# All imports used
from .stats_parser import StatsParser

class bos(StatsParser) :
  def __init__(self, logger = None, ansible_module = None, cwd = '/tmp', preserv_stats = False) :
    '''

    '''
    super().__init__()
    self.preserv_stats  = preserv_stats
    self.commands = {
        'lsdev_loc'   : "lsdev -C -c adapter -F 'name class location physloc'",
        'lsdev_class' : "lsdev -C -H -S a -F 'name class subclass type'",
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
        'lsdev_class' : self.parse_lsdev_class
        }

    self.data = { 'dev' : {}, 'dev_class' : {} }
    return(None)


  def parse_lsdev_class(self, data:list) -> dict :
    for l in line_cleanup(data, remove_endln=True, split=True, delimiter=' ') :
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
