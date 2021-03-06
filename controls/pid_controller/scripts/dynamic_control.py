#!/usr/bin/python
import numpy as np
import rospy

from std_msgs.msg import Float64MultiArray
from geometry_msgs.msg import Pose
from underwater_sensor_msgs.msg import DVL  
from visualization_msgs.msg import Marker
from underwater_sensor_msgs.srv import SpawnMarker, SpawnMarkerRequest
from PID import PIDRegulator

## \class controlPID
#  \brief This is a class for PID controller
#
#  Takes x,y,z co-ordinates as arguments.
#  Invoke update() function for thruster control
# 	
class controlPID:	
	def __init__(self,x,y,z):
		self.cur_pos=np.array([0,0,0])
		self.cur_vel=np.array([0,0,0])
		self.ref=np.array([x,y,z])
		self.pidp=PIDRegulator(0.75,0,0)
		self.pidv=PIDRegulator(1,0,0)
		self.u=np.zeros(5)
		
		
	## This function publish acceleration for each thruster on /g500/thrusters_input.
	#  It subscribes from /g500/dvl to get velocity and /g500/pose to get veloctiy
	#  and use cascaded PID controller to move the bot to desired co-ordinates
	# 
	def update(self):

		sub_pose=rospy.Subscriber('g500/pose',Pose,self.pose_callback,queue_size=1)
		sub_vel=rospy.Subscriber('g500/dvl',DVL,self.vel_callback)
		pub_acc=rospy.Publisher('g500/thrusters_input', Float64MultiArray, queue_size=1000)
		
		e_pos=np.zeros(3)
		e_vel=np.zeros(3)
		cmd_vel=np.zeros(3)
		cmd_acc=np.zeros(3)
		dt=0.01
		#cascaded PID-controller
		for i in range(3):
			e_pos[i]=self.ref[i]-self.cur_pos[i]
			cmd_vel[i]=self.pidp.regulate(e_pos[i],dt)
			e_vel[i]=cmd_vel[i]-self.cur_vel[i]
			cmd_acc[i]=self.pidv.regulate(e_vel[i],dt)
			
		self.u[0]=-cmd_acc[1]
		self.u[1]=-cmd_acc[1]
		self.u[2]=-cmd_acc[2]
		self.u[3]=-cmd_acc[2]
		self.u[4]=-cmd_acc[0]
		
		msg=Float64MultiArray()
		msg.data=self.u
		pub_acc.publish(msg)
		print cmd_acc
		
		
	#velocity subscriber callback
	def vel_callback(self, msg):
		self.cur_vel =np.array([msg.bi_x_axis, msg.bi_y_axis, msg.bi_z_axis])
		#rounding of velocity to one decimal place to neglect disturbances
		for i in range(3):
			self.cur_vel[i]=round(self.cur_vel[i],1)
			
			
	#postion subscriber callback	
	def pose_callback(self,msg):
		self.cur_pos=np.array([msg.position.x, msg.position.y, msg.position.z])
		#rounding of velocity to one decimal place to neglect disturbances
		for i in range(3):
			self.cur_pos[i]=round(self.cur_pos[i],1)
		
	
print "Controller Node:"
rospy.init_node('Controller', anonymous=True)

x=int(input("Enter x co-ordinate"))
y=int(input("Enter y co-ordinate"))
z=int(input("Enter z co-ordinate"))

cnt=controlPID(x,y,z)

while not rospy.is_shutdown():
	cnt.update()
	rospy.Rate(100).sleep()

