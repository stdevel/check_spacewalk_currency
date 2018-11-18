#!/usr/bin/python

# check_spacewalk_currency.py - a script for
# currency of systems managed by Spacewalk,
# Red Hat Satellite 5.x or SUSE Manager
#
# 2016 By Christian Stankowic
# <info at stankowic hyphen development dot net>
# https://github.com/stdevel
#

from optparse import OptionParser, OptionGroup
import getpass
import logging
import xmlrpclib
import os
import stat
import getpass
import math
import sys

#some global variables
state=0
system_currency = {}
system_stats = {}



#setting logger and supported API levels
LOGGER =  logging.getLogger('spacewalk-currency')
SUPPORTED_API_LEVELS = ["11.1", "12", "13", "13.0", "14", "14.0", "15", "15.0", "16", "16.0", "17", "17.0", "18", "18.0", "19", "19.0", "20", "20.0", "21", "21.0"]



class APILevelNotSupportedException(Exception):
    pass



def check_if_api_is_supported(client):
#check whether API is supported
    api_level = client.api.getVersion()
    if api_level not in SUPPORTED_API_LEVELS:
        raise APILevelNotSupportedException(
            "Your API version ({0}) does not support the required calls. "
            "You'll need API version 1.8 (11.1) or higher!".format(api_level)
        )
    else:
        LOGGER.debug("Supported API version (" + api_level + ") found.")



def get_credentials(type, input_file=None):
#retrieve credentials
    if input_file:
        LOGGER.debug("Using authfile")
        try:
            # check filemode and read file
            filemode = oct(stat.S_IMODE(os.lstat(input_file).st_mode))
            if filemode == "0600":
                LOGGER.debug("File permission matches 0600")
                with open(input_file, "r") as auth_file:
                    s_username = auth_file.readline().replace("\n", "")
                    s_password = auth_file.readline().replace("\n", "")
                return (s_username, s_password)
            else:
                LOGGER.warning("File permissions (" + filemode + ") not matching 0600!")
                #sys.exit(1)
        except OSError:
		LOGGER.warning("File non-existent or permissions not 0600!")
		#sys.exit(1)
        	LOGGER.debug("Prompting for login credentials as we have a faulty file")
		s_username = raw_input(type + " Username: ")
		s_password = getpass.getpass(type + " Password: ")
		return (s_username, s_password)
    elif type.upper()+"_LOGIN" in os.environ and type.upper()+"_PASSWORD" in os.environ:
	# shell variables
	LOGGER.debug("Checking shell variables")
	return (os.environ[type.upper()+"_LOGIN"], os.environ[type.upper()+"_PASSWORD"])
    else:
	# prompt user
	LOGGER.debug("Prompting for login credentials")
	s_username = raw_input(type + " Username: ")
	s_password = getpass.getpass(type + " Password: ")
	return (s_username, s_password)



def set_code(int):
	#set result code
	global state
	if int > state: state = int



def get_return_str():
	#get return string
	if state == 3: return "UNKNOWN"
	elif state == 2: return "CRITICAL"
	elif state == 1: return "WARNING"
	else: return "OK"



def check_value(val, desc, warn, crit):
	#compares value to thresholds and sets codes
	LOGGER.debug("Comparing '{0}' ({1}) to warning/critical thresholds {2}/{3})".format(val, desc, warn, crit))
	snip=""
	if val > crit:
		#critical
		snip="{0} critical ({1})".format(desc, val)
		set_code(2)
	elif val > warn:
		#warning
		snip="{0} warning ({1})".format(desc, val)
		set_code(1)
	else: snip="{0} okay ({1})".format(desc, val)
	return snip



