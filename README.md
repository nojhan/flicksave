FlickSave -- automatic snapshot each time you hit save
======================================================

FlickSave automagically backup a timestamped snapshot of a file that you edit with any program, without getting in your way.

For example, each time you hit `Ctrl-S` within a drawing software,
FlickSave will make a copy the current version of your file,
along with the precise date of this version.

## Usage

You should start FlickSave with the file you want to save as an argument
and let it run during the time you want to create snapshots.
Once started, it will watch for modifications on the given file
and create the snapshots by himself each time something happens.

### Synopsis

`flicksave.py [-h] [-d DIRECTORY] [-y DELAY] [-s SEPARATOR] [-t TEMPLATE] [-v {DEBUG,INFO,WARNING,ERROR}] target`

### Required positional argument

`target`: The file to save each time it's modified.

### Optional arguments

* `-h`, `--help`: show this help message and exit.
* `-d DIRECTORY`, `--directory DIRECTORY`: The directory in which to copy the saved versions.  (default: .)
* `-y DELAY`, `--delay DELAY`: The minimum time (in seconds) between the creation of different saved files. (default: 10)
* `-s SEPARATOR`, `--separator SEPARATOR`: Separator character between the file name and the date stamp. (default: _)
* `-t TEMPLATE`, `--template TEMPLATE`: Template of the date stamp. (default: %Y-%m-%dT%H:%M:%S)
* `-v {DEBUG,INFO,WARNING,ERROR}`, `--verbose {DEBUG,INFO,WARNING,ERROR}`: Verbosity level. (default: WARNING) 
## Examples

### Command line

Just start FlickSave with your target file as an argument:

    $ ./flicksave.py my_file.svg

Then edit your file and save it.
As usual, hit `Ctrl-C` (or close the terminal) to stop FlickSave.

If you want to specify a directory in which to put your snapshots,  with no more than one separate file every minute:

    $ ./flicksave.py -d flicksave -y 60 my_file.xcf

If you want to see what's going on and when the snapshots are created, ask it to be more verbose:

    $ touch test.txt
    $ ./flicksave.py -v INFO test.txt &
    [1] 4303
    echo "." >> test.txt
    2017-11-29T21:15:51 -- ./test.txt -> ./test_2017-11-29T21:15:51.txt
    $ kill 4303
    [1]+  Complété              ./flicksave.py -v INFO test.txt

## Authors

Original Author: [![endorse](https://api.coderwall.com/nojhan/endorsecount.png)](https://coderwall.com/nojhan)

