from .settings import *

import numpy as np
import random

class Group():

    def __init__(self, tiles):
        self.group = tiles # 牌Idのリスト

    def get(self):
        return self.group

    # 萬子の場合は0, 索子の場合は1, 筒子の場合は2, 字牌の場合は3
    def color(self):
        return self.group[0]//9
            
    # 順子の場合は0, 刻子の場合は1を返す(七対子や国士は意味不明な値になるが使わないので無視)
    def shape(self):
        return (len(set(self.group))-3)//(-2)
    
    def only_yaochu(self):
        return not False in [ tile in Used["Yaochu"] for tile in self.group ]

    def count(self,Id):
        return sum([ tile == Id for tile in self.group ])
        
    def include(self,tile_Id):
        return tile_Id%34 in self.group



# 牌をまとまり（鳴き・面子）を表すクラス
class Ments(Group):

    def __init__(self,tiles,dark=True,kind="hand",from_who=None, what=None):

        super().__init__(tiles)
        self.kind = kind # 手牌面子("hand")・ポン("pon")・チー("ti")・暗槓("ankan")・明槓("minkan")・加槓("kakan")
        self.dark = dark # 手牌面子・暗槓でTrue
        self.from_who = from_who # 鳴き牌の場合，だれから鳴いたか（0:左（上家）, 1:対面, 2:右（下家））
        self.what = what # チーの場合どれを鳴いたかが重要

    def add(self,tile_Id):
        self.group.append(tile_Id)
    
    def exclude_red_for_analysis(self):
        group_copy = [ tile%34 for tile in self.group ]
        return Ments(group_copy, self.dark, self.kind, self.from_who, self.what)
    
    
# 雀頭を表すクラス
class Head(Group):

    def __init__(self,tiles):

        super().__init__(tiles)
    
    def yaku(self, field_wind, self_wind ):

        return self.group[0] in Used["Yaku"] + [field_wind, self_wind]


# ターツを表すクラス（0:単騎，1:両面，2:ペンチャン左，3:ペンチャン右，4:カンチャン，5:シャボ）
class Tarts(Group):

    def __init__(self,tiles,kind):

        super().__init__(tiles)
        self.kind = kind # "single":単騎，"double":両面，"left":ペンチャン左，"right":ペンチャン右，"center":カンチャン，"pair":シャボ
    
    def for_complete(self):

        if self.kind == "single":
            return [ self.group[0] ]
        elif self.kind == "double":
            return [ self.group[0]-1, self.group[1]+1 ]
        elif self.kind == "left":
            return [ self.group[1]+1 ]
        elif self.kind == "right":
            return [ self.group[0]-1 ]
        elif self.kind == "center":
            return [ self.group[0]+1 ]
        elif self.kind == "pair":
            return [ self.group[0] ]

    