def check_stats():
	#check statistics
	LOGGER.debug("System statistics is: {0}".format(str(system_stats)))
	
	#calculate absolute thresholds
	options.inactive_warn = int( math.ceil( float(system_stats["total"])*(float(options.inactive_warn)/100) ))
	options.inactive_crit = int( math.ceil( float(system_stats["total"])*(float(options.inactive_crit)/100) ))
	options.outdated_warn = int( math.ceil( float(system_stats["total"])*(float(options.outdated_warn)/100) ))
	options.outdated_crit = int( math.ceil( float(system_stats["total"])*(float(options.outdated_crit)/100) ))
	LOGGER.debug("Absolute thresholds for inactive (warning/critical): {0}/{1}".format(options.inactive_warn, options.inactive_crit))
	LOGGER.debug("Absolute thresholds for outdated (warning/critical): {0}/{1}".format(options.outdated_warn, options.outdated_crit))
	
	#check values
	result="{0}, {1}".format(
		check_value(int(system_stats["outdated"]), "outdated systems", options.outdated_warn, options.outdated_crit),
		check_value(int(system_stats["inactive"]), "inactive systems", options.inactive_warn, options.inactive_crit)
	)
	
	#set performance data
	if options.show_perfdata:
		perfdata = " | "
		perfdata_snip = ("{0}"
				"'sys_total'={1};;;; "
				"'sys_outdated'={2};{3};{4};; "
				"'sys_inact'={5};{6};{7};;")
		perfdata = perfdata_snip.format(
			perfdata,
			system_stats["total"],
			system_stats["outdated"], options.outdated_warn, options.outdated_crit,
			system_stats["inactive"], options.inactive_warn, options.outdated_warn
		)
		LOGGER.debug("DEBUG: perfdata is:\n{0}".format(str(perfdata)))
	else: perfdata=""
	
	#return result and die in a fire
	print "{0}: {1}{2}".format(get_return_str(), result, perfdata)
        exit(state)



def check_systems():
	#check _all_ the systems
	global system_currency
	snip_total=""
	snip_crit=""
	snip_bugs=""
	hostname=""
	
	for entry in system_currency:
		hostname=entry['hostname']
		#set prefix
		if len(system_currency) > 1: this_prefix = "{0} ".format(hostname)
		else: this_prefix = ""
		
		#total package updates
		if options.total_warn and options.total_crit:
			snip_total = "{0}{1}".format(snip_total, check_value(
				entry['all'],
				"{0}total updates".format(this_prefix),
				options.total_warn, options.total_crit
			))
		
		#critical package updates
		snip_crit = "{0}{1}".format(snip_crit, check_value(
			int(entry['imp'] + entry['crit'] + entry['mod']),
			"{0}critical updates".format(this_prefix),
			options.security_warn, options.security_crit
		))
		
		#bug fixes
		snip_bugs = "{0}{1}".format(snip_bugs, check_value(
			entry['bug'],
			"{0}bug fixes".format(this_prefix),
			options.bugs_warn, options.bugs_crit
		))
		
	#generate perfdata
	if options.show_perfdata:
		#generate perfdata
		perfdata=" | "
		
		for entry in system_currency:
			#set prefix
			if len(system_currency) > 1: this_prefix = "{0}_".format(entry['hostname'])
			else: this_prefix = ""
			
			perfdata_snip = ("{0}"
			"'{1}crit_pkgs'={2};{3};{4};; "
			"'{5}imp_pkgs'={6};{7};{8};; "
			"'{9}mod_pkgs'={10};{11};{12};; "
			"'{13}low_pkgs'={14};;;; "
			"'{15}enh_pkgs'={16};;;; "
			"'{17}bug_pkgs'={18};{19};{20};; "
			"'{21}all_pkgs'={22};{23};{24};; "
			"'{25}score'={26};;;;")
			if not options.total_warn or not options.total_crit:
				options.total_warn = "";
				options.total_crit = "";
			perfdata = perfdata_snip.format(
				perfdata,
				this_prefix, int(entry['crit']), int(options.security_warn), int(options.security_crit),
				this_prefix, int(entry['imp']), int(options.security_warn), int(options.security_crit),
				this_prefix, int(entry['mod']), int(options.security_warn), int(options.security_crit),
				this_prefix, int(entry['low']),
				this_prefix, int(entry['enh']),
				this_prefix, int(entry['bug']), int(options.bugs_warn), int(options.bugs_crit),
				this_prefix, int(entry['all']), options.total_warn, options.total_crit,
				this_prefix, int(entry['score'])
			)
		LOGGER.debug("DEBUG: perfdata is:\n{0}".format(str(perfdata)))
	else: perfdata=""
	
	#return result
	snips = [x for x in [snip_total, snip_crit, snip_bugs] if x != ""]
	if len(options.system) > 1: hostname=''
	else: hostname="{0}{1}".format(" for ", hostname)
	print "{0}: {1}{2}{3}".format(get_return_str(), str(", ".join(snips)), hostname, perfdata)
	exit(state)



