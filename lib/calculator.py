from .analyzer_winning import WinningAnalyzer
from .settings import *
from itertools import combinations
import numpy as np

class Calculator():

    def calc(self,status,target):

        an = WinningAnalyzer()
        player = status.players[target]
        results = an.analyze(player)
        
        if results == {}:
            return {}

        for i in results:
            calc_result = self.calc_part(results[i]["combination"], status, target)
            
            for label in ("kind","point","message"):
                results[i][label] = calc_result[label]
        
        Mi = 0
        Mp = 0
        for i in results:
            if results[i]["point"] > Mp:
                Mi = i
                Mp = results[i]["point"]
        
        return results[Mi]

    def calc_part(self,result,status,target):

        # special[0]=n役満
        # special[1]=Message
        special=self.judge_special(result,status,target)
        if special[0]>0:
            point_special=self.calc_special(special[0],status,target)
            
            return { "kind":"special","point":point_special,"message":special[1] }
        
        # normal[0]=nハン
        # normal[1]=Message
        
        normal=self.judge_normal(result,status,target)

        if normal[0]>0:
            fu=self.calc_base(result,status,target)
            point_normal=self.calc_normal(fu,normal[0],status,target)
            
            return { "kind":"normal","point":point_normal,"message":normal[1] }
        
        return { "kind":"none","point":0,"message":[] }

    def judge_special(self,result,status,target):

        player = status.players[target]

        n_Yakuman=0
        Message=[]
        
        # 必要情報
        colors=[ment.color() for ment in result]

        hand_table=player.hand_table()

        # 天和・地和
        if status.first_turn and status.phase == 0:
            
            if player.parent:
                n_Yakuman+=1
                Message.append("天和")
            elif status.phase == 0 and status.first_turn:
                n_Yakuman+=1
                Message.append("地和")

        #国士無双
        if len(result)==13:
            if result[0].include(player.last_draw):
                n_Yakuman+=2
                Message.append("国士無双13面待ち")
            else:
                n_Yakuman+=1
                Message.append("国士無双")
            return (n_Yakuman,Message)

        #字一色
        if set(colors) == {3}:
            n_Yakuman+=1
            Message.append("字一色")

        # 大車輪
        if set(hand_table[[19,20,21,22,23,24,25]]) == {2}:
            n_Yakuman+=1
            Message.append("大車輪")

        # 七対子の場合はここまで
        if len(result) == 7:
            return (n_Yakuman,Message)

        # 大三元
        if np.sum( hand_table[ Used["Yaku"] ]) == 9:
            n_Yakuman+=1
            Message.append("大三元")

        # 大四喜・小四喜
        if np.sum( hand_table[ Used["Kaze"] ]) == 12:
            n_Yakuman+=2
            Message.append("大四喜")
        elif np.sum( hand_table[ Used["Kaze"] ]) == 11:
            n_Yakuman+=1
            Message.append("小四喜")
        
        # 發無し緑一色・緑一色
        if np.sum( hand_table[ Used["Ryuiso"] ]) == N_Tehai+1:
            if hand_table[32]==0:
                n_Yakuman+=2
                Message.append("發無し緑一色")
            else:
                n_Yakuman+=1
                Message.append("緑一色")
            
        # 清老頭
        if np.sum( hand_table[ Used["First"] ]) == N_Tehai+1:
            n_Yakuman+=1
            Message.append("清老頭")
        
        #四槓子
        if len(player.squeal["minkan"])+len(player.squeal["ankan"])==4:
            n_Yakuman+=2
            Message.append("四槓子")
        
        # 四暗刻単騎・四暗刻
        if sum([ ments.shape() and ments.dark for ments in result[1:] ]) - (status.phase!=0 and player.waiting_method=="pair") == 4:
            if result[0].include(player.last_draw):
                n_Yakuman+=2
                Message.append("四暗刻単騎")
            else:
                n_Yakuman+=1
                Message.append("四暗刻")

        # 純正九漣宝燈・九漣宝燈
        # 頭を一枚抜いて1112345678999の形になっている

        if len(set(colors))==1 and player.once_squeal==False:

            two_or_four = np.where( (hand_table==2)+(hand_table==4) )[0]
            if len(two_or_four)>0:

                hand_table[ two_or_four[0] ]-=1  

                one = set(np.where(hand_table==1)[0]%9) == { Id for Id in range(1,8)}
                three = set(np.where(hand_table==3)[0]%9) == { 0,8 }
                
                if one and three:
                    if two_or_four[0] == player.last_draw:
                        n_Yakuman+=2
                        Message.append("純正九漣宝燈")
                    else:
                        n_Yakuman+=1
                        Message.append("九漣宝燈")

        return (n_Yakuman,Message)
    
    
    def judge_normal(self,result,status,target):
        
        player = status.players[target]

        han=0
        Message=[]
        
        # 色（0=萬子、1=索子、2=筒子、3=字牌）(長さN_Ments+1)
        colors=set([ments.color() for ments in result])
        
        # 副露牌・赤牌も含めた長さ34の牌テーブル
        hand_table = player.hand_table()

        # 非副露時
        if player.once_squeal==False:
            
            if player.reach:
                han += player.reach
                Message.append( ["立直","二重立直"][player.reach-1] )
            
            if player.one_panch:
                han += 1
                Message.append("一発")
            
            if status.phase == 0:
                han += 1
                Message.append("面前自摸")
        
        # 清一色・混一色
        if len(colors)==1: #字一色も清一色が出るけど、字一色優先になるので無視
            han += (6-player.once_squeal)
            Message.append("清一色")
        elif len(colors)==2 and (3 in colors):
            han += (3-player.once_squeal)
            Message.append("混一色")
        
        # 断幺九・混老頭
        if hand_table[ Used["Yaochu"] ].sum() == 0:
            han+=1
            Message.append("断幺九")
        elif hand_table[ Used["Second"]+Used["Third"] ].sum() == 0:
            han+=2
            Message.append("混老頭")
        
        # 海底撈月・河底撈魚
        if status.last_turn:

            if status.phase==0:
                han+=1
                Message.append("海底撈月")
            else:
                han+=1
                Message.append("河底撈魚")        

        # 七対子
        if len(result)==7:
            han+=2
            Message.append("七対子")
        
        #七対子非複合役
        else:

            # 面子構造役の解析用配列の用意

            triple = np.zeros((3,9))
            sequence = np.zeros((3,7))
            
            for ments in result[1:]:

                combination = ments.get()
                c=combination[0] // 9
                n=combination[0] % 9

                # 字牌の場合はスルー
                if c == 3:
                    continue

                # 数牌の面子を登録
                if ments.shape() == 1:
                    triple[c][n]+=1
                elif ments.shape() == 0:
                    sequence[c][n]+=1

            if not player.once_squeal:
                
                # 一盃口・二盃口
                if np.sum( sequence >= 2 ) == 2:
                    han+=3
                    Message.append("二盃口")
                elif np.sum( sequence >= 2 ) == 1:
                    han+=1
                    Message.append("一盃口")
                
                #平和（全て順子で、頭が役牌でない、両面待ち）
                if np.sum(sequence) == N_Ments and not result[0].yaku(status.field_wind, player.self_wind) and player.waiting_method == "double":
                    han+=1
                    Message.append("平和")
            
            # 純全帯幺九・混全帯幺九
            if result[0].get()[0] in Used["First"] and sequence[:,[0,6]].sum()+triple[:,[0,8]].sum()==N_Ments:
                han+=(3-player.once_squeal)
                Message.append("純全帯幺九")
            elif (not "混老頭" in Message) and result[0].get()[0] in Used["First"]+Used["Zihai"] and not (sequence[:,1:6].any() or triple[:,1:8].any()):
                han+=(2-player.once_squeal)
                Message.append("混全帯幺九")

            # 対々和 
            if np.sum(sequence) == 0:
                han+=2
                Message.append("対々和")
            
            # 役牌
            for Id in (31,32,33):    
                if hand_table[ Id ]==3:
                    han+=1
                    Message.append( tile_formal_name[Id] )
                
            # 場風牌
            if hand_table[status.field_wind]==3:
                han+=1
                Message.append("場風牌")
            
            # 自風牌
            if hand_table[player.self_wind]==3:
                han+=1
                Message.append("自風牌")
            
            # 三色同順・一気通貫・三色同刻
            if sequence.all(axis=0).any():
                han+=(2-player.once_squeal)
                Message.append("三色同順")
            elif sequence[:,[0,3,6]].all(axis=1).any():
                han+=(2-player.once_squeal)
                Message.append("一気通貫")
            elif triple.all(axis=0).any():
                han+=2
                Message.append("三色同刻")

            # 小三元
            if sum(hand_table[Used["Yaku"]]) == 8:
                han += 2
                Message.append("小三元")

            # 三槓子
            if len(player.squeal["ankan"])+len(player.squeal["minkan"])==3:
                han+=2
                Message.append("三槓子")

            # 三暗刻（暗刻・暗槓がシャボロンを除いて3つ）
            if sum([ ments.shape() and ments.dark for ments in result[1:] ]) - (status.phase!=0 and player.waiting_method=="pair") == 3:
                han += 2
                Message.append("三暗刻")
                
            # 嶺上開花・槍槓
            if status.flower:
                han+=1
                Message.append("嶺上開花")
            elif status.phase==1:
                han+=1
                Message.append("槍槓")
        
        if han>0:
            dora=get_dora_in_player(status,player)
            if dora>0:
                han+=dora
                Message.append("ドラ{0}".format(dora))

        return (han,Message)
    
   
    #点数計算一般式
    #fu,hanはそれぞれ、符、翻
    def calc_normal(self,fu,han,status,target):
        
        player = status.players[target]

        over_mangan=(0,)*3+(8000,)*3+(12000,)*2+(16000,)*3+(24000,)*2+(32000,)
        
        # 親ならp==1.5、子ならp==1
        p=(player.parent+2)/2
        
        #13翻以上はどうせ数えなので13に統一
        if han>13:
            han=13
        
        han = int(han)

        #マンガン以上判定
        if (han>4) or (han>3 and fu>30) or (han>2 and fu>60):
            point = int(over_mangan[han]*p)+300*status.additional_game
        #マンガン未満判定
        else:
            point = int(down_2_ceil(fu*4*p*(2**(han+2))))+300*status.additional_game

        return int(point)

    #役満点数計算一般式
    #fu,hanはそれぞれ、符、翻
    def calc_special(self,n,status,target):
        
        player = status.players[target]

        p=(player.parent+2)/2
        point=32000*p*n+300*status.additional_game
        
        return int(point)
    
    #符点計算
    def calc_base(self,result,status,target):

        player = status.players[target]

        if len(result)==7:
            return 25

        #副底点
        base=20
        
        #自摸か面前ロンか
        if status.phase==0:
            base+=2
        elif not player.once_squeal:
            base+=10

        #雀頭が役牌かどうか
        if result[0].yaku(status.field_wind,player.self_wind):
            base+=2

        #単騎・カンチャン・ペンチャン
        if player.waiting_method in ("single","left","right","center"):
            base+=2
            
        #暗刻明刻暗槓明槓
        point_list = {"ti":0,"pon":2,"hand":4,"minkan":8,"kakan":8,"ankan":16}
        x = [ ments.shape()*point_list[ments.kind] for ments in result[1:] ] #各メンツの形（暗刻明子暗槓明槓）  
        y = [ ments.only_yaochu()+1 for ments in result[1:] ] #各メンツが么九牌か中張牌か
        base += sum( np.array(x)*np.array(y) )

        # 切り上げ
        base=((base//10)+1)*10

        return base

def result_to_1darray(result):
        
    array=[]
    for r in result:
        array+=list(r)
    
    return array

def combination(n,m):
    """
    nCm 仮り値は[(),(),(),...]
    4C2 なら [(1,2),(1,3),(1,4),(2,3),(2,4),(3,4)]
    """
    
    answer=[]
    for i in combinations(range(1,n+1),m):
        answer.append(i)
    return answer

def get_dora_in_player(status,player):
    """
    playerオブジェクトの持つドラの総計を返す
    """
    
    hand_list = np.concatenate( [ player.hand[:34]+player.hand[34:], player.hand[34:] ] )

    # ドラ表示牌からドラを計算する
    show_dora_list = status.field.show_dora[:1+len(status.kan)]+status.field.show_uradora[:1+len(status.kan)]
    dora_list = [ calc_dora(sd%34) for sd in show_dora_list ] + [ 38, 47, 56 ]

    # 手牌，鳴き牌中のドラ，裏ドラ，赤牌を数える
    dora_in_hand = sum( [ hand_list[d] for d in dora_list ] )
    dora_in_furo = sum( [ sum([ furo.count(d) for d in dora_list]) for furo in player.squeal["pon"]+player.squeal["ti"]+player.squeal["minkan"]+player.squeal["ankan"] ])
    
    return int(dora_in_hand + dora_in_furo)

def calc_dora(showing_dora):
    """
    ドラ表示牌（Id）からドラ(Id)を返す関数
    """

    if showing_dora in Used["Yaku"]:
        if showing_dora == Used["Yaku"][-1]:
            dora=Used["Yaku"][0]
        else:
            dora=showing_dora+1
    elif showing_dora in Used["Kaze"]:
        if showing_dora == Used["Kaze"][-1]:
            dora=Used["Kaze"][0]
        else:
            dora=showing_dora+1
    else:
        if showing_dora in Used["First"][1::2]:
            dora=Used["First"][Used["First"].index(showing_dora)-1]
        else:
            dora=showing_dora+1
    
    return dora

def down_2_ceil(x):
        """
        整数値xの下2桁を切り上げる
        """
        
        if x%100==0:
            return int(x)
        else:
            return int((x//100+1)*100)
