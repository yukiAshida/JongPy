from .objects import *
from .settings import *

import numpy as np
from collections import OrderedDict

"""
left : 判定に使用されていない残された手牌（34状態）
result : 実際にどの組み合わせで手牌が分割されたかを表すリスト [ (2,2), (10,11,12), ... , ]
stamp : stamp[0]は面子の数、stamp[1]は雀頭の数、stamp[2]はターツの数

naki : 鳴きの種類に関わらず、鳴いた牌を [(...), (...), ] の形でまとめる
"""

class SyantenAnalyzer():

    def __init__(self):

        self.Syanten_Result = {}
        self.syanten_count = 0
        self.syanten_minimum = 10

    def analyze(self, player):
        
        # 鳴き牌を統合
        furoes = player.squeal["pon"] + player.squeal["ti"] + player.squeal["ankan"] + player.squeal["minkan"]
        
        # 赤牌を統合
        hand34 = player.hand[:34] + player.hand[34:]
        
        # 孤立牌の確認
        self.head_and_zihai_and_naki( hand34 , furoes, [], [0,0,0] )
        
        if furoes == []:
            self.seven_pairs( hand34 )
            self.thirteen_ophans( hand34 )

        # シャン点数が最小になる結果を取得
        minimum_result = { i: each_result for i,each_result in enumerate( [ each_result for each_result in self.Syanten_Result.values() if each_result["syanten"] == self.syanten_minimum ] ) }

        # 待ち牌・待ち方            
        waiting = []
        waiting_method = {}

        for result_part in minimum_result.values():

            # 待ち牌を追加                
            waiting += result_part["waiting"]
            
            # 待ち方を追加
            for waiting_tile in result_part["waiting"]:
                
                # 両面とみなせる場合は両面指定
                if not(waiting_tile in waiting_method and waiting_method[waiting_tile]=="double"):
                    waiting_method[waiting_tile] = result_part["waiting_method"]
        
        # 重複する待ち牌を削除
        waiting = list(set(waiting))
        minimum_result["syanten"] = self.syanten_minimum
        minimum_result["waiting"] = waiting
        minimum_result["waiting_method"] = waiting_method

        # minimum_result = {
        #     0: { "syanten":S, "combination":None, "waiting":list(int), "waiting_method":str }
        #     1: { "syanten":S, "combination":None, "waiting":list(int), "waiting_method":str }
        #     ...
        #     "syanten" : S
        #     "waiting" : [t1, t2, ... ]
        #     "waiting_method" : { t1:str, t2:str, ... }
        # }

        return minimum_result
    
    #数牌の面子を考える
    def ments_of_number(self,left,result,stamp,start_color=0,start_number=Num["min"]-1):
        
        added = False

        #前回調べた色から調査開始
        for c in range(start_color, N_Color):
            
            #前回調べた数から調査開始（色が変わったら再度0から検索）
            for n in range( (0,start_number)[c==start_color] ,Num["max"] ):
                
                #牌Idを取得
                Id = c*9+n

                # 面子の条件を取得
                add_list = { "order":[Id,Id+1,Id+2], "triple":[Id,Id,Id] }
                condition = OrderedDict()
                condition["order"] = n < Num["max"]-2 and left[Id]*left[Id+1]*left[Id+2] > 0
                condition["triple"] = left[Id]>=3
                
                # 面子,順子を手牌から引き抜く
                for key, value in condition.items():
                    
                    # 条件を満たす場合は
                    if value:

                        #対象となるターツを手牌から引き抜く
                        left_new, result_new, stamp_new = self.extract_from_hand( add_list[key], left, result, stamp, kind=0 )

                        #再度面子の検索
                        self.ments_of_number(left_new, result_new, stamp_new, c, n)                    
                        
                        added = True
    

        #面子を加え終わったら、ターツ検索に進む
        if added==False:

            #字牌のターツ
            for i in Used["Zihai"]:
                if left[i]==2:
                    self.extract_from_hand( [i,i], left, result, stamp, kind=2, tarts_kind="pair", copy=False )

            #数牌のペンチャン、カンチャン、両面、対子の検索に進む
            self.tarts_of_number(left,result,stamp)

    #数牌のターツを考える
    def tarts_of_number(self,left,result,stamp,start_color=0,start_number=Num["min"]-1):

        added = False

        #前回調べた色から調査開始
        for c in range(start_color,N_Color):

            #前回調べた数から調査開始
            for n in range((0,start_number)[c==start_color],Num["max"]):
                
                #牌Idを取得
                Id = c*9 + n
                add_list = { "left":[Id,Id+1], "right":[Id,Id+1], "double":[Id,Id+1], "center":[Id,Id+2], "pair":[Id,Id] }
                
                condition = OrderedDict()
                condition["left"] = n==Num["min"]-1 and left[Id]*left[Id+1]>0 and left[Id+2]==0
                condition["right"] = n==Num["max"]-2 and left[Id]*left[Id+1]>0 and left[Id-1]==0
                condition["double"] = Num["min"]-1 < n < Num["max"]-2 and left[Id]*left[Id+1]>0 and left[Id-1]==0 and left[Id+2]==0
                condition["center"] = n < Num["max"]-2 and left[Id]*left[Id+2]>0 and left[Id+1]==0
                condition["pair"] = left[Id]>=2
        
                # ペンチャン，両面，カンチャン，シャボを検索
                for key, value in condition.items():
                    
                    # 条件を満たす場合は
                    if value:

                        #対象となるターツを手牌から引き抜く
                        left_new, result_new, stamp_new = self.extract_from_hand( add_list[key], left, result, stamp, kind=2, tarts_kind=key )

                        #再度面子の検索
                        self.tarts_of_number(left_new, result_new, stamp_new, c, n)                    
                        
                        added = True
                
                

        #ターツを加えている場合は、以下考慮する必要なし
        if added == False:
            
            #シャンテン数の計算
            s = 2*N_Ments - 2*stamp[0] - stamp[1] - min(stamp[2], N_Ments-stamp[0])

            #シャンテン数と待ち牌を渡す（牌の組み合わせは不要っぽい？）
            self.Syanten_Result[self.syanten_count] = {
                "syanten":s,
                "combination":None,
                "waiting": [] if s!=0 else ( np.where(left==1)[0].tolist() if 1 in left else result[-1].for_complete() ),
                "waiting_method": {} if s!=0 else ( "single" if 1 in left else result[-1].kind )
            }
            
            self.syanten_minimum = min(s, self.syanten_minimum)
            self.syanten_count += 1
    
    #雀頭、字牌、鳴き牌の検索
    def head_and_zihai_and_naki(self,left,furoes,result,stamp):
        
        #雀頭
        if N_Tehai <= sum(left) + len(furoes)*3 <= N_Tehai+1 :
            
            for i in Used["Id"]:
                if left[i]>=2:

                    #手牌から雀頭を引き抜いた結果を取得
                    left_new, result_new, stamp_new = self.extract_from_hand([i,i],left,result,stamp,kind=1)
                    
                    # 引き続き雀頭を検索
                    self.head_and_zihai_and_naki(left_new, furoes, result_new, stamp_new)
    
        #字牌の暗刻
        for i in Used["Zihai"]:
            if left[i]>=3:

                #手牌の字牌は暗刻以外使用可能性がないため、コピーを生成する必要なし
                left, result, stamp = self.extract_from_hand([i,i,i], left, result, stamp, kind=0, copy=False)

        #鳴き牌（leftには元々鳴き牌は含まれていないため、鳴き牌はここで処理可）
        for furo in furoes:
            result.append(furo.exclude_red_for_analysis())
            stamp[0]+=1
        
        #面子の処理に進む
        self.ments_of_number(left,result,stamp)
    
    # 手牌から指定した牌を引き抜き，更新した結果を返す
    def extract_from_hand(self, Id_list, left, result, stamp, copy=True, kind=0, tarts_kind=None):

        #並列再帰に影響しないようにコピー
        left_return = left.copy() if copy else left
        result_return = result.copy() if copy else result
        stamp_return = stamp.copy() if copy else stamp
        
        # 手牌から指定した牌を引き抜く
        for Id in Id_list:
            left_return[Id] -= 1

        new_object = Ments(Id_list) if kind==0 else ( Head(Id_list) if kind==1 else Tarts(Id_list, tarts_kind) )
        
        result_return.append( new_object )
        stamp_return[kind] += 1
        
        return left_return, result_return, stamp_return

    #七対子判定用
    def seven_pairs(self,hand):

        # 対子を数えてグループ化
        index_of_pair = np.where(hand==2)[0]
        result = [ Ments( [Id,Id] ) for Id in index_of_pair ]

        # 対子以上と槓子をカウント
        pair = np.sum( hand >= 2 )
        four = np.sum( hand == 4 )
    
        # 向聴数を計算
        syanten = 6-pair+four
        waiting = np.where(hand%2==1)[0].tolist() if syanten == 0 else []
        self.Syanten_Result[self.syanten_count] = { "syanten":syanten,"combination":None, "waiting": waiting, "waiting_method":"single" }
        
        # 最小向聴数を更新
        self.syanten_minimum = min( syanten, self.syanten_minimum )
        self.syanten_count += 1

    # 国士無双判定用
    def thirteen_ophans(self,hand):
        
        # 幺九牌の種類と対子の確認
        kind = sum( hand[ Used["Yaochu"] ] > 0 )
        pair = sum( hand[ Used["Yaochu"] ] > 1 ) > 0
        
        # 向聴数を計算
        syanten=13-kind-pair
        waiting = [] if syanten>0 else ( [Id for Id in Used["Yaochu"]] if not pair else [Id for Id in Used["Yaochu"] if hand[Id]==0] ) 
        self.Syanten_Result[self.syanten_count]={"syanten":syanten,"combination":None,"waiting":waiting, "waiting_method":"single"}

        # # 最小向聴数を更新
        self.syanten_minimum = min( syanten, self.syanten_minimum )
        self.syanten_count += 1
