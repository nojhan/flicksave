import os
import glob
import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from watchdog.events import LoggingEventHandler

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
        # Current date with second precision (without micro-seconds).
        tag = date.isoformat().split(".")[0]
        flick = name + self.date_sep + tag + ext
        return os.path.join(save_dir, flick)

    def next(self):
        full = os.path.expanduser(self.base)
        head = os.path.basename(full)
        name,ext = os.path.splitext(head)

        pattern = name+self.date_sep+self.glob_template+ext
        existing = glob.glob(os.path.join(self.save_dir,pattern))

        date_now = datetime.datetime.now()
        #print(date_now)

        if existing:
            last = last_of(sorted(existing))
            root,ext = os.path.splitext(last)
            last_name = os.path.basename(root)
            # As we globbed the pattern, no need for complex regexp.
            last_tag = last_of(last_name.split(self.date_sep))
            last_date = datetime.datetime.strptime(last_tag, self.date_template)

            #print("Last flick on:",last_date.isoformat())
            logging.info("Last flick on %s", last_date.isoformat())

            assert(last_date <= date_now)
            if date_now - last_date < datetime.timedelta(seconds=self.delay):
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
        # Watchdog cannot watch singl files,
        # so we filter it in this event handler.
        if (not event.is_directory) and event.src_path == self.base:
            logging.info("Touched %s -> %s", event.src_path, self.flick.next())


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
    import time
    import logging

    target = sys.argv[1]

    #flick = Flick(target)
    #print(flick.next())

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    flicksave(target)
