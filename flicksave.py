import os
import glob
import datetime

def make_flick(save_dir, name, date, ext):
    # Current date with second precision (without micro-seconds).
    tag = date.isoformat().split(".")[0]
    flick = name + "_" + tag + ext
    return os.path.join(save_dir, flick)


def last_of(us):
    return us[-1]


def next_name(base, save_dir=".", delay=10):
    full = os.path.expanduser(base)
    head = os.path.basename(full)
    name,ext = os.path.splitext(head)

    pattern = name+"_????-??-??T??:??:??"+ext
    existing = glob.glob(os.path.join(save_dir,pattern))

    date_now = datetime.datetime.now()
    #print(date_now)

    if existing:
        last = last_of(sorted(existing))
        root,ext = os.path.splitext(last)
        last_name = os.path.basename(root)
        # As we globbed the pattern, no need for complex regexp.
        last_tag = last_of(last_name.split("_"))
        last_date = datetime.datetime.strptime(last_tag, "%Y-%m-%dT%H:%M:%S")

        print("Last save:",last_date.isoformat())

        assert(last_date <= date_now)
        if date_now - last_date < datetime.timedelta(seconds=delay):
            return make_flick(save_dir,name,last_date,ext)

    return make_flick(save_dir,name,date_now,ext)


if __name__=="__main__":

    import sys

    print(next_name(sys.argv[1]))
