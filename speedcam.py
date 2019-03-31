#!/usr/bin/python
import time
import math
import datetime
import cv2
import os.path
import argparse
import csv
import pickle

WINDOW_NAME = 'SPEED CAMERA'

class BoundingBoxHelper:

	def __init__(self):
		self.prompt = "set bounding box"
		self.drawing = False
		self.ix,self.iy = -1,-1
		self.fx,self.fy = -1,-1
		self.image = None

	def prompt_on_image(self,image,txt):
		cv2.putText(image,txt, (10,30),
		cv2.FONT_HERSHEY_SIMPLEX, .75, (0,255,0), 1)

	def draw_rectangle(self,e,x,y,flags,param):
		if e == cv2.EVENT_LBUTTONDOWN:
			self.drawing = True
			self.ix, self.iy = x, y
		elif e == cv2.EVENT_MOUSEMOVE:
			if self.drawing == True:
				image = self.org_image.copy()
				self.prompt_on_image(image,self.prompt)
				cv2.rectangle(image,(self.ix,self.iy),(x,y),(0,255,0),2)
				self.image = image
		elif e == cv2.EVENT_LBUTTONUP:
			self.drawing = False
			self.fx, self.fy = x, y
			image = self.org_image.copy()
			self.prompt_on_image(image,'any key to continue')
			cv2.rectangle(image,(self.ix,self.iy),(self.fx,self.fy),(0,255,0),2)
			self.image = image

	def get_normalized_coordinates(self):
		upper_left_x,upper_left_y = -1,-1
		lower_right_x, lower_right_y = -1,-1
		if self.fx > self.ix:
			upper_left_x = self.ix
			lower_right_x = self.fx
		else:
			upper_left_x = self.fx
			lower_right_x = self.ix

		if self.fy > self.iy:
			upper_left_y = self.iy
			lower_right_y = self.fy
		else:
			upper_left_y = self.fy
			lower_right_y = self.iy

		return (upper_left_x,upper_left_y,lower_right_x,lower_right_y)

	def do_setup(self,camera):
		_, self.image = camera.read()
		self.org_image = self.image.copy()
		self.prompt_on_image(self.image, self.prompt)
		cv2.setMouseCallback(WINDOW_NAME,self.draw_rectangle)
		while 1:
			cv2.imshow(WINDOW_NAME, self.image)
			key = cv2.waitKey(1) & 0xFF
			if key != 255:
				break

#------------------------------------------------------------------------------

CSV_FILE = 'carspeed.csv'
CSV_FIELD_NAMES = ['Date','Day','Time','Direction','Speed','Image']

THRESHOLD = 15
MIN_AREA = 175
BLURSIZE = (15,15)
IMAGEWIDTH = 1024
IMAGEHEIGHT = 576
RESOLUTION = [IMAGEWIDTH,IMAGEHEIGHT]
FOV = 59.1
FPS = 30

DISTANCE = 58
LANE_WIDTH = 8
MIN_SPEED = 10

def get_camera(file=0):
	camera = cv2.VideoCapture(file)
	if file == 0:
		camera.set(cv2.CAP_PROP_FRAME_WIDTH,IMAGEWIDTH)
		camera.set(cv2.CAP_PROP_FRAME_HEIGHT,IMAGEHEIGHT)
		camera.set(cv2.CAP_PROP_FPS,FPS)
		#let camera warm up
		time.sleep(0.9)
	return camera


def calc_speed(pixels, ftperpixel, secs):
	if secs > 0.0:
		return ((pixels * ftperpixel) / secs ) * 0.681818
	else: return 0.0

def elapsed_seconds(endtime, begintime):
	return (endtime - begintime).total_seconds()

def calc_frame_width(fov,distance):
	return 2*(math.tan(math.radians(fov*0.5))*distance)

def calc_ft_per_pixel(frame_width,img_width):
	return frame_width / float(img_width)

def annotate_image(image,now,last_mph):
	cv2.putText(image,now.strftime("%A %d %B %Y %I:%M:%S%p"),
		(10, image.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0,255,0),1)
	size, base = cv2.getTextSize("%.0f mph" % last_mph, cv2.FONT_HERSHEY_SIMPLEX, 2, 3)
	cntr = int((IMAGEWIDTH - size[0]) / 2)
	cv2.putText(image,"%.0f mph" % last_mph, (cntr, int(IMAGEHEIGHT * 0.2)), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,255,0),3)

def save_image(image,now):
	filename = 'imgs/car_at_{0}.jpg'.format(now.strftime('%Y%m%d_%H%M%S'))
	cv2.imwrite(filename,image)
	return filename

def save_data(curtime,direction,speed,filename):
	with open(CSV_FILE,'a') as file:
		writer = csv.DictWriter(file,fieldnames=CSV_FIELD_NAMES)
		writer.writerow({\
					'Date':curtime.strftime('%Y.%m.%d'),\
					'Day':curtime.strftime('%A'),\
					'Time':curtime.strftime('%H:%M:%S'),\
					'Direction':direction,\
					'Speed':'{0:.0f}'.format(speed),\
					'Image':filename})

def init_csv():
	if (not os.path.isfile(CSV_FILE)):
		with open(CSV_FILE, 'a') as file:
			writer = csv.DictWriter(file,fieldnames=CSV_FIELD_NAMES)
			writer.writeheader()

def load_box_settings(settings_file='speedcam_settings.p'):
	try:
		return pickle.load(open(settings_file,'rb'))
	except:
		return None

def write_box_settings(bound_box,settings_file='speedcam_settings.p'):
	pickle.dump(bound_box,open(settings_file,'wb'))

