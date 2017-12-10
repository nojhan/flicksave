#!/usr/bin/env python3
#encoding: utf-8

import os
import time
import glob
import shutil
import logging
import datetime
import subprocess

from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEventHandler


def last_of(us):
    return us[-1]


class Flick:
    """Build a new timestamped file name."""
    def __init__(self, target, save_dir=".", delay=10, stamp_sep='_', date_template="%Y-%m-%dT%H:%M:%S"):
        self.target = target
        self.date_template = date_template
        self.date_sep = stamp_sep
        self.save_dir = save_dir
        self.delay = delay

        # Make a glob search expression with the date template.
        self.fields = {'Y':4,'m':2,'d':2,'H':2,'M':2,'S':2}
        self.glob_template = self.date_template
        for k in self.fields:
            self.glob_template = self.glob_template.replace("%"+k,'?'*self.fields[k])

    def __iter__(self):
        return self

    def make(self, save_dir, name, date, ext):
        # Current date with second precision (i.e. without micro-seconds).
        tag = date.isoformat().split(".")[0]
        flick = name + self.date_sep + tag + ext
        return os.path.join(save_dir, flick)

    def next(self):
        full = os.path.expanduser(self.target)
        head = os.path.basename(full)
        name,ext = os.path.splitext(head)

        pattern = name+self.date_sep+self.glob_template+ext
        logging.debug("Search pattern: %s", pattern)

        existing = glob.glob(os.path.join(self.save_dir,pattern))
        logging.debug("Matching files: %s", existing)

        date_now = datetime.datetime.now()
        logging.debug("Current date: %s", date_now.isoformat())

        if existing:
            last = last_of(sorted(existing))
            root,ext = os.path.splitext(last)
            last_name = os.path.basename(root)
            # As we globbed the pattern, no need for complex regexp.
            last_tag = last_of(last_name.split(self.date_sep))
            last_date = datetime.datetime.strptime(last_tag, self.date_template)

            logging.debug("Last flick at: %s", last_date.isoformat())

            assert(last_date <= date_now)
            if date_now - last_date < datetime.timedelta(seconds=self.delay):
                logging.debug("Current delta: %s < %s", date_now - last_date,datetime.timedelta(seconds=self.delay))
                return self.make(self.save_dir,name,last_date,ext)

        return self.make(self.save_dir,name,date_now,ext)


class Operator:
    """Interface example for an Operator (but can actually be any callable with the same signature)."""
    def __call__(self, target, flick, alt_ext = None):
        raise NotImplemented


class Command(Operator):
    """Run a user-defined command.
    Takes the target and the flick as argument.
    The command should be a python 3 format string.
    For example: 'cp {target} {flick}'
    You can omit one of the named arguments.
    For example: 'touch {flick}'"""

    def __init__(self, command, alt_ext = None):
        self.cmd = command
        self.alt_ext = alt_ext

    def __repr__(self):
        return "Command(\"{}\",\"{}\")".format(self.cmd,self.alt_ext)

    def __call__(self, target, flick):

        # Change the extension, if asked.
        flickname,flickext = os.path.splitext(flick)
        if self.alt_ext:
            flick = "{}.{}".format(flickname,self.alt_ext)

        cmd = self.cmd.format(target=target,flick=flick)
        logging.info("Run command: %s", cmd )
        try:
            # We want the shell because we may call shell command or need environment variables.
            proc = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            logging.error("ERROR while calling command")
            logging.debug("\tReturn code: %s",proc.returncode)
            logging.info("\tOut: %s",proc.stdout)
            logging.info("\tErr: %s",proc.stderr)
        except:
            logging.error("ERROR while calling subprocess: %s", sys.exc_info()[0])

        logging.debug("Command ended.")