def get_currency_data(stats_only=False):
	#get _all_ the currency or statistics data
	global system_currency
	global system_stats
	
	(username, password) = get_credentials("Satellite", options.authfile)
	satellite_url = "http://{0}/rpc/api".format(options.server)
	client = xmlrpclib.Server(satellite_url, verbose=options.debug)

        try:
            key = client.auth.login(username, password)
            check_if_api_is_supported(client)
            
            if stats_only:
                    #statistics only
                   system_stats["total"] = len(client.system.listSystems(key))
                   system_stats["inactive"] = len(client.system.listInactiveSystems(key))
                   system_stats["outdated"] = len(client.system.listOutOfDateSystems(key))
            else:
                    #currency data only
                    system_currency = client.system.getSystemCurrencyScores(key)
                    
                    #append hostname
                    counter=0
                    for system in system_currency:
                            system_sid = client.system.getName(key, system['sid'])
                            LOGGER.debug("DEBUG: Hostname for SID '{0}' seems to be '{1}'".format(system['sid'], system_sid['name']))
                            system['hostname']=system_sid['name']
                            #get total package counter
                            upgradable_pkgs = client.system.listLatestUpgradablePackages(key, system['sid'])
                            if(len(upgradable_pkgs)>0): system['all']=len(upgradable_pkgs)-1
                            else: system['all']=0
                            #drop host if not requested
                            if options.all_systems == False:
                                    if system['hostname'] not in options.system: system_currency[counter]=None
                            counter=counter+1
                    #clean removed hosts
                    system_currency = [system for system in system_currency if system != None]
        except:
            print("Unauthenticated.")
            sys.exit(1)



