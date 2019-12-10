from .settings import *

import numpy as np
import matplotlib.pyplot as plt
import mpl_toolkits.axes_grid1 as axgr
import cv2
import warnings

class Picture():
    
    def __init__(self,file_pass, flags=1):
        
        warnings.filterwarnings('ignore')
        self.picture = cv2.imread(file_pass, flags=flags)
        self.H = self.picture.shape[0]
        self.W = self.picture.shape[1]
    
    def get(self):
        return self.picture

    #縦をnh倍，横をnw倍する
    def expand(self,nh,nw):
        self.H = int(self.H*nh)
        self.W = int(self.W*nw)
        self.picture = cv2.resize(self.picture,(self.W,self.H))
    
    def resize(self,h,w):
        self.H = h
        self.W = w
        self.picture = cv2.resize(self.picture,(h,w))
    
    #画像を表示する
    def show(self,figure=None):
        
        if figure != None:
            fig = figure
            fig.axes[0].clear()
            ax = fig.axes[0]
        else:
            fig = plt.figure()
            ax = fig.add_subplot(1,1,1)

        ax.tick_params(labelbottom="off",bottom="off") # x軸の削除
        ax.tick_params(labelleft="off",left="off") # y軸の削除
        
        #divider = axgr.make_axes_locatable(ax)
        #cax = divider.append_axes("right","5%",pad="3%")

        show_result = ax.imshow(cv2.cvtColor(self.picture, cv2.COLOR_BGR2RGB))
            
        #fig.colorbar(show_result,cax=cax) 
        plt.pause(1)

    def turn(self,direction=0):

        """
        反時計回り
        direction==0 : 0度回転
        direction==1 : 90度回転
        direction==2 : 180度回転
        direction==3 : 270度回転
        """
        
        if direction==1:
            self.H ,self.W = self.W ,self.H
            self.picture = self.picture.transpose((1,0,2))[::-1]
        elif direction==2:
            self.picture = self.picture[::-1,::-1]
        elif direction==3:
            self.H ,self.W = self.W ,self.H
            self.picture = self.picture.transpose((1,0,2))[:,::-1]
    
    def set_picture(self,image, hp, wp):
        
        self.picture[hp:hp+image.H, wp:wp+image.W] = image.picture
    
    def draw_corner(self):
        
        r = 30
        x = np.arange(r)
        y = np.arange(r)
        X,Y = np.meshgrid(x,y)
        Z = X**0.5 + Y**0.5 < r**0.5
        Z = Z.reshape(1,r*r)
        color_range = { "b":(120,140), "g":(80,90), "r":(40,70)  }        
        
        for _ in range(4):

            self.turn(1) # 90度回転

            corner = {}
            corner["b"],corner["g"],corner["r"] = self.picture[:r,:r].transpose(2,0,1) #画像の左上をカラーレイヤーごとに取得
            
            for color in ("b","g","r"):

                corner[color] = corner[color].reshape(1,r*r) # 1次元化
                replace = np.random.randint(color_range[color][0],color_range[color][1], r*r).reshape(1,r*r)
                corner[color] = np.where( Z, replace , corner[color] ) # 角をまるめる
                corner[color] = corner[color].reshape(1,r,r) # 2次元化
            
            self.picture[:r, :r] = np.concatenate( [corner["b"],corner["g"],corner["r"]] ).transpose(1,2,0)
    
    def color(self):

        pict = self.picture.transpose(2,0,1)
        pict[0] = pict[0] + 100
        self.picture = pict.transpose(1,2,0)