# プレイヤーを表すクラス
class Player():

    def __init__(self):

        # 手牌
        self.hand = np.zeros(68,dtype=np.int32) #0~33は通常牌，34~67は赤牌
        
        # 捨て牌
        self.garbege = []
        
        # 鳴き牌
        self.squeal = {}
        self.squeal["pon"] = []
        self.squeal["ti"] = []
        self.squeal["minkan"] = []
        self.squeal["ankan"] = []
        
        # 状態変数（ゲーム内でオンオフが切り変わる変数）
        self.last_draw = None # 自摸牌
        self.furiten = 0
        self.one_panch = False
        self.waiting = None # 待ち牌
        self.waiting_method = None # 待ち方(単騎，左右ペンチャン，カンチャン，両面，シャボ)
        self.possible_shoot = False # その巡目にろんできたかどうか（フリテンフラグ操作に関係）
        self.prohibit = [] # 鳴きの喰い替えで次に捨てられない牌ID（0~33）

        # 運命変数（ゲーム内で一度だけオンオフが切り替わる変数）
        self.reach = 0  # 0:通常 1:立直 2:ダブリー
        self.once_squeal = False 

        # ゲーム変数（そのゲーム内では変わらない変数）
        self.self_wind = None
        self.point = None
        self.parent = False
    
    def Tumo(self, tile_Id):

        # 手牌に加える
        self.hand[tile_Id] += 1

    
    def Dump(self, tile_Id):

        # 手牌から削る
        self.hand[tile_Id] -=1

        # 捨て牌に加える
        self.garbege.append(tile_Id)

    def count_tile(self,Id):

        x = self.hand[:34]
        y = self.hand[34:]

        return (x + y)[Id%34]
    
    def hand_table(self):

        table = self.hand.copy()

        for furo in self.squeal["pon"]+self.squeal["ti"]:
            for tile in furo.get():
                table[tile]+=1
            
        for furo in self.squeal["minkan"]+self.squeal["ankan"]:
            for tile in furo.get()[:3]:
                table[tile]+=1
        
        return table[:34] + table[34:]
        
        
    # 暗槓 => already_Id==[i1,i2,i3,i4], new_Id==None
    # 加槓 => already_Id==None,new_Id==None, pos_in_pon==j
    # それ以外  => already_Id==[i1,i2 (,i3)], new_Id==i
    def Squeal(self, squeal_type, already_Id, new_Id, pos_in_pon=None, from_who = None):
        
        # 加槓の場合
        if squeal_type == "kakan":
            
            # 自模った牌を手牌から削る
            self.hand[ self.last_draw ] -= 1

            # ポンを明槓に移す
            pon_group = self.squeal["pon"].pop( pos_in_pon )
            pon_group.add( self.last_draw )
            pon_group.dark = False
            pon_group.kind = "kakan"
            self.squeal["minkan"].append(pon_group)

        # それ以外
        else:

            # 手牌から泣き牌を削る
            for Id in already_Id:
                self.hand[Id] -= 1

            # 暗槓の場合
            if squeal_type == "ankan":
                self.squeal["ankan"].append( Ments(already_Id,True,squeal_type) )
                
            # それ以外の鳴き
            else:
                already_Id.append(new_Id)
                already_Id.sort()
                
                # 赤牌はソートで後ろにくる
                if squeal_type=="ti" and already_Id[2] > 33 :
                    if already_Id[2]%34 < already_Id[0]:
                        already_Id = already_Id[2:] + already_Id[0:2]                    
                    elif  already_Id[-1]%34 < already_Id[1]:
                        already_Id[1],already_Id[2] = already_Id[2],already_Id[1] 

                self.squeal[ squeal_type ].append( Ments(already_Id,False,squeal_type,from_who, new_Id) )

    
class Field():
    
    def __init__(self):
    
        self.mountain = []
        self.show_dora = []
        self.show_uradora = []
        self.rinsyan = []
        self.tumo_num = 0
        self.rinsyan_num = 0

    def init_mountain(self):

        # 山に牌をセット
        self.mountain += [ Id for Id in Used["Id"] if not Id in (4,13,22) ]*4  # 五萬・五索・五筒以外

        # 5の設定
        if Num["min"] <= 5 <= Num["max"]:

            if Exist_Red:
                if N_Color>=1:
                    self.mountain += [ 4 ]*3 + [ 38 ] # 五萬・赤五萬
                if N_Color>=2:
                    self.mountain += [ 13 ]*3 + [ 47 ] # 五索・赤五索
                if N_Color>=3: 
                    self.mountain += [ 22 ]*2 + [ 56 ]*2 # 五筒・赤五筒
            else:
                self.mountain += [4,13,22]*4
            

        #山をシャッフル
        random.shuffle(self.mountain)

        # 嶺上牌とドラ表示牌を分離
        self.cut_rinsyan_and_dora()

    def cut_rinsyan_and_dora(self):
        
        # 山の分割
        self.rinsyan = self.mountain[-1:-5:-1]
        self.show_dora = self.mountain[-5:-14:-2]
        self.show_uradora = self.mountain[-6:-15:-2]
        self.mountain = self.mountain[:-14]

    def tumo(self):
        
        extracted_tile = self.mountain.pop(self.tumo_num)
        self.tumo_num += 1
        self.mountain.insert(0,None)

        return extracted_tile
    
    def rinsyan_tumo(self):

        extracted_tile = self.rinsyan.pop(self.rinsyan_num)
        self.rinsyan_num += 1
        self.rinsyan.insert(0,None)

        return extracted_tile