class Save(Operator):
   """Make a copy of the target file.
   Takes care to create a missing directory if necessary."""
   def __repr__(self):
       return "Save()"

   def __call__(self, target, flickname):
       logging.info("Copy %s as %s", target, flickname)
       try:
           shutil.copy(target, flickname)
       except FileNotFoundError:
           logging.warning('WARNING create missing directory: %s',os.path.dirname(flickname))
           os.mkdir(os.path.dirname(flickname))
           shutil.copy(target, flickname)
           #FIXME more error handling?
       except:
           logging.error("ERROR while copying file: %s", sys.exc_info()[0])


class Handler(FileSystemEventHandler):
    """Event handler, will call a sequence of operators at each event matching the target."""
    def __init__(self, target, operators, flick = None):
        self.target = target

        if not flick:
            self.flick = Flick(target)
        else:
            self.flick = flick

        self.ops = operators

    def on_any_event(self, event):
        logging.debug("Received event %s",event)
        super(Handler,self).on_any_event(event)
        # Watchdog cannot watch single files (FIXME bugreport),
        # so we filter it in this event handler.
        if (not event.is_directory) and os.path.abspath(event.src_path) == os.path.abspath(self.target):
            logging.debug("Handle event")
            flickname = self.flick.next()
            logging.debug("New flick for %s: %s", event.src_path, flickname)

            for op in self.ops:
                logging.debug("Calling %s", op)
                op(os.path.abspath(event.src_path), os.path.abspath(flickname))


def flicksave(target, operators=None, save_dir=".", delay=10, stamp_sep='_', date_template="%Y-%m-%dT%H:%M:%S"):
    """Start the watch thread."""
    # Handle files specified without a directory.
    root = os.path.dirname(target)
    if not root:
        root = '.'
    target = os.path.join(root,target)

    flick = Flick(target, save_dir, delay, stamp_sep, date_template)

    # At least, save a copy of the file.
    if not operators:
        operators = [Save()]

    handler = Handler(target, operators, flick)

    # Start the watch thread.
    observer = Observer()
    observer.schedule(handler, root)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__=="__main__":
    import sys
    import argparse

    # With default values in help message.
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Required argument.
    parser.add_argument("target",
        help="The file to save each time it's modified.")

    # Optional arguments.
    parser.add_argument("-d","--directory", default='.',
        help="The directory in which to copy the saved versions.")
    parser.add_argument("-y","--delay",     default=10,
        help="The minimum time (in seconds) between the creation of different saved files.")
    parser.add_argument("-s","--separator", default='_',
        help="Separator character between the file name and the date stamp.")
    parser.add_argument("-t","--template",  default='%Y-%m-%dT%H:%M:%S',
        help="Template of the date stamp.")
    parser.add_argument("-v","--verbose", choices=['DEBUG','INFO','WARNING','ERROR'], default='WARNING',
        help="Verbosity level.")
    log_as = { 'DEBUG'  :logging.DEBUG,
               'INFO'   :logging.INFO,
               'WARNING':logging.WARNING,
               'ERROR'  :logging.ERROR }
    parser.add_argument("-n","--no-save", action="store_true",
        help="Do not copy the file (useful if you only want to run another command).")

    available = {
        "inkscape":
            ("Save a PNG snapshot of the file, using inkscape.",
             Command("inkscape {target} --without-gui --export-png={flick} --export-area-page", "png"))
    }

    def help(name):
        return available[name][0]
    def instance(name):
        return available[name][1]

    for name in available:
        parser.add_argument("--"+name, help=help(name), action="store_true")

    asked = parser.parse_args()

    logging.basicConfig(level=log_as[asked.verbose], format='%(asctime)s -- %(message)s', datefmt=asked.template)

    logging.debug("Available operators:")
    for name in available:
        logging.debug("\t%s",name)

    if asked.no_save:
        operators = []
    else:
        operators = [Save()]

    requested = vars(asked)
    for it in [iz for iz in requested if iz in available and requested[iz]==True]:
        operators.append(instance(it))

    logging.debug("Used operators:")
    for op in operators:
        logging.debug("\t%s", op)

    # Start it.
    flicksave(asked.target, operators, asked.directory, asked.delay, asked.separator, asked.template)

