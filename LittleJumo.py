# coding:utf-8
'''
<跳一跳小游戏的外挂>
- Windows与Android的互动
	- 使用Adb shell作为桥梁连接Android和Windows
	- 使用'adb shell screencap -p /sdcard/jump.png' 截屏并存储
	- 使用'adb pull /sdcard/jump.png' 将存储的截屏拉取到Windows
	- 使用'abd shell input swipe x1 y1 x2 y2 ms' 按压屏幕,按压时间由ms决定
- 图像处理
	- 找到人物的位置
		- 使用hsv空间来确定人物
	- 找到新生成的图块
		- 使用bitxor来取反获得新图块
- 按压处理
	- 按压的时间决定了人物跳的远近
	- 目标点和人物点的距离乘上某个系数
'''
import numpy as np
import cv2
import os,math,time

# 图像处理
class ImgHandle:
	def __init__(self,img):
		self.breakFlag = 250
		self.newImg = None
		self.hsvL = np.array((116,107,86))
		self.hsvH = np.array((122,120,102))
		pass

	# 找到棋子的点
	def findSelfPoint(self,img):
		hsvImg = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
		# 棋子底部的hsv
		roiImg = self.getROI(img,hsvImg,self.hsvL,self.hsvH)
		(x,y),r = self.minCircle(img,roiImg)
		return (x,y)

	# 取得感兴趣的区域
	def getROI(self,img,hsv,tmin,tmax): #普通组合滤波,hsv格式
		thresh=cv2.inRange(hsv, tmin,tmax) #过滤
		thresh=cv2.medianBlur(thresh,3) #中值滤波
		thresh=cv2.GaussianBlur(thresh,(3,3),0) #高斯滤波
		return thresh

	# 最小包裹圆
	def minCircle(self,sImg,img):
		img = cv2.GaussianBlur(img, (3, 3), 1)  #
		t, img = cv2.threshold(img,0,255,cv2.THRESH_OTSU)
		(cnts, _) = cv2.findContours(img, cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
		c = sorted(cnts, key = cv2.contourArea, reverse = True)[0]  #最大圆
		(x,y),r=cv2.minEnclosingCircle(c)
		(x,y),r=(int(x),int(y)),int(r)
		return (x,y),r

	# 创建异或模版
	def creatMask(self,img):
		lastList = []
		lastLayer = 0
		for color in img:
			lastList.append(color[-1])
			lastLayer += 1
			if lastLayer > self.breakFlag:
				break
		self.newImg = np.zeros((480,270,3),np.uint8)
		tempColor = None
		for color in lastList[::-1]:
			cv2.line(self.newImg,(0,lastLayer),(270,lastLayer),
					(int(color[0]),int(color[1]),int(color[2])),1)
			lastLayer -= 1

	# 找到跳跃的点
	def findNextPoint(self,img,px):
		bitImg = cv2.bitwise_xor(img,self.newImg)
		gray = cv2.cvtColor(bitImg, cv2.COLOR_BGR2GRAY)
		(_,gray) = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY)
		kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(13, 13))  
		gray = cv2.erode(gray,kernel)

		cv2.line(gray,(0,self.breakFlag),(270,self.breakFlag),(0,0,0),5)
		contours, hierarchy = cv2.findContours(gray,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
		cnts = sorted(contours, key = cv2.contourArea, reverse = True)
		(x,y) = (0,0)
		r = 0
		for cnt in cnts[::-1]:
			 (x,y),r=cv2.minEnclosingCircle(cnt)
			 if y > 50 and abs(x-px) > 15:
			 	break
		(x,y),r=(int(x),int(y)),int(r)
		return (x,y)


# 命令处理
class CmdHandle:
	# 获取截图指令
	def getOrder(self):
		os.system('adb shell screencap -p /sdcard/ajump.png')
		os.system('adb pull /sdcard/ajump.png')

	# 发送跳跃指令
	def jumpOrder(self,dis):
		pressTime = max(6*dis,180)
		os.system('adb shell input swipe 1 1 1 1 %s'%pressTime)

# 应用开始
class App:
	def __init__(self):
		self.img = None
		self.imgHandle = None
		self.cmdHandle = CmdHandle()
		self.imgHandle = ImgHandle()
		pass

	def main(self):
		imgName = 0
		while (1):
			self.cmdHandle.getOrder()
			self.img = cv2.imread('ajump.png')
			self.img = cv2.resize(self.img,(270,480))

			self.imgHandle.creatMask(self.img)
			(x1,y1) = self.imgHandle.findSelfPoint(self.img)
			(x2,y2) = self.imgHandle.findNextPoint(self.img,x1)

			y2-=2
			if x2 < x1:
				x2+=6
			else:
				x2+=2
			dis = math.sqrt((y2-y1)**2+(x2-x1)**2)
			self.cmdHandle.jumpOrder(int(dis))#abs(x2-x1))
			time.sleep(1)
		pass
	

if __name__ == '__main__':
	print 'hello'
	app = App()
	app.main()
	pass




