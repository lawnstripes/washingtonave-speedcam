# washingtonave-speedcam
A python script that uses OpenCV to measure the speed of am object (hopefully a car) traveling through a camera's field of view. For each object measured an image is composed containing the car's speed and time of capture. An entry in a CSV file is also added to store the date, time, direction of travel, speed and relative image path. This script currently runs on a Raspberry Pi 3B+ although it should work on most OS with minimal modifications. 

## Installation
1. Install OpenCV 
2. Copy this script to your machine
3. Open the script and modify the ```DISTANCE``` variable to match the distance from your webcam to the road. Modify the ```FOV``` (field of view) variable to match your camera's hardware.
3. ```python3 speedcam.py```

## Usage
The first time the script is run, it will display a static image and prompt the user to draw a rectangle within the image. This rectangle is used to 'focus' the tracking on a specific area of the screen. The rectangle coordinates are saved to the current directory. If these coordinates need to change run the script with the -s argument to re-calibrate: ```python3 speedcam.py -s```

The -c switch will draw a contour box around the car as it exits the capture area: ```python3 speedcam.py -c```

## Resources
Check out Adrian Rosebrock's AWESOME blog [pyimagesearch.com](https://pyimagesearch.com) which has lots and lots of resources and reference material for computer vision via Python. In particular: 

1. [Install OpenCV3 + Python on your Raspberry Pi](https://www.pyimagesearch.com/2017/09/04/raspbian-stretch-install-opencv-3-python-on-your-raspberry-pi/)
2. [Basic motion detection and tracking with Python and OpenCV](https://www.pyimagesearch.com/2015/05/25/basic-motion-detection-and-tracking-with-python-and-opencv/)

[@pageauc](https://github.com/pageauc/) has a much more 'feature rich' speed camera project available here: https://github.com/pageauc/speed-camera. This script borrows several ideas from his project. 

### License
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
