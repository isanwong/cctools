# -*- coding: utf-8 -*-
# Copyright (C) 2012- The University of Notre Dame
# This software is distributed under the GNU General Public License.
# See the file COPYING for details.
#
# This program provides a simple api to sweep though a range of parameters
# and store the output in progname/param/
#

from work_queue import *
import itertools, sys, os, re, hashlib, mmap
from subprocess import *

class Sweeper:
    """Provides a simple api for a program to sweep through a range of parameters.
        Usage: import sweeper
               x = sweeper.Sweeper()"""
    def __init__(self):
        self.port = WORK_QUEUE_RANDOM_PORT  # random, default is 9123
        self.progname = ""                  # the program to sweep with
        self.envpath = ""                   # path to a environment set up script
        self.paramvalues = []               # list of arguments e.g. -l -o 27
        self.command = []                   # list of the full command to be run
        self.sweeps = []                    # list of variables to sweep over
        self.inputlist = []                 # list of input files
        self.outputlist = []                # list of output files

    def addprog(self, progname):
        """The program (sans parameters) to sweep with.
            Usage: x.addprog("echo")
            @param progname The base program that will be run."""
        self.command.append(progname)
        # remove the file extension so we can create a nice directory
        self.progname, sep, tail = progname.partition('.')

    def setenv(self, pathtoenv):
        """Set the path to a env script to set up an environment for the command to run in.
            Usage: x.setenv("env.sh")
            @param pathtoenv The path to a script to run first."""
        self.envpath = pathtoenv

    def setenvdir(self, pathtoenvdir, caching=2):
        """Specify a directory to be submitted that contains an environment for the worker to run in, a script will still have to set the env up.
            Usage: x.setenvdir('myenvdir')
                   x.setenv('env.sh') # set ups env on worker using myenvdir
            @param pathtoenvdir The path to the directory."""
        # TODO contained in the envdir should be a script that sets up the env, this needs to be added to the env script
        r = []
        r.append(pathtoenvdir)
        r.append(caching)
        self.inputlist.append(r)

    def addtuple(self, flag, iterlist):
        """Add a flag/sweep pair to the command. This has the same functionality as addparameter() and addsweep() used together.
            Usage: x.addtuple("-n", xrange(1,10,2))
            @param flag The flag to be added to the command.
            @param iterlist An interable list object that contains the values to sweep over."""
        self.command.append(str(flag))
        self.command.append('%s')
        self.paramvalues.append('%s')
        r = []
        for i in iterlist:
            r.append(i)
        self.sweeps.append(r)

    def addparameter(self, param):
        """Add a parameter to the list of parameters(arguments).
            Usage: x.addparameter("-n")
                   x.addsweep(xrange(1,10,2))
                   x.addparameter("> out")
            @param param The argument to be added."""
        self.command.append(str(param))

    def addinput(self, input, caching=2):
        """Add a file (or directory) to the input list.
            Usage: x.addinput("infile")
            @param input The file or directory to be included as input."""
        r = []
        r.append(input)
        r.append(caching)
        self.inputlist.append(r)

    def addoutput(self, output, caching=1):
        """Add a file (or directory) to the output list.
            Output will be placed in progname/parameters/
            Usage: a.addoutput("outfile")
            @param output The file to be recieved back from the worker as output."""
        r = []
        r.append(output)
        r.append(caching)
        self.outputlist.append(r)

    def addsweep(self, iterlist):
        """Add a sweep to the command.
            Usage: x.addsweep(xrange(1,10,2))
            @param iterlist An iterable object that contains the values to sweep over."""
        self.command.append("%s")
        self.paramvalues.append("%s")
        r = []
        for i in iterlist:
            r.append(i)
        self.sweeps.append(r)

    def sweep(self, interpreter='bash'):
        """Sweep over the command.
            @param interpreter The interpreter to run the script with."""
        try:
            self.q = WorkQueue(self.port)
        except:
            print "Work Queue init failed!"
            sys.exit(1)

        print "listening on port %d..." % self.q.port

        for item in itertools.product(*self.sweeps):
            # create the commad
            command  = ' '.join(self.command) % (item)
            commdir = '_'.join(self.command) % (item)
            # we want to replace illegal file characters with _
            regex = re.compile('[:/" ()<>|?*]|(\\\)')
            commdir = regex.sub('_', commdir)
            
            # create progname/commdir, this is where the output will go ex. BuildMSM-sweep/command_with_underscores/Data
            os.system("mkdir -p %s-sweep/%s" % (self.progname, commdir))

            if (self.envpath): # if a env script was specified
                env = open(self.envpath).read()
            else:
                env = ""

            # combine an env script and the command into one
            script = """%(env)s%(command)s\n""" % {'env': env, 'command': command}
            fo = open('%s-sweep/%s/%s-script' % (self.progname, commdir, commdir), 'w')
            fo.write(script)
            fo.close
            # TODO add an option to specify the interpreter
            taskcommand = '%s script.sh' % (interpreter) # run with bash

            t = Task(taskcommand)
            t.specify_buffer(script, 'script.sh')

            for input in self.inputlist:
                if input[1] == 2: # 2 means caching should be true
                    # the input is usually the same for all the commands
                    t.specify_file(os.path.abspath(input[0]), input[0], WORK_QUEUE_INPUT, cache=True)
                else:
                    t.specify_file(os.path.abspath(input[0]), input[0], WORK_QUEUE_INPUT, cache=False)
            for output in self.outputlist:
                # we want the output on the remote machine to go to progname-sweep/params/ on the local machine
                if output[1] == 2: # 2 means caching should be true
                    t.specify_file("%s-sweep/%s/%s" % (self.progname, commdir, output[0]), output[0], WORK_QUEUE_OUTPUT, cache=True)
                else:
                    t.specify_file("%s-sweep/%s/%s" % (self.progname, commdir, output[0]), output[0], WORK_QUEUE_OUTPUT, cache=False)

            taskid = self.q.submit(t)
            print "submitted task (id# %d): %s" % (taskid, t.command)

        print "waiting for tasks to complete..."

        while not self.q.empty():
            t = self.q.wait(5)
            if t:
                print "task (id# %d) complete %s (return code %d)" % (t.id, t.command, t.return_status)

        print "all tasks complete!"
        print 'output and a copy of the script run by each worker located in %s-sweep' % (self.progname)

    def sqldbsubmit(self, host, user,  dbname, pwfile, interpreter='bash'):
        """Submit the commands to a MyWorkQueue MySQL database
            Usage: x.sqldbsubmit('cvrl-sql.crc.nd.edu', 'ccl', 'ccltest', 'secret/mysql.pwd')
            @param host The MySQL host.
            @param user The MySQL user.
            @param dbname The name of the db
            @param pwfile A file containing the pw for the mysql server.
            @param interpreter The interpreter to run the script"""
        sqlscript = ""
        for item in itertools.product(*self.sweeps):
            command  = ' '.join(self.command) % (item) # create the command
            commdir = '_'.join(self.command) % (item)
            # we want to replace all illegal file characters with _
            regex = re.compile('[:/" ()<>|?*]|(\\\)')
            commdir = regex.sub('_', commdir)
            # this is the location of the script on the master
            localpath = os.path.abspath('%s-sweep/%s/%s-script' % (self.progname, commdir, commdir))
            # location of the script on the worker
            remotepath = '%s-script' % (commdir)
            dbcommand = '%s ./' % (interpreter)+remotepath
            
            # create progname-sweep/commdir, this is where the output will go ex. BuildMSM-sweep/command_with_underscores/Data
            os.system("mkdir -p %s-sweep/%s" % (self.progname, commdir))

            if (self.envpath): # if a env script was specified
                env = open(self.envpath).read()
            else:
                env = ""

            # combine the env script and the command into one
            script = """%(env)s%(command)s\n""" % {'env': env, 'command': command}
            fo = open(localpath, 'w')
            fo.write(script)
            fo.close()

            #INSERT INTO commands VALUES (command_id, username, personal_id, name, command, status, stdout)
            #INSERT INTO files VALUES (fileid, command_id, local_path, remote_path, type, flags, checksum)
            # add the command to the table
            sqlscript += 'INSERT INTO %s.commands VALUES (command_id, \'%s\', personal_id, name, \'%s\', 2, stdout);\n' % (dbname, user, dbcommand)

            # add script as input so it is sent to the worker - no caching
            # get the checksum of the input script (localpath)
            sqlscript += 'INSERT INTO %s.files VALUES (fileid, command_id, \'%s\', \'%s\', 1, 1, \'%s\');\n' % (dbname, localpath, remotepath, self._checksum(localpath))
            # add the input files to the myworkqueue db
            for input in self.inputlist:
                # TODO get the checksum of input files, check if the input is the same
                sqlscript += 'INSERT INTO %s.files VALUES (fileid, command_id, \'%s\', \'%s\', 1, %s, \'%s\');\n' % (dbname, os.path.abspath(input[0]), input[0], input[1], self.checksum(input))
            # add the output files to the myworkqueue db
            for output in self.outputlist:
                outputdir = '%s-sweep/%s/' % (self.progname, commdir)
                sqlscript += 'INSERT INTO %s.files VALUES (fileid, command_id, \'%s\', \'%s\', 2, %s, checksum);\n' % (dbname, os.path.abspath(outputdir+output[0]), output[0], output[1])
                # each command in the commands table has a unique command_id, this needs to be associated with the correct input/output files
                sqlscript += 'UPDATE %s.files SET files.command_id=(SELECT MAX(command_id) FROM %s.commands WHERE command=\'%s\' LIMIT 1) WHERE files.command_id=0;\n' % (dbname, dbname, dbcommand)
            sqlscript += '\n'

        # create a copy of the sqlscript that was run
        fo = open('%s-sweep/sqlscript' % (self.progname), 'w')
        fo.write(sqlscript)
        fo.close()
        # note that the password comes from a file
        os.system(('mysql --debug-check --show-warnings -h %s -u %s --password=%s < %s-sweep/sqlscript') % (host, user, open(pwfile).read().strip(), self.progname))

    def _checksum(self, filename):
        try:
            f = open(localpath)
            # this is faster but doesn't seem to work in ND afs space
            map = mmap.mmap(f.fileno(), 0, flags=mmap.MAP_PRIVATE, prot=mmap.PROT_READ)
            return hashlib.sha1(map).hexdigest()
        except:
            # slightly slower but always works
            return hashlib.sha1(open(filename, 'rb').read()).hexdigest()