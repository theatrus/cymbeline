import sys
import os
import optparse
import signal

from xml.dom import minidom


def createDaemon():
   """Detach a process from the controlling terminal and run it in the
   background as a daemon.
   """

   try:
      # Fork a child process so the parent can exit.  This will return control
      # to the command line or shell.  This is required so that the new process
      # is guaranteed not to be a process group leader.  We have this guarantee
      # because the process GID of the parent is inherited by the child, but
      # the child gets a new PID, making it impossible for its PID to equal its
      # PGID.
      pid = os.fork()
   except OSError, e:
      return((e.errno, e.strerror))     # ERROR (return a tuple)

   if (pid == 0):       # The first child.

      # Next we call os.setsid() to become the session leader of this new
      # session.  The process also becomes the process group leader of the
      # new process group.  Since a controlling terminal is associated with a
      # session, and this new session has not yet acquired a controlling
      # terminal our process now has no controlling terminal.  This shouldn't
      # fail, since we're guaranteed that the child is not a process group
      # leader.
      os.setsid()

      # When the first child terminates, all processes in the second child
      # are sent a SIGHUP, so it's ignored.
      signal.signal(signal.SIGHUP, signal.SIG_IGN)

      try:
         # Fork a second child to prevent zombies.  Since the first child is
         # a session leader without a controlling terminal, it's possible for
         # it to acquire one by opening a terminal in the future.  This second
         # fork guarantees that the child is no longer a session leader, thus
         # preventing the daemon from ever acquiring a controlling terminal.
         pid = os.fork()        # Fork a second child.
      except OSError, e:
         return((e.errno, e.strerror))  # ERROR (return a tuple)

      if (pid == 0):      # The second child.
         # Ensure that the daemon doesn't keep any directory in use.  Failure
         # to do this could make a filesystem unmountable.
         #os.chdir("/")
         # Give the child complete control over permissions.
         os.umask(0)
      else:
         os._exit(0)      # Exit parent (the first child) of the second child.
   else:
      os._exit(0)         # Exit parent of the first child.

   # Close all open files.  Try the system configuration variable, SC_OPEN_MAX,
   # for the maximum number of open files to close.  If it doesn't exist, use
   # the default value (configurable).
   #try:
   #   maxfd = os.sysconf("SC_OPEN_MAX")
   #except (AttributeError, ValueError):
   #   maxfd = 256       # default maximum

   for fd in range(0, 2):
      try:
         os.close(fd)
      except OSError:   # ERROR (ignore)
         pass

   # Redirect the standard file descriptors to /dev/null.
   os.open("/dev/null", os.O_RDONLY)    # standard input (0)
   os.open("/dev/null", os.O_RDWR)       # standard output (1)
   os.open("/dev/null", os.O_RDWR)       # standard error (2)

   return (0,pid)


def launch():
    # Setup path to include the local directory
    cwd = os.getcwd()
    sys.path.append(cwd)
    
    # New fangled cymbelined launcher - no more ugly cymbeline.py hacks.
    
    parser = optparse.OptionParser()
    parser.add_option("-n", "--no-daemon", dest="console",
                      action="store_true",  default=False,
                      help="Enable the interactive console (no daemon)")
    parser.add_option("-s", '--settings', dest='settings',
                      help = 'The Settings database for cymbeline')
    parser.add_option("-l", '--log', dest='dolog', help='Enable logging')
    
    (options,args) = parser.parse_args()
    
    app = args[0]
    # pretend to parse app here
    
    # Parse .cymapp for file
    xmldoc = minidom.parse(app + ".cymapp")
    cymapp = xmldoc.getElementsByTagName('cymapp')[0]
    xmodule = cymapp.getElementsByTagName('module')[0]
    try:
        xsettings = cymapp.getElementsByTagName('settings')[0]
    except:
        xsettings = None

    # Try to read settings
    settings=""
    if options.settings:
        settings = options.settings
    elif xsettings:
        settings = xsettings.childNodes[0].data
    else:
        settings = 'db_settings'

    app = xmodule.childNodes[0].data
    print "Trying to launch '"+app+"'",
    
    if options.console:
        print " on the console."
    else:
        print " as a daemon."



    exec("import " + app + ".Boot")
    mod = sys.modules[app+".Boot"]
    fun = getattr(mod, 'boot')
    
    from cymbeline.Bootstrap import bootstrap
    
    try:
        if not options.console:
            createDaemon()
    except:
        print "Can't fork on this platform"
   
   

    bootstrap(fun, settings_db = settings, ic_console = options.console)
