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

- `--save`: save a timestamped  snapshot of the watched file(s),
- `--inkscape`: export a timestamped PNG(s) of a watched SVG(s),
- `--git`: commit the modifications of the watched file(s),
- `--log`: print a message stating that the watched file(s) were touched.
- `--dbus`: send a notification to the system's D-Bus.

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

* `-h`, `--help`: show this help message and exit.
* `--save`: Save a snapshot of the watched file.
* `--inkscape`: Save a PNG snpashot of the watched SVG file.
* `--git`: Commit the watched file if it has been modified.
* `--log`: Print a message when the watched file is touched.
* `--dbus`: Send a notification to the system's D-Bus.
* `-d DIRECTORY`, `--directory DIRECTORY`: The directory in which to copy the saved versions.  (default: .)
* `-y DELAY`, `--delay DELAY`: The minimum time (in seconds) between the creation of different saved files. (default: 10)
* `-s SEPARATOR`, `--separator SEPARATOR`: Separator character between the file name and the date stamp. (default: _)
* `-t TEMPLATE`, `--template TEMPLATE`: Template of the date stamp. (default: %Y-%m-%dT%H:%M:%S)
* `-e {opened,moved,deleted,created,modified,closed}...`, `--events`: The events touching the watched file for which you want your action perfomed. You can pass multiple (space-separated) events, then the action will be performed for each of them. (default: modified)
* `-w`, `--no-overwrite`: Do not overwrite snapshots created at the same time, but append a number to their name (especially useful if you watch several events).
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


## Authors

Original Author: nojhan ([![endorse](https://api.coderwall.com/nojhan/endorsecount.png)](https://coderwall.com/nojhan))