if __name__ == "__main__":
	#define description, version and load parser
	desc='''%prog is used to check systems managed by Spacewalk, Red Hat Satellite 5.x or SUSE Manager for outstanding patches. Login credentials are assigned using the following shell variables:
	SATELLITE_LOGIN  username
	SATELLITE_PASSWORD  password
	
	It is also possible to create an authfile (permissions 0600) for usage with this script. The first line needs to contain the username, the second line should consist of the appropriate password. If you're not defining variables or an authfile you will be prompted to enter your login information.
	
	Checkout the GitHub page for updates: https://github.com/stdevel/check_spacewalk_currency'''
	parser = OptionParser(description=desc,version="%prog version 0.5.6")
	
	gen_opts = OptionGroup(parser, "Generic options")
	space_opts = OptionGroup(parser, "Spacewalk options")
	system_opts = OptionGroup(parser, "System options")
	stat_opts = OptionGroup(parser, "Statistic options")
	parser.add_option_group(gen_opts)
	parser.add_option_group(space_opts)
	parser.add_option_group(system_opts)
	parser.add_option_group(stat_opts)
	
	#-d / --debug
	gen_opts.add_option("-d", "--debug", dest="debug", default=False, action="store_true", help="enable debugging outputs")
	
	#-P / --show-perfdata
	gen_opts.add_option("-P", "--show-perfdata", dest="show_perfdata", default=False, action="store_true", help="enables performance data (default: no)")
	
	#-a / --authfile
	space_opts.add_option("-a", "--authfile", dest="authfile", metavar="FILE", default="", help="defines an auth file to use instead of shell variables")
	
	#-s / --server
	space_opts.add_option("-s", "--server", dest="server", metavar="SERVER", default="localhost", help="defines the server to use (default: localhost)")
	
	
	#-y / --generic-statistics
	stat_opts.add_option("-y", "--generic-statistics", dest="gen_stats", default=False, action="store_true", help="checks for inactive and outdated system statistic metrics (default :no)")
	
	#-u / --outdated-warning
	stat_opts.add_option("-u", "--outdated-warning", dest="outdated_warn", default=50, metavar="NUMBER", type=int, help="defines outdated systems warning percentage threshold (default: 50)")
	
	#-U / --outdated-critical
	stat_opts.add_option("-U", "--outdated-critical", dest="outdated_crit", default=80, metavar="NUMBER", type=int, help="defines outdated systems critical percentage threshold (default: 80)")
	
	#-n / --inactive-warning
	stat_opts.add_option("-n", "--inactive-warning", dest="inactive_warn", default=10, metavar="NUMBER", type=int, help="defines inactive systems warning percentage threshold (default: 10)")
	
	#-N / --inactive-critical
	stat_opts.add_option("-N", "--inactive-critical", dest="inactive_crit", default=50, metavar="NUMBER", type=int, help="defines inactive systems critical percentage threshold (default: 50)")
	
	
	#-S / --system
	system_opts.add_option("-S", "--system", dest="system", default=[], metavar="SYSTEM", action="append", help="defines one or multiple system(s) to check")
	
	#-A / --all-systems
	system_opts.add_option("-A", "--all-systems", dest="all_systems", default=False, action="store_true", help="checks all registered systems - USE WITH CAUTION (default: no)")
	
	#-t / --total-warning
	system_opts.add_option("-t", "--total-warning", dest="total_warn", metavar="NUMBER", type=int, help="defines total package update warning threshold (default: empty)")
	
	#-T / --total-critical
	system_opts.add_option("-T", "--total-critical", dest="total_crit", metavar="NUMBER", type=int, help="defines total package update critical threshold (default: empty)")
	
	#-i / --important-warning
	system_opts.add_option("-i", "--security-warning", "--important-warning", dest="security_warn", metavar="NUMBER", type=int, default=10, help="defines security package (critical, important and moderate security fixes) update warning threshold (default: 10)")
	
	#-I / --important-critical
	system_opts.add_option("-I", "--security-critical", "--important-critical", dest="security_crit", metavar="NUMBER", type=int, default=20, help="defines security package (critical, important and moderate security fixes) update critical threshold (default: 20)")
	
	#-b / --bugs-warning
	system_opts.add_option("-b", "--bugs-warning", dest="bugs_warn", type=int, metavar="NUMBER", default=25, help="defines bug package update warning threshold (default: 25)")
	
	#-B / --bugs-critical
	system_opts.add_option("-B", "--bugs-critical", dest="bugs_crit", type=int, metavar="NUMBER", default=50, help="defines bug package update critical threshold (default: 50)")
	
	#parse arguments
	(options, args) = parser.parse_args()
	
	#set logging
	if options.debug:
		logging.basicConfig(level=logging.DEBUG)
		LOGGER.setLevel(logging.DEBUG)
	else:
		logging.basicConfig()
		LOGGER.setLevel(logging.INFO)
	
	#check system specification
	if options.all_systems == False and options.gen_stats == False and not options.system:
		LOGGER.error("You need to either specify (a) particular system(s) or all check all systems!")
		exit(1)
	
	#debug outputs
	LOGGER.debug("OPTIONS: {0}".format(options))
	
	#check statistics or systems
	get_currency_data(options.gen_stats)
	if options.gen_stats: check_stats()
	else: check_systems()