def run(camera,uly,lry,ulx,lrx,incl_contour=False):
	IDLE,TRACK,SAVE = 0,1,2 #processing states
	L2R, R2L = 1,2 #direction of travel
	state = IDLE
	direction = 0
	base_image = None
	init_csv()

	while 1:
		ret, image = camera.read()
		timestamp = datetime.datetime.now()
		#crop to defined area
		crop = image[uly:lry,ulx:lrx]
		#convert to grey scale, and blur
		grey = cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY)
		grey = cv2.GaussianBlur(grey, BLURSIZE, 0)

		if base_image is None:
			base_image = grey.copy().astype('float')
			last_time = timestamp
			cv2.imshow(WINDOW_NAME,image)

		# compute absolute difference between the current image and
		# base image and the turn everything lighter gray than THRESHOLD into white
		frame_delta = cv2.absdiff(grey, cv2.convertScaleAbs(base_image))
		thresh = cv2.threshold(frame_delta, THRESHOLD, 255, cv2.THRESH_BINARY)[1]

		#dilate threshold image, then find contours
		thresh = cv2.dilate(thresh, None, iterations=2)
		(cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

		motion_found = False
		biggest_area = 0
		#find largest bounding rectangle
		for c in cnts:
			(cx,cy,cw,ch) = cv2.boundingRect(c)
			found_area = cw*ch
			if (found_area < MIN_AREA):
				continue
			elif (found_area > biggest_area):
				biggest_area = found_area
				motion_found = True
				# bounding rectangle location and dimensions
				x,y,w,h = cx,cy,cw,ch

		if motion_found:
			if state == IDLE:
				state = TRACK
				initial_x = x
				last_x = x
				initial_time = timestamp
				last_mph = 0
				print('time	x	width x-delta	MPH')
			else:
				dur = elapsed_seconds(timestamp,initial_time)
				#too long tracking object, so reset
				if dur >= 3:
					state = IDLE
					direction = 0
					base_image = None
					print('reset')
					continue

				ft_p_px = 0
				if state == TRACK:
					if x >= last_x:
						direction = L2R
						abs_chg = x+w-initial_x
						frame_width = calc_frame_width(FOV,DISTANCE-LANE_WIDTH)
						ft_p_px = calc_ft_per_pixel(frame_width,IMAGEWIDTH)
					else:
						direction = R2L
						abs_chg = initial_x - x
						frame_width = calc_frame_width(FOV,DISTANCE)
						ft_p_px = calc_ft_per_pixel(frame_width,IMAGEWIDTH)

					mph = calc_speed(abs_chg,ft_p_px,dur)
					print('{0:7.3f}	{1:4d}	{2:4d}	{3:4d}	{4:7.0f} '.format(dur,x,w,abs_chg,mph))
					# object crossed left edge or object crossed right edge
					if ((direction == R2L) and (x <= 2)) \
						or ((direction == L2R) and (x+w >= (lrx-ulx-2))): 
						state = SAVE
						if(last_mph > MIN_SPEED):
							curtime = datetime.datetime.now()
							annotate_image(image,curtime,mph)
							if incl_contour:
								#contour coordinates are relative to bounding box
								cv2.rectangle(image,(x+ulx,y+uly),(x+w+ulx,y+h+uly),(0,255,0),2)
							file_name = save_image(image,curtime)
							direction = "N" if direction == R2L else "S"
							save_data(curtime,direction,last_mph,file_name)
					#not at a boundary, so save current speed and position
					last_mph = mph
					last_x = x


		else: #no motion found
			if state != IDLE:
				state = IDLE
				direction = 0

		if state == IDLE:
			cv2.putText(image,datetime.datetime.now().strftime('%A %d %B %Y %I:%M:%S%p'),
				(10,image.shape[0]-10),cv2.FONT_HERSHEY_SIMPLEX,0.75,(0,255,0),1)

			cv2.line(image,(ulx,uly),(ulx,lry),(0,255,0))
			cv2.line(image,(lrx,uly),(lrx,lry),(0,255,0))

			cv2.putText(image,"'q' to quit", (10,35),
				cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0,255,0), 1)
			cv2.imshow(WINDOW_NAME,image)

			last_x = 0
			cv2.accumulateWeighted(grey, base_image, 0.25)

			key = cv2.waitKey(1) & 0xFF

			if key == ord("q"):
				break
	#free cv2 windwow(s)
	cv2.destroyAllWindows()

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-s','--setup',help='run bounding box setup',action='store_true')
	parser.add_argument('-c','--contourbox',help='include contour box in capture',action='store_true')
	args = parser.parse_args()

	# initialize the camera
	camera = get_camera()
	cv2.namedWindow(WINDOW_NAME)
	cv2.moveWindow(WINDOW_NAME,10,40)

	# create imgs folder if it doesn't exist
	if not os.path.isdir(os.path.join(os.getcwd(),'imgs')):
		os.mkdir(os.path.join(os.getcwd(),'imgs'))

	box_settings = load_box_settings()
	#uly,lry,ulx,lrx=350,500,130,740

	if args.setup or (box_settings is None):
		setup = BoundingBoxHelper()
		setup.do_setup(camera)
		(ulx,uly,lrx,lry) = setup.get_normalized_coordinates()
		box_settings = {'ulx':ulx,'uly':uly,'lrx':lrx,'lry':lry}
		write_box_settings(box_settings)
		print('uly: {0}, lry: {1}, ulx: {2}, lrx: {3}'.format(uly,lry,ulx,lrx))

	uly = box_settings['uly']
	lry = box_settings['lry']
	ulx = box_settings['ulx']
	lrx = box_settings['lrx']
	run(camera,uly,lry,ulx,lrx,args.contourbox)

