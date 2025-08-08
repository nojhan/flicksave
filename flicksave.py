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
    def __init__(self, target, date, ext = None):
        self.target = target
        self.date = date
        self.ext = ext

    def __repr__(self):
        return f"Flick({self.date},{self.target},{self.ext})"

    def as_file(self):
        # Assemble the flick properties as if it was a file.
        # Current date with second precision (i.e. without micro-seconds).
        tag = self.date.isoformat().split(".")[0]
        name,ext = os.path.splitext(self.target)
        if self.ext:
            ext = self.ext
        flickname = name + self.date_sep + tag + ext
        return os.path.join(save_dir, flickname)


class Flicker:
    """Build a new timestamped file name."""
    def __init__(self, target, delay=10):
        self.target = target
        self.delay = delay
        self.last_date = None

    def __iter__(self):
        return self

    def next(self):
        name,ext = os.path.splitext(self.target)
        date_now = datetime.datetime.now()

        if self.last_date:
            logging.debug("Current date: %s", date_now.isoformat())
            assert(self.last_date <= date_now)

            if date_now - self.last_date < datetime.timedelta(seconds=self.delay):
                logging.debug("Current delta: %s < %s", date_now - self.last_date,datetime.timedelta(seconds=self.delay))
                return Flick(self.target, self.last_date, ext)

        return Flick(self.target, date_now, ext)


class Operator:
    """Interface example for an Operator (but can actually be any callable with the same signature)."""
    def __call__(self, target, flick, alt_ext = None):
        raise NotImplemented


class Save(Operator):
    """Make a copy of the target file.
    Takes care to create a missing directory if necessary."""
    def __repr__(self):
        return f"Save({self.last_date})"

    def __init__(self, save_dir, date_sep, date_template):
        self.date_template = date_template
        self.date_sep = date_sep
        self.save_dir = save_dir
        # Make a glob search expression with the date template.
        self.fields = {'Y':4,'m':2,'d':2,'H':2,'M':2,'S':2}
        self.glob_template = self.date_template
        for k in self.fields:
            self.glob_template = self.glob_template.replace("%"+k,'?'*self.fields[k])

    def find_last_save(self, target):
        full = os.path.expanduser(target)
        head = os.path.basename(full)
        name,ext = os.path.splitext(head)

        pattern = name+self.date_sep+self.glob_template+ext
        logging.debug("Search pattern: %s", pattern)

        existing = glob.glob(os.path.join(self.save_dir,pattern))
        logging.debug("Matching files: %s", existing)

        if existing:
            last = last_of(sorted(existing))
            root,ext = os.path.splitext(last)
            last_name = os.path.basename(root)
            # As we globbed the pattern, no need for complex regexp.
            last_tag = last_of(last_name.split(self.date_sep))
            last_date = datetime.datetime.strptime(last_tag, self.date_template)
            logging.debug("Last flick at: %s", last_date.isoformat())
            return last_date

        logging.debug("No previous save found.")
        return None

    def save(self, flick):
        flickfile = flick.as_file()
        logging.info("Copy %s as %s", target, flickfile)
        try:
            shutil.copy(target, flickfile)
        except FileNotFoundError:
            logging.warning('WARNING create missing directory: %s',os.path.dirname(flickfile))
            os.mkdir(os.path.dirname(flickfile))
            shutil.copy(target, flickfile)
            #FIXME more error handling?
        except:
            logging.error("ERROR while copying file: %s", sys.exc_info()[0])

        self.last_date = self.find_last_save(self.flick.target)

    def __call__(self, target, flick, alt_ext = None):
        self.last_date = self.find_last_save(self.flick.target)
        if self.last_date:
            logging.debug("Current date: %s", date_now.isoformat())
            assert(self.last_date <= date_now)

            if date_now - self.last_date < datetime.timedelta(seconds=self.delay):
                logging.debug("Current delta: %s < %s", date_now - self.last_date,datetime.timedelta(seconds=self.delay))
                save(flick)
            else:
                logging.info("Delay not reached, I will not save.")
        else:
            save(flick)


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
            flick.ext = self.alt_ext

        cmd = self.cmd.format(target=target,flick=flick)
        logging.info("Run command: %s", cmd )
        try:
            # We want the shell because we may call shell command or need environment variables.
            proc = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            logging.error("ERROR while calling command")
            logging.error("\tReturn code: %s",proc.returncode)
            logging.error("\tOut: %s",proc.stdout)
            logging.error("\tErr: %s",proc.stderr)
        except:
            logging.error("ERROR while calling subprocess: %s", sys.exc_info()[0])

        logging.debug("Command ended.")


class Log(Operator):
    def __repr__(self):
        return "Log()"

    def __call__(self, target, flick, alt_ext = None):
        logging.info("Event(s) seen for {}: {}".format(target,flick))


