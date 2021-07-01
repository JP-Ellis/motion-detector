# Motion Detector

A small library to extract segments of CCTV footage with motion.

## Usage

After downloading the code, you can install and run the package with:

```shell
$ pipenv install
$ pipenv shell
$ extract-motion ...
```

Note that by default, this will re-encode the parts with motion with HEVC (using
GPU acceleration) though the default arguments are for FFMPEG running on Linux.
These will need to be adjusted.

## Documentation

```text
usage: extract-motion [-h] [-b BACKGROUND] [-m MASK] [--history HISTORY] [-s] [-v] video

positional arguments:
  video                 Path to the video file

optional arguments:
  -h, --help            show this help message and exit
  -b BACKGROUND, --background BACKGROUND
                        reference background image
  -m MASK, --mask MASK  Bounds of rectangle to ignore, specified as 'x1,x2,y1,y2'
  --history HISTORY
  -s, --show            Show the stream
  -v, --verbose
```

## Workings

This uses a weighted moving average of the previous images in order to determine
whether there has been any change. When changes are detected, the previous and
next 2 seconds are included and then everything is exported to a new file.
