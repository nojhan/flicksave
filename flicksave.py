#!/usr/bin/env python3
#encoding: utf-8

import os
import time
import glob
import shutil
import logging
import datetime

from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEventHandler


def last_of(us):
    return us[-1]


class Flick:
    def __init__(self, target, save_dir=".", delay=10, stamp_sep='_', date_template="%Y-%m-%dT%H:%M:%S"):
        self.base = target
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
        full = os.path.expanduser(self.base)
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


class Save(FileSystemEventHandler):
    def __init__(self, target, flick = None):
        self.base = target

        if not flick:
            self.flick = Flick(target)
        else:
            self.flick = flick

        super(Save,self).__init__()


    def on_any_event(self, event):
        super(Save,self).on_any_event(event)
        # Watchdog cannot watch single files (FIXME bugreport),
        # so we filter it in this event handler.
        if (not event.is_directory) and event.src_path == self.base:
            f = self.flick.next()
            logging.info("%s -> %s", event.src_path, f)
            try:
                shutil.copy(event.src_path, f)
            except FileNotFoundError:
                logging.warning('WARNING create missing directory: %s',os.path.dirname(f))
                os.mkdir(os.path.dirname(f))
                shutil.copy(event.src_path, f)
            #FIXME more error handling?
            except:
                logging.error("ERROR while copying file: %s", sys.exc_info()[0])


def flicksave(target, save_dir=".", delay=10, stamp_sep='_', date_template="%Y-%m-%dT%H:%M:%S"):
    flick = Flick(target, save_dir, delay, stamp_sep, date_template)
    save = Save(target, flick)

    observer = Observer()

    path = os.path.dirname(target)
    observer.schedule(save, path)

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

    asked = parser.parse_args()

    logging.basicConfig(level=log_as[asked.verbose], format='%(asctime)s -- %(message)s', datefmt=asked.template)

    # Start it.
    flicksave(asked.target, asked.directory, asked.delay, asked.separator, asked.template)

