import cv2

#===カメラオブジェクト===============================================================


class Camera():
    def __init__(self, camera_wait):
        
        #描画設定、描画速度
        self.wait_time=camera_wait

        #クリックポイント管理
        self.mouse_point=[]
        self.click_LR=None
        
    #初期化
    def initialize(self,players):
        
        #設定
        cv2.namedWindow("test", cv2.WINDOW_NORMAL)
        cv2.setMouseCallback("test", self.click)

    def show(self, background):

        # 描画
        cv2.imshow("test", cv2.resize(background.picture, (600,600)))
        cv2.waitKey(self.wait_time)

    def select_TF(self):
        self.click_LR=None
        while True:
            if cv2.waitKey(1) and self.click_LR!=None:
                if self.click_LR=="left":
                    return True
                else:
                    return False
    
    def click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONUP:
            self.mouse_point=[x, y]
            self.click_LR="left"
        elif event == cv2.EVENT_RBUTTONUP:
            self.click_LR="right"
