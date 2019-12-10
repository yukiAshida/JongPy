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

class WinningAnalyzer():

    def __init__(self):

        self.possible_head = []
        self.Winning_Result = {}
        self.winning_count = 0

    def analyze(self, player):
        
        # 鳴き牌を統合
        furoes = player.squeal["pon"] + player.squeal["ti"] + player.squeal["ankan"] + player.squeal["minkan"]
        
        # 赤牌を統合
        hand34 = player.hand[:34] + player.hand[34:]

        # 頭として可能性のある牌を検索
        head_key = sum( (np.arange(27)%9+1)*hand34[:27] )%3
        self.possible_head = { 0: [2,5,8,11,14,17,20,23,26], 1: [1,4,7,10,13,16,19,22,25], 2: [0,3,6,9,12,15,18,21,24] }[head_key] + Used["Zihai"]

        self.head_and_zihai_and_naki( hand34, furoes, [] )
        
        if furoes == []:
            self.seven_pairs( hand34 )
            self.thirteen_ophans( hand34 )
        
        return self.Winning_Result

    #数牌の面子を考える
    def ments_of_number(self,left,result,start_color=0,start_number=Num["min"]-1):
        
        added = False

        if sum( (np.arange(27)%9+1)*left[:27] )%3 != 0:
            return

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
                        left_new, result_new = self.extract_from_hand( add_list[key], left, result, kind=0 )

                        #再度面子の検索
                        self.ments_of_number(left_new, result_new, c, n)                    
                        
                        added = True

        #面子を加え終わっていて，和了している場合は結果を記録
        if added==False and len(result)==N_Ments+1:

            self.Winning_Result[self.winning_count]={ "combination": result }
            self.winning_count+=1
    
    #雀頭、字牌、鳴き牌の検索
    def head_and_zihai_and_naki(self,left,furoes,result):
        
        #雀頭
        if N_Tehai <= sum(left) + len(furoes)*3 <= N_Tehai+1 :

            for i in self.possible_head:
                if left[i]>=2:

                    #手牌から雀頭を引き抜いた結果を取得
                    left_new, result_new = self.extract_from_hand([i,i],left,result,kind=1)
                    
                    # 引き続き雀頭を検索
                    self.head_and_zihai_and_naki(left_new, furoes, result_new)

        # 雀頭が無ければ即終了
        if len(result)==0:
            return
        
        # 刻子以外の字牌があれば和了不可
        if len( {1,2,4}&set([ left[Id] for Id in Used["Zihai"] ]) )>0:
            return

        #字牌の暗刻
        for i in Used["Zihai"]:
            if left[i]>=3:

                #手牌の字牌は暗刻以外使用可能性がないため、コピーを生成する必要なし
                left, result = self.extract_from_hand([i,i,i], left, result, kind=0, copy=False)

        #鳴き牌（leftには元々鳴き牌は含まれていないため、鳴き牌はここで処理可）
        for furo in furoes:
            result.append(furo.exclude_red_for_analysis())
        
        #面子の処理に進む
        self.ments_of_number(left,result)
    
    # 手牌から指定した牌を引き抜き，更新した結果を返す
    def extract_from_hand(self, Id_list, left, result, copy=True, kind=0):

        #並列再帰に影響しないようにコピー
        left_return = left.copy() if copy else left
        result_return = result.copy() if copy else result
        
        # 手牌から指定した牌を引き抜く
        for Id in Id_list:
            left_return[Id] -= 1

        new_object = Ments(Id_list) if kind==0 else Head(Id_list)
        
        result_return.append( new_object )
        return left_return, result_return

    #七対子判定用
    def seven_pairs(self,hand):

        index_of_pair = np.where(hand==2)[0]

        # 対子が7個ある場合
        if len(index_of_pair) == 7:
            self.Winning_Result[self.winning_count] = { "combination": [ Ments( [Id,Id] ) for Id in index_of_pair ] }
            self.winning_count+=1
            return
        
    # 国士無双判定用
    def thirteen_ophans(self,hand):
        
        # 幺九牌の種類と対子の確認
        kind = sum( hand[ Used["Yaochu"] ] > 0 )        
        pair = sum( hand[ Used["Yaochu"] ] > 1 ) > 0

        #和了判定の場合の場合
        if kind==13 and pair:
            head = np.where( hand==2)[0][0]
            kokushi_result = [ Ments( [Id] ) for Id in Used["Yaochu"] if Id != head ]
            kokushi_result.insert(0,Head( [head,head] ))
            self.Winning_Result[self.winning_count]={ "combination": kokushi_result }
            self.winning_count+=1