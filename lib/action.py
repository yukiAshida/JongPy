from .settings import *

class Action():

    def __init__(self,name,no):
        
        # 行動名
        self.name = name
        self.no = no
        self.return_message = None
    
    # 追加
    def __str__(self):
        return ""

class Dump(Action):
    def __init__(self,Id,syanten,waiting,waiting_method):
        super().__init__("dump",0)
        self.dump_Id = Id
        self.syanten = syanten
        self.waiting = waiting
        self.waiting_method = waiting_method # {}

    def __str__(self):
        """
        "dump Id"
        """
        return "dump "+str(self.dump_Id)

class Reach_Dump(Action):
    def __init__(self,Id,waiting,waiting_method):
        super().__init__("reach_dump",1)
        self.dump_Id = Id
        self.waiting = waiting
        self.waiting_method = waiting_method

    def __str__(self):
        """
        "reach_dump Id"
        """
        return "reach_dump "+str(self.dump_Id)

class Dark_Kan(Action):
    def __init__(self,already_Id):
        super().__init__("dark_kan",2)
        self.already_Id = already_Id

    def __str__(self):
        """
        "dark_kan Id"
        """
        return "dark_kan "+str(self.already_Id)

class Add_Kan(Action):
    def __init__(self,Id, pos_in_pon):
        super().__init__("add_kan",3)
        self.Id = Id
        self.pos_in_pon = pos_in_pon

    def __str__(self):
        """
        "add_kann Id"
        """
        return "add_kan "+str(self.Id)

class Nine_Burst(Action):
    def __init__(self):
        super().__init__("nine_burst",4)

    def __str__(self):
        """
        "nine_burst"
        """
        return "nine_burst"


class Draw_Kill(Action):
    def __init__(self,result):
        super().__init__("draw_kill",5)
        self.result = result

    def __str__(self):
        """
        "draw_kill"
        """
        return "draw_kill"


class Shoot_Kill(Action):
    def __init__(self,result):
        super().__init__("shoot_kill",6)
        self.result = result

    def __str__(self):
        """
        "shoot_kill"
        """
        return "shoot_kill"

class Spear_Kill(Action):

    def __init__(self,result):
        super().__init__("spear_kill",7)
        self.result = result
    
    def __str__(self):
        """
        "spear_kill"
        """
        return "spear_kill"

class Light_Kan(Action):
    def __init__(self, already_Id):
        super().__init__("light_kan",8)
        self.already_Id = already_Id

    def __str__(self):
        """
        "light_kan"
        """
        return "light_kan"

class Pon(Action):
    def __init__(self, already_Id, red_num):
        super().__init__("pon",9)
        self.already_Id = already_Id
        self.red_num = red_num # 0,1,2

    def __str__(self):
        """
        Exist_Red == trueの場合
            "pon red"
        Exist_Red == falseの場合
            "pon"
        """
        return "pon"+ ((" "+str(self.red_num)) if Exist_Red else "")

class Ti(Action):
    def __init__(self, already_Id, red_num, lcr, prohibit):
        super().__init__("ti",10)
        self.already_Id = already_Id
        self.red_num = int(red_num) # 0,1
        self.lcr = lcr # 0(left) or 1(center) or 2(right)
        self.prohibit = prohibit
    
    def __str__(self):
        """
        Exist_Red == trueの場合
            "ti direction(left,center,right) red"
        Exist_Red == falseの場合
            "ti direction(left,center,right)"
        """
        return "ti " + ["left","center","right"][self.lcr] + ((" "+str(self.red_num)) if Exist_Red else "")

class Nothing(Action):
    def __init__(self):
        super().__init__("nothing",11)
    
    def __str__(self):
        """
        "nothing"
        """
        return "nothing"