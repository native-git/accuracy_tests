#! /usr/bin/env python

import rospy
import tf
import math
import time

from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist


rospy.init_node("motion_testing")
rate = rospy.Rate(10.0)

listener = tf.TransformListener()
t = tf.Transformer(True, rospy.Duration(20.0))

def get_transform(from_a,to_b):

	(trans,rot) = t.lookupTransform(from_a,to_b,rospy.Time(0))
	return (trans,rot)

def set_transform(from_a,to_b,(trans,rot)):

	m = geometry_msgs.msg.TransformStamped()
	m.header.frame_id = from_a
	m.child_frame_id = to_b
	m.transform.translation.x = trans[0]
	m.transform.translation.y = trans[1]
	m.transform.rotation.x = 0.0
	m.transform.rotation.y = 0.0
	m.transform.rotation.z = rot[2]
	m.transform.rotation.w = rot[3]
	t.setTransform(m)

def lookup_odom():

	got_one = False

	while not got_one:
		
		try:
			(trans,rot) = listener.lookupTransform("/odom", "/base_link", rospy.Time(0))
			got_one = True
		except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
			continue
		return (trans, rot)

def check_camera():

	i = 0
	x_old = 0
	y_old = 0
	yaw_old = 0

	while i <= 21:

		try:
			(trans,rot) = listener.lookupTransform('/map', '/pioneer', rospy.Time(0))
			rate.sleep()
			i += 1
		except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
			continue

		euler = tf.transformations.euler_from_quaternion(rot)
		x = trans[0]
		y = trans[1]
		yaw = euler[2]
		x_avg = (x + ((i-1)*x_old))/i
		y_avg = (y + ((i-1)*y_old))/i
		yaw_avg = (yaw + ((i-1)*yaw_old))/i
		x_old = x_avg
		y_old = y_avg
		yaw_old = yaw_avg

	quaternion = tf.transformations.quaternion_from_euler(0.0,0.0,yaw_avg)
	trans = (x_avg,y_avg,0.0)
	set_transform("map","pioneer",(trans,quaternion))

def odometryCb(msg):
    print msg.pose.pose
    x = msg.pose.pose.position.x
    vel = abs(target_x-x)/2
    print vel
    if vel <= 0.0001 or vel >= 1.5:
    	v_x = 0
    else:
    	v_x = min(vel,0.5)
    print v_x
    cmd_msg = Twist()
    cmd_msg.linear.x = v_x
    pub.publish(cmd_msg)
    sub_once.unregister()

def pub_cmd_vel(v_x,v_theta):

	msg = Twist()
	msg.linear.x = v_x
	msg.angular.z = v_theta
	pub.publish(msg)

def move_x(x):
	# This function should move some relative distance x, accelerating for 1/4t, traveling at constant v for 1/2t, and decelerating for 1/4t
	# [a] -> acceleration, is assumed to be pioneer's default setting of 0.3 m/s^2
	# [d_t] -> delta t, refresh rate to send commands (warning, must be > 0.6, or pioneer will stop due to command timeout)
	# [v_max] -> maximum velocity, assumed to be pioneers default value of 0.75 m/s
	a = 0.3
	d_t = 0.25
	v_max = 0.75

	print "Moving a distance of " + str(x) + " meters..."

	x_vel = math.sqrt((x*a)/3)

	if x_vel >= v_max:
		t_extra = (x/v_max) - ((3*v_max)/a)
		x_vel = v_max

	else:
		t_extra = 0

	t = 4*x_vel/a
	stop_t = 0.75*t
	stop_t += t_extra
	remainder = stop_t%d_t
	n = int(stop_t/d_t)

	for i in range(0,n+1):
		pub_cmd_vel(x_vel,0)
		time.sleep(d_t)
	time.sleep(remainder)
	pub_cmd_vel(0,0)

	print "Stop command sent..."


pub = rospy.Publisher('cmd_vel', Twist, queue_size = 1)
target_x = 1.5

move_x(1.0)
"""
time.sleep(1)
for i in range(0,8):
	pub_cmd_vel(0.5,0)
	time.sleep(0.25)
pub_cmd_vel(0,0)
"""


"""
while not rospy.is_shutdown():
	rate = rospy.Rate(10)
	sub_once = rospy.Subscriber('/odom',Odometry,odometryCb)
	#(trans,rot) = lookup_odom()
	#print trans
	rate.sleep()
	#rospy.spin()
"""