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
$ HISTFILE="" SATELLITE_LOGIN=mylogin SATELLITE_PASSWORD=mypass ./check_repodata.py -S giertz.stankowic.lo c
```

## Using an authfile
A better possibility is to create a authfile with permisions **0600**. Just enter the username in the first line and the password in the second line and hand the path to the script:
```
$ ./check_repodata.py -a myauthfile -l centos6-x86_64
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
