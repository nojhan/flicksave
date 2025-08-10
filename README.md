FlickSave -- automatic snapshot each time you hit save
======================================================

FlickSave automagically perform an action each time you touch watched files.

For instance, FlickSave can backup a timestamped snapshot of a file that you edit with any program, without getting in your way.

For example, each time you hit `Ctrl-S` within a drawing software,
FlickSave will make a copy the current version of your file,
along with the precise date of this version.

This may be useful for digital artists that want to prepare a time-lapse of their on-going work without having to think about it.
You can even do an automatic Git commit the same way.


## Usage

You should start FlickSave with the files you want to save as argument(s)
and let it run during the time you want to perform your action(s).
Once started, it will watch for modifications on the given file(s)
and, for instance, create the snapshots by himself each time something happens.

Currently, FlickSave can perform the following actions:

- `--save`,
- `--inkscape`,
- `--git`,
- `--log`,
- `--dbus`,
- `--cmd [COMMAND]`.

You can pass multiple actions.
For instance, you can both export a PNG and do a Git commit.

By default, timestamped snapshots have the same name than the targeted files,
with the addition of the timestamp.
For instance, with a target file named `test.svg`, a snapshot will look like `test_2017-11-28T21:02:59.svg`.


### Synopsis

`flicksave.py [-h] [--save] [--inkscape] [--git] [--log] [--dbus] [-d DIRECTORY] [-y DELAY] [-s SEPARATOR] [-t TEMPLATE] [-w] [-v {DEBUG,INFO,WARNING,ERROR}] [-e {opened,moved,deleted,created,modified,closed}...] target [target ...]`

### Required positional argument

`target`: The file to watch.

### Optional arguments

Actions:

* `--save`: Save a snapshot of the watched file.
* `--inkscape`: Save a PNG snpashot of the watched SVG file.
* `--git`: Commit the watched file if it has been modified.
* `--log`: Print a message when the watched file is touched.
* `--dbus`: Send a notification to the system's D-Bus.
* `--cmd [COMMAND]: Run the passed command for each watched file.
    You can use tags, which will be replaced by actual data:
        - {target} (the current watched file),
        - {flick} (the timestamped absolute filename, containing the --directory),
        - {directory} (cf. --directory, where to put timestamped files),
        - {separator} (cf. --separator),
        - {timestamp} (the timestamp formatted by --template),
        - {alt_ext} (cf. --alt-ext alternate extension),
        - {no_overwrite} (cf. --no-overwrite boolean, 1 if True, 0 if False),
        - {event} (the event type, cf. --events).

Common actions parameters:

* `-y DELAY`, `--delay DELAY`: The minimum time (in seconds) between running actions. (default: 10)
* `-e {opened,moved,deleted,created,modified,closed}...`, `--events`: The events touching the watched file for which you want your action perfomed. You can pass multiple (space-separated) events, then the action will be performed for each of them. (default: modified)

Actions parameters affecting only certain actions:

* `-d DIRECTORY`, `--directory DIRECTORY`: The directory in which to copy the saved versions.  (default: .)
* `-s SEPARATOR`, `--separator SEPARATOR`: Separator character between the file name and the date stamp. (default: _)
* `-t TEMPLATE`, `--template TEMPLATE`: Template of the date stamp. (default: %Y-%m-%dT%H:%M:%S)
* `-w`, `--no-overwrite`: Do not overwrite snapshots created at the same time, but append a number to their name (especially useful if you watch several events).
* `-x EXTENSION`, `--alt-ext EXTENSION`: Alternate extension for the timestamped snapshot (do not forget the dot). (default: )

Other:

* `-h`, `--help`: show this help message and exit.
* `-v {DEBUG,INFO,WARNING,ERROR}`, `--verbose {DEBUG,INFO,WARNING,ERROR}`: Verbosity level. (default: WARNING)

## Examples

### Command line

Just start FlickSave with your target file as an argument:

    $ flicksave --save my_file.svg

Then edit your file and save it.
As usual, hit `Ctrl-C` (or close the terminal) to stop FlickSave.

If you want to specify a directory in which to put your snapshots,  with no more than one separate file every minute:

    $ flicksave --inkscape --directory flicksave --delay 60 my_file.svg

You can call sevral actions, for instance export a PNG and commit the source SVG:

    $ flicksave --inkscape --git my_file.svg

You can use your shell to create the file list:

    $ flicksave --git *.py

And even handle files in subdirectories:

    $ flicksave --log */*.log

You may want to save both the file before and after it was modified by any
program:

    $ flicksave --save --events opened closed --no-overwrite my_file

You can export PNGs and commit their source across sub-directories,
and be notified when it's done:

    $ flicksave --inkscape --git --dbus --events closed */*.svg

You can also prepare the list of files to watch by using a subcommand:

    $ flicksave --log $(find . -type f -name *.png | grep -v test)

If you want to pass your own command:

    $ flicksave --cmd "git commit -a -m 'whatever'" my_file
    $ flicksave --cmd "git add {target} ; git commit -m 'Automated commit' ; git tag '{timestamp}'"
    $ flicksave --cmd "echo '{flick}' > watching_pipe" *.log


## Authors

Original Author: nojhan ([![endorse](https://api.coderwall.com/nojhan/endorsecount.png)](https://coderwall.com/nojhan))