class Status():

    def __init__(self):

        # 最重要プロパティ        
        self.phase = 0 # どのフェーズか(0,1,2,3) 
        self.who = None # 誰の自摸番か
        self.parent = None # 誰が親か
        
        # ゲームオブジェクト
        self.players = [ Player() for Id in range(N_Player) ]
        self.field = Field()

        # 状態変数
        self.flower = False
        self.kan = []

        # 運命変数
        self.first_turn = True
        self.last_turn = False

        # ゲーム変数
        self.field_wind = False
        self.additional_game = 0

        # 結果変数
        self.method = None # None or "Draw" or "Shoot" 
        self.winner = None
        self.loser = None

    def set_gameinfo(self, field_wind, additional_game, points):

        self.field_wind = field_wind
        self.additional_game = additional_game

        for i in range(N_Player):
            self.players[i].point = points[i]
        
    def left(self):
        return len(self.field.mountain) - self.field.mountain.count(None)
    
    def get(self):

        tiles_Id = [i for i in range(34)]
        tiles_Id.insert(23,56)
        tiles_Id.insert(14,47)
        tiles_Id.insert(5,38)

        all_status = {}

        # 種々の状態変数を取得
        all_status["phase"] = self.phase
        all_status["who_turn"] = self.who
        all_status["rinsyan_tumo"] = self.flower
        all_status["kan"] = self.kan
        all_status["first_turn"] = self.first_turn
        all_status["last_tumo"] = self.last_turn
        all_status["wind"] = self.field_wind
        all_status["honba"] = self.additional_game
        
        # 山の情報を取得
        all_status["mountain"] = [ Id for Id in self.field.mountain if Id!=None ]
        all_status["rinsyan"] = [ Id for Id in self.field.rinsyan if Id!=None ]
        all_status["show_dora"] = [ Id for Id in self.field.show_dora if Id!=None ]
        all_status["show_uradora"] = [ Id for Id in self.field.show_uradora if Id!=None ]
        
        # player i の情報を取得
        for i in range(N_Player):

            all_status["player"+str(i)] = {}

            # 手牌をリストで取得            
            all_status["player"+str(i)]["hand"] = []
            for Id in tiles_Id:
                for _ in range(self.players[i].hand[Id]):
                    all_status["player"+str(i)]["hand"].append(Id)

            # 捨て牌を取得
            all_status["player"+str(i)]["garbege"] = self.players[i].garbege
            
            # プレイヤーが最後に引いた牌
            all_status["player"+str(i)]["last_draw"] = self.players[i].last_draw

            # 鳴き牌をリストのリストで取得
            for squeal in ("pon","ti","ankan","minkan"):
                all_status["player"+str(i)][squeal] = [ ments.get() for ments in self.players[i].squeal[squeal] ]
            
            # フリテン
            all_status["player"+str(i)]["temporary_furiten"] = self.players[i].furiten==1
            all_status["player"+str(i)]["eternal_furiten"] = self.players[i].furiten==2

            # 喰い替えで打牌が禁止される牌
            all_status["player"+str(i)]["prohibition"] = self.players[i].prohibit

            # 待ち牌・待ち方
            all_status["player"+str(i)]["waiting"] = self.players[i].waiting
            all_status["player"+str(i)]["waiting_method"] = self.players[i].waiting_method

            # 立直・ダブリー・一発
            all_status["player"+str(i)]["reach"] = self.players[i].reach == 1
            all_status["player"+str(i)]["dbl_reach"] = self.players[i].reach == 2
            all_status["player"+str(i)]["one_panch"] = self.players[i].one_panch
            
            # 点数・風・親
            all_status["player"+str(i)]["point"] = self.players[i].point
            all_status["player"+str(i)]["wind"] = self.players[i].self_wind
            all_status["player"+str(i)]["parent"] = self.players[i].parent

        return all_status