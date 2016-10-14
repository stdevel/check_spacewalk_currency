# check_spacewalk_currency
`check_spacewalk_currency` is a Nagios/Icinga plugin for checking patch currency of hosts managed by Spacewalk, Red Hat Satellite 5.x or SUSE Manager.

The script checks the patch currency of one or multiple systems. The following information are gathered by accesing Spacewalk, Red Hat Satellite 5.x or SUSE Manager:
- Outstanding package update counter per category:
  - critical
  - important
  - moderate
  - low
  - enhancement
  - bug fix
- system currency score

To gather these information a valid username / password combination to your management system is required. The login credentials **are prompted** when running the script. To automate this you have two options:

## Setting shell variables
The following shell variables are used:
* **SATELLITE_LOGIN** - a username
* **SATELLITE_PASSWORD** - the appropriate password

You might also want to set the HISTFILE variable (*depending on your shell*) to hide the command including the password in the history:
```
$ HISTFILE="" SATELLITE_LOGIN=mylogin SATELLITE_PASSWORD=mypass ./check_spacewalk_currency.py -S giertz.stankowic.loc
```

## Using an authfile
A better possibility is to create a authfile with permisions **0600**. Just enter the username in the first line and the password in the second line and hand the path to the script:
```
$ ./check_spacewalk_currency.py -a myauthfile -S giertz.stankowic.loc
```

# Requirements
The plugin requires Python 2.6 or newer - it also requires the `xmlrpclic` module which is shipped with `rhnlib`.
A minimum Spacewalk API version of 11.1 (**TODO: RELEASE?**) is required. The script checks the API version and aborts if you are using an historic version of Spacewalk.

# Usage
By default, the script checks a particular system or multiple systems for outstanding bug fixes and critical updates (*combining critical, important and also moderate patch metrics*). It is possible to control this behaviour by specifying additional parameters (*see below*).
The script also support performance data for data visualization.

The following parameters can be specified:

| Parameter | Description |
|:----------|:------------|
| `-d` / `--debug` | enable debugging outputs (*default: no*) |
| `-h` / `--help` | shows help and quits |
| `-P` / `--show-perfdata` | enables performance data (*default: no*) |
| `-a` / `--authfile` | defines an auth file to use instead of shell variables |
| `-s` / `--server` | defines the server to use (*default: localhost*) |
| `-S` / `--system` | defines one or multiple system(s) to check |
| `-A` / `--all-systems` | checks all registered systems - USE WITH CAUTION (*default: no*) |
| `-t` / `--total-warning` | defines total package update warning threshold (*default: empty*) |
| `-T` / `--total-critical` | defines total package update critical threshold (*default: empty*) |
| `-i` / `--important-warning` | defines security package (*critical, important and moderate security fixes*) update warning threshold (*default: 10*) |
| `-I` / `--important-critical` | defines security package (*critical, important and moderate security fixes*) update warning threshold (*default: 20*) |
| `-b` / `--bugs-warning` | defines bug package update warning threshold (*default: 25*) |
| `-B` / `--bugs-critical` | defines bug package update warning threshold (*default: 50*) |
| `--version` | prints programm version and quits |

## Examples
The following example checks a single system on the local Spacewalk server:
```
$ ./check_spacewalk_currency.py -S giertz.stankowic.loc
Username: admin
Password:
OK: critical updates okay (0), bug fixes okay (0) for giertz.stankowic.loc
```

Checking multiple systems on a remote Spacewalk server, authentication using authfile:
```
$ ./check_spacewalk_currency.py -s st-spacewalk02.stankowic.loc -a spacewalk.auth -S giertz.stankowic.loc -S shittyrobots.test.loc
OK: giertz.stankowic.loc critical updates okay (0)critical updates okay (0), shittyrobots.test.loc bug fixes okay (0)shittyrobots.test.loc bug fixes okay (0)
```

Checking a single host on a local Spacewalk installation, also checking total updates, enabling performance data:
```
$ ./check_spacewalk_currency.py -S giertz.stankowic.loc -t 20 -T 40 -P
Username: admin
Password:
OK: total updates okay (0), critical updates okay (0), bug fixes okay (0) for giertz.stankowic.loc | 'crit_pkgs'=0;10;20;; 'imp_pkgs'=0;10;20;; 'mod_pkgs'=0;10;20;; 'low_pkgs'=0;;;; 'enh_pkgs'=0;;;; 'bug_pkgs'=0;25;50;; 'score'=0;;;;
```

When specifying multiple systems along with performance data, the metric names will get prefix according to the particular host:
```
$ ./check_spacewalk_currency.py -S giertz.stankowic.loc -S shittyrobots.test.loc -a spacewalk.auth -P
OK: shittyrobots.test.loc critical updates okay (0)giertz.stankowic.loc critical updates okay (0), shittyrobots.test.loc bug fixes okay (0)giertz.stankowic.loc bug fixes okay (0) | 'shittyrobots.test.loc_crit_pkgs'=0;10;20;; 'shittyrobots.test.loc_imp_pkgs'=0;10;20;; 'shittyrobots.test.loc_mod_pkgs'=0;10;20;; 'shittyrobots.test.loc_low_pkgs'=0;;;; 'shittyrobots.test.loc_enh_pkgs'=0;;;; 'shittyrobots.test.loc_bug_pkgs'=0;25;50;; 'shittyrobots.test.loc_score'=0;;;;'giertz.stankowic.loc_crit_pkgs'=0;10;20;; 'giertz.stankowic.loc_imp_pkgs'=0;10;20;; 'giertz.stankowic.loc_mod_pkgs'=0;10;20;; 'giertz.stankowic.loc_low_pkgs'=0;;;; 'giertz.stankowic.loc_enh_pkgs'=0;;;; 'giertz.stankowic.loc_bug_pkgs'=0;25;50;; 'giertz.stankowic.loc_score'=0;;;;
```
