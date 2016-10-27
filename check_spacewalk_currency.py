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

#list of supported API levels
supportedAPI = ["11.1","12","13","13.0","14","14.0","15","15.0","16","16.0","17","17.0"]
state=0
system_currency = {}



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
	if options.debug: print  "Comparing '{0}' ({1}) to warning/critical thresholds {2}/{3})".format(val, desc, warn, crit)
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
		
				#int(entry['enh'] + entry['imp'] + entry['low'] + entry['crit'] + entry['bug'] + entry['mod']),
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
		if options.debug: print "DEBUG: perfdata is:\n{0}".format(str(perfdata))
	else: perfdata=""
	
	#return result
	snips = [x for x in [snip_total, snip_crit, snip_bugs] if x != ""]
	if len(options.system) > 1: hostname=''
	else: hostname="{0}{1}".format(" for ", hostname)
	print "{0}: {1}{2}{3}".format(get_return_str(), str(", ".join(snips)), hostname, perfdata)
	exit(state)



def get_currency_data():
	#get _all_ the currency data
	global system_currency
	
	#define URL and login information
	SATELLITE_URL = "http://{0}/rpc/api".format(options.server)
	
	#setup client and key depending on mode if needed
	client = xmlrpclib.Server(SATELLITE_URL, verbose=options.debug)
	if options.authfile:
		#use authfile
		if options.debug: print "DEBUG: using authfile"
		try:
			#check filemode and read file
			filemode = oct(stat.S_IMODE(os.lstat(options.authfile).st_mode))
			if filemode == "0600":
				if options.debug: print "DEBUG: file permission ({0}) matches 0600".format(filemode)
				fo = open(options.authfile, "r")
				s_username=fo.readline().replace("\n", "")
				s_password=fo.readline().replace("\n", "")
				key = client.auth.login(s_username, s_password)
			else:
				print "ERROR: file permission ({0}) not matching 0600!".format(filemode)
				exit(1)
		except OSError:
			print "ERROR: file non-existent or permissions not 0600!"
			exit(1)
	elif "SATELLITE_LOGIN" in os.environ and "SATELLITE_PASSWORD" in os.environ:
		#shell variables
		if options.debug: print "DEBUG: checking shell variables"
		key = client.auth.login(os.environ["SATELLITE_LOGIN"], os.environ["SATELLITE_PASSWORD"])
	else:
		#prompt user
		if options.debug: print "DEBUG: prompting for login credentials"
		s_username = raw_input("Username: ")
		s_password = getpass.getpass("Password: ")
		key = client.auth.login(s_username, s_password)
	
	#check whether the API version matches the minimum required
	api_level = client.api.getVersion()
	if not api_level in supportedAPI:
		print "ERROR: your API version ("+api_level+") does not support the required calls. You'll need API version 1.8 (11.1) or higher!"
		exit(1)
	else:
		if options.debug: print "INFO: supported API version ("+api_level+") found."
	
	#get currency data
	system_currency = client.system.getSystemCurrencyScores(key)
	
	#append hostname
	counter=0
	for system in system_currency:
		system_sid = client.system.getName(key, system['sid'])
		if options.debug: print "DEBUG: Hostname for SID '{0}' seems to be '{1}'".format(system['sid'], system_sid['name'])
		system['hostname']=system_sid['name']
		#get total package counter
		upgradable_pkgs = client.system.listLatestUpgradablePackages(key, system['sid'])
		system['all']=len(upgradable_pkgs)-1
		#drop host if not requested
		if options.all_systems == False:
			if system['hostname'] not in options.system: system_currency[counter]=None
		counter=counter+1
	#clean removed hosts
	system_currency = [system for system in system_currency if system != None]



if __name__ == "__main__":
	#define description, version and load parser
	desc='''%prog is used to check systems managed by Spacewalk, Red Hat Satellite 5.x or SUSE Manager for outstanding patches. Login credentials are assigned using the following shell variables:
	SATELLITE_LOGIN  username
	SATELLITE_PASSWORD  password
	
	It is also possible to create an authfile (permissions 0600) for usage with this script. The first line needs to contain the username, the second line should consist of the appropriate password. If you're not defining variables or an authfile you will be prompted to enter your login information.
	
	Checkout the GitHub page for updates: https://github.com/stdevel/check_spacewalk_currency'''
	parser = OptionParser(description=desc,version="%prog version 0.5.1")
	
	gen_opts = OptionGroup(parser, "Generic options")
	space_opts = OptionGroup(parser, "Spacewalk options")
	system_opts = OptionGroup(parser, "System options")
	parser.add_option_group(gen_opts)
	parser.add_option_group(space_opts)
	parser.add_option_group(system_opts)
	
	#-d / --debug
	gen_opts.add_option("-d", "--debug", dest="debug", default=False, action="store_true", help="enable debugging outputs")
	
	#-P / --show-perfdata
	gen_opts.add_option("-P", "--show-perfdata", dest="show_perfdata", default=False, action="store_true", help="enables performance data (default: no)")
	
	#-a / --authfile
	space_opts.add_option("-a", "--authfile", dest="authfile", metavar="FILE", default="", help="defines an auth file to use instead of shell variables")
	
	#-s / --server
	space_opts.add_option("-s", "--server", dest="server", metavar="SERVER", default="localhost", help="defines the server to use (default: localhost)")
	
	#-S / --system
	system_opts.add_option("-S", "--system", dest="system", default=[], metavar="SYSTEM", action="append", help="defines one or multiple system(s) to check")
	
	#-A / --all-systems
	system_opts.add_option("-A", "--all-systems", dest="all_systems", default=False, action="store_true", help="checks all registered systems - USE WITH CAUTION (default: no)")
	
	#-t / --total-warning
	system_opts.add_option("-t", "--total-warning", dest="total_warn", metavar="NUMBER", type=int, help="defines total package update warning threshold (default: empty)")
	
	#-T / --total-critical
	system_opts.add_option("-T", "--total-critical", dest="total_crit", metavar="NUMBER", type=int, help="defines total package update critical threshold (default: empty)")
	
	#-i / --important-warning
	system_opts.add_option("-i", "--security-warning", dest="security_warn", metavar="NUMBER", type=int, default=10, help="defines security package (critical, important and moderate security fixes) update warning threshold (default: 10)")
	
	#-i / --important-critical
	system_opts.add_option("-I", "--security-critical", dest="security_crit", metavar="NUMBER", type=int, default=20, help="defines security package (critical, important and moderate security fixes) update critical threshold (default: 20)")
	
	#-b / --bugs-warning
	system_opts.add_option("-b", "--bugs-warning", dest="bugs_warn", type=int, metavar="NUMBER", default=25, help="defines bug package update warning threshold (default: 25)")
	
	#-B / --bugs-critical
	system_opts.add_option("-B", "--bugs-critical", dest="bugs_crit", type=int, metavar="NUMBER", default=50, help="defines bug package update critical threshold (default: 50)")
	
	#parse arguments
	(options, args) = parser.parse_args()
	
	#check system specification
	if options.all_systems == False and len(options.system) == 0:
		print "ERROR: You need to either specify (a) particular system(s) or all check all systems!"
	
	#debug outputs
	if options.debug: print "OPTIONS: {0}".format(options)
	
	#get currency information
	get_currency_data()
	
	#check systems
	check_systems()