class Handler(FileSystemEventHandler):
    """Event handler, will call a sequence of operators at each event matching the target."""
    def __init__(self, operators, flicker, watched_types = ["modified"] ):
        self.flicker = flicker
        self.ops = operators
        self.watched_types = watched_types

    def on_any_event(self, event):
        logging.debug("Received event %s",event)
        super(Handler,self).on_any_event(event)
        # Watchdog cannot watch single files (FIXME bugreport?),
        # so we filter it in this event handler.
        if (not event.is_directory) and os.path.abspath(event.src_path) == os.path.abspath(self.flicker.target) and event.event_type in self.watched_types:
            logging.debug("Handle event")
            flick = self.flicker.next()
            logging.debug("New flicker for %s: %s", event.src_path, flick)

            for op in self.ops:
                logging.debug("Calling %s", op)
                op(os.path.abspath(event.src_path), flick)
        else:
            logging.debug("Not handling event: file={}, is_directory={}, watched_types={}".format(os.path.abspath(event.src_path),event.is_directory, self.watched_types))


def flicksave(target, operators=None, delay=10, watched=["modified"]):
    """Start the watch thread."""
    # Handle files specified without a directory.
    root = os.path.dirname(target)
    if not root:
        root = '.'
    target = os.path.join(root,target)

    flicker = Flicker(target, delay)

    handler = Handler(operators, flicker, watched)

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

    class SaneHelpFormatter(
        argparse.RawTextHelpFormatter, argparse.ArgumentDefaultsHelpFormatter
    ):
        pass

    # With default values in help message.
    parser = argparse.ArgumentParser(formatter_class=SaneHelpFormatter,
        description="Perofm an action each time a file is touched. For example: make a copy of a file each time it is modified.",
        epilog="""Examples:
    Copy the file each time it is modified:
        flicksave --save my_file
    Copy the file in a subdirectory each time it is modified:
        flicksave --directory snapshots --save my_file
    Export a PNG from a watched SVG, each time you hit 'save' in inkscape:
        flicksave --inkscape my_file
    Git commit the file if it has been modified, but not before 30 seconds after the previous commit:
        flicksave --git --delay 30 my_file
    Copy the file each time is is opened or closed:
        flicksave --events opened closed --save my_file
    """)

    # Required argument.
    parser.add_argument("target",
        help="The file to save each time it's modified.")

    # Optional arguments.
    parser.add_argument("-d","--directory", default='.',
        help="The directory in which to copy the saved versions.")

    parser.add_argument("-y","--delay",     default=10, type=int,
        help="The minimum time (in seconds) between the creation of different saved files.")

    parser.add_argument("-e","--events", default="modified", nargs="*",
        choices = ["opened", "moved", "deleted", "created", "modified", "closed"],
        help="The event(s) on which you want to perform the action.")

    parser.add_argument("-s","--separator", default='_',
        help="Separator character between the file name and the date stamp.")

    parser.add_argument("-t","--template",  default='%Y-%m-%dT%H:%M:%S',
        help="Template of the date stamp.")

    parser.add_argument("-v","--verbose", choices=['DEBUG','INFO','WARNING','ERROR'], default='INFO',
        help="Verbosity level.")
    log_as = { 'DEBUG'  :logging.DEBUG,
               'INFO'   :logging.INFO,
               'WARNING':logging.WARNING,
               'ERROR'  :logging.ERROR }


    # TODO HERE: keep help in existing, put instance in available
    existing = {
        "save":
            ["Save a snapshot of the target file.",
            None],
        "inkscape":
            ["Save a PNG snapshot of the file, using inkscape.",
            None],
        "git":
            ["Commit the target file if it has been modified [the repository should be set-up].",
             None],
         "log":
             ["Log when the target file is modified.",
             None],
    }

    def help(name):
        return existing[name][0]
    def instance(name):
        return existing[name][1]

    for name in existing:
        parser.add_argument("--"+name, help=help(name), action="store_true")

    asked = parser.parse_args()

    logging.basicConfig(level=log_as[asked.verbose], format='%(asctime)s -- %(message)s', datefmt=asked.template)

    available = existing;

    available["save"][1] = Save(asked.directory, asked.separator, asked.template)
    available["inkscape"][1] = Command("inkscape {target} --without-gui --export-png={flick} --export-area-page", "png")
    available["git"][1] = Command("git add {target} ; git commit -m 'Automatic flicksave commit: {flick}'")
    available["log"][1] = Log()

    if __debug__:
        for op in existing:
            assert op in available
        for op in available:
            assert op in existing

    logging.debug("Available operators:")
    for name in available:
        logging.debug("\t%s",name)

    operators = []
    requested = vars(asked)
    for it in [iz for iz in requested if iz in available and requested[iz]==True]:
        operators.append(instance(it))

    if len(operators) == 0:
        logging.warning(
            "WARNING: you did not asked for any snapshot command, "
             "I will only log when you save the file, but not perform any action. "
             "Use one of the following option if you want me to do something: "
             +", ".join(["--"+str(k) for k in available.keys()])
         )
        operators.append(Log())

    logging.debug("Used operators:")
    for op in operators:
        logging.debug("\t%s", op)

    # Start it.
    flicksave(asked.target, operators, asked.delay, asked.events)

