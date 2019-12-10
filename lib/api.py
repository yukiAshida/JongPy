import numpy as np
from .objects import *
from .settings import *
from .action import *
from .analyzer_syanten import SyantenAnalyzer
from .analyzer_winning import WinningAnalyzer
from .calculator import Calculator
from .picture import Picture
from pprint import pprint
import time

def game_init(field_wind=27,additional_game=0, points=[100000,100000,100000,100000]):

    # 状態インスタンスを生成
    status = Status()
    status.set_gameinfo(field_wind, additional_game, points)

    # 山を積む
    status.field.init_mountain()

    # 親を決める(自摸順は親から)
    decide_parent(status)
    
    # 自風の指定
    set_wind_to_players(status)
    
    # 配牌をする
    distribute_tiles_to_players(status)
    
    # 配牌の瞬間の待ち牌をセット
    set_first_waiting(status)

    # 親に最初の自摸を渡す
    first_tumo = status.field.tumo()
    status.players[status.parent].hand[ first_tumo ] += 1
    status.players[status.parent].last_draw = first_tumo

    return status

def decide_parent(status):
    status.parent = np.random.randint(N_Player)
    status.players[status.parent].parent = True
    status.who = status.parent

def set_wind_to_players(status):

    # 親が27，そこから時計回りに28,29,30を割り当てる
    for i,player in enumerate(status.players):
        player.self_wind = (i-status.parent)%N_Player + 27

def distribute_tiles_to_players(status):
    
    for _ in range(N_Tehai):
        for i in range(N_Player):
            who = (status.parent + i) % N_Player
            status.players[who].hand[status.field.tumo()] += 1

def set_first_waiting(status):

    for player in status.players:

        analyzer = SyantenAnalyzer()
        result = analyzer.analyze(player)
        
        # result = 
        #   {  0:{"syanten":n , "combination":None, "waiting":[], "waiting_method":{i:string},
        #      1:{"syanten":n , "combination":None, "waiting":[], "waiting_method":{i:string},
        #   ...
        #   }
        # （nは共通）

        # 待ち牌・待ち方をセット
        player.waiting = result["waiting"]
        player.waiting_method = result["waiting_method"]

def possible_action(status):
    
    """
    Parameters:
    -----------------
    status : class Status
        ゲーム状態を表すクラス

    Returns:
    -----------------
    action : dict
        各プレイヤーの選択可能行動
        { 0: [action_0, ... action_m0], ... ,3:[ action_0, action_m3] ]

    """

    # phase0の場合
    if status.phase == 0:

        # player who がどの行動を選択するか
        # player who 以外はnone行動
        action = { Id : [Nothing()] for Id in range(N_Player) if Id != status.who }
        action[status.who] = action_at_phase0(status)
        return action

    # phase1の場合
    elif status.phase == 1:

        # player who はnone行動
        # player who 以外が槍槓できるかどうか
        
        action = { Id : action_at_phase1(status,Id) for Id in range(N_Player) if Id != status.who}
        action[status.who] = [ Nothing() ]

        return action

    # phase2の場合
    elif status.phase == 2:

        # player who はnone行動
        # player who 以外はどの行動を選択するか

        action = { Id : action_at_phase2(status,Id) for Id in range(N_Player) if Id != status.who}
        action[status.who] = [ Nothing() ]

        return action

    # phase3の場合
    elif status.phase == 3:

        print("game set")
        return
    
    elif status.phase == 4:

        # player who がどの行動を選択するか
        # player who 以外はnone行動
        action = { Id : [Nothing()] for Id in range(N_Player) if Id != status.who }
        action[status.who] = action_at_phase4(status)
        return action

def action_at_phase0(status):

    possible_actions = []
    
    # 自摸順のプレイヤーを取得
    target_player = status.players[status.who]

    # player who がリーチを掛けている場合
    if target_player.reach:
        possible_actions.append( Dump(target_player.last_draw, 0, target_player.waiting, target_player.waiting_method) ) ## 切れる牌は自摸牌のみ
    
    # player who がリーチを掛けていない場合
    else:
        
        for Id in Used["Id"] + [38,47,56]:

            # その牌を持っていなかったらスキップ
            if target_player.hand[Id] == 0:
                continue
            
            # 牌を一度外して，手牌解析を行う
            target_player.hand[Id] -= 1
            analyzer = SyantenAnalyzer()
            result = analyzer.analyze(target_player)
            target_player.hand[Id] += 1
            
            # minimum_result = {
            #     0: { "syanten":S, "combination":None, "waiting":list(int), "waiting_method":str }
            #     1: { "syanten":S, "combination":None, "waiting":list(int), "waiting_method":str }
            #     ...
            #     "syanten" : S
            #     "waiting" : [t1, t2, ... ]
            #     "waiting_method" : { t1:str, t2:str, ... }
            # }

            # 鳴きなし・テンパイ・ラス順以外ならリーチ可能
            if result["syanten"]==0 and not target_player.once_squeal and status.left() > 5+len(status.kan) :
                possible_actions.append( Reach_Dump(Id, result["waiting"], result["waiting_method"]) )

            # テンパイに関係なく手牌14枚中好きな牌を切れる
            possible_actions.append( Dump(Id, result["syanten"], result["waiting"], result["waiting_method"]) )

            ## 同じ牌が4枚あれば暗槓可能(立直後の槓は禁止)
            if (len(status.kan)<4 or len(set(status.kan))==1) and target_player.count_tile(Id) == 4 and not status.last_turn:
                possible_actions.append( Dark_Kan( [Id%34]*target_player.hand[Id%34] + [Id%34+34]*target_player.hand[Id%34+34] ) )

            ## ポンしている場合は加槓可能
            check_in_pon = [ pon.include(Id) for pon in target_player.squeal["pon"] ]
            if (len(status.kan)<4 or len(set(status.kan))==1) and sum(check_in_pon) and not status.last_turn:
                possible_actions.append( Add_Kan( Id, check_in_pon.index(True) ) )

        # 1巡目で9種9牌で鳴きが発生していない場合は、9種9牌可能
        if status.first_turn and sum(target_player.hand[ Used["First"]+Used["Zihai"] ] > 0) >=9:
            possible_actions.append( Nine_Burst() )

    # 和了している場合は自摸上がり可能
    calculator = Calculator()
    result = calculator.calc(status,status.who)

    if result != {} and result["kind"]!="none":
        possible_actions.append( Draw_Kill(result) )

    #print(target_player.hand)
    return possible_actions

# phase1で,player which が選択できる行動
def action_at_phase1(status,which):

    possible_actions = [ Nothing() ]

    # 他家が加槓した牌を一度手牌に加える
    kakan_Id = status.players[status.who].last_draw
    status.players[which].hand[kakan_Id] += 1

    calculator = Calculator()
    result = calculator.calc(status,which)

    if result != {} and not is_dust_furiten(status.players[which]) and status.players[which].furiten==0:
        possible_actions.append( Spear_Kill(result) )
        status.players[which].possible_shoot = True

    # 加えた加槓牌を外す
    status.players[which].hand[kakan_Id] -= 1

    return  possible_actions

# phase2で,player which が選択できる行動
def action_at_phase2(status,which):

    possible_actions = [ Nothing() ]
    
    # 自摸番の人が捨てた牌
    target_tile = status.players[status.who].garbege[-1]

    # 対象となる他家
    target_other = status.players[which]
    
    # リーチをしていない・河底でない時
    if not ( target_other.reach or status.last_turn ):

        # 他家が捨てた牌を対子で持っている場合
        if Possible_Pon and target_other.count_tile(target_tile) == 2:
            possible_actions.append( Pon( [target_tile%34]*target_other.hand[target_tile%34] + [target_tile%34+34]*target_other.hand[target_tile%34+34], target_other.hand[target_tile%34+34] ) )
        
        # 他家が捨てた牌を刻子で持っている場合
        elif target_other.count_tile(target_tile) == 3:

            # 赤牌の枚数の違いを考慮してポン
            if Possible_Pon:
                for i in range(target_other.hand[target_tile%34+34]+1):
                    possible_actions.append( Pon(  [target_tile%34]*(2-i) + [target_tile%34+34]*i , i) )

            # 明槓が可能
            if len(status.kan)<4 or len(set(status.kan))==1:
                possible_actions.append( Light_Kan( [target_tile%34]*target_other.hand[target_tile%34] + [target_tile%34+34]*target_other.hand[target_tile%34+34] ) )


        # チーできるかどうか(上家限定)
        if Possible_Ti and (status.who - which) in (-1,3):
            
            Id = target_tile % 34

            # target_tileが数牌である
            if Id < 27:
                
                target_kind = { 
                    "L":(Id-2, Id-1),
                    "C":(Id-1, Id+1),
                    "R":(Id+1, Id+2),
                    "Lr":(Id-2, Id+33),
                    "LLr":(Id+32, Id-1),
                    "Rr":(Id-1, Id+35),
                    "RRr":(Id+1,Id+36),
                     }
                
                research_target = {
                    0: [ "R" ],
                    1: [ "C", "R" ],
                    2: [ "L", "C", "R", "Rr" ],
                    3: [ "L", "C", "R", "Rr", "RRr" ],
                    4: [ "L", "C", "R" ],
                    5: [ "L", "Lr", "LLr", "C", "R" ],
                    6: [ "L", "Lr", "C", "R"],
                    7: [ "L", "C"],
                    8: [ "L" ]
                }

                for kind in research_target[ Id%9 ]:
                    
                    L,R = target_kind[kind]
                    
                    if target_other.hand[L]*target_other.hand[R]>0:

                        ti_direction = {"L":0,"C":1,"R":2}[kind[0]]
                        prohibit = {"L": [target_tile%34,target_tile%34-3],"R":[target_tile%34,target_tile%34+3],"C":[target_tile%34]}[kind[0]]
                        red_in_ti = target_tile>33 if Id%9 == 4 else "r" in kind
                        possible_actions.append( Ti( [L,R] ,  red_in_ti, ti_direction, prohibit ) )
                
    # ロンできるかどうか
    target_other.hand[target_tile]+=1
    
    calculator = Calculator()
    result = calculator.calc(status,which)

    if result != {} and result["kind"]!="none" and not is_dust_furiten(target_other) and target_other.furiten==0:
        possible_actions.append( Shoot_Kill(result) )
        target_other.possible_shoot = True
    
    target_other.hand[target_tile]-=1
    
    return possible_actions

def action_at_phase4(status):

    possible_actions = []
    
    # 自摸順のプレイヤーを取得
    target_player = status.players[status.who] 

    for Id in Used["Id"] + [38,47,56]:

        # その牌を持っていなかったらスキップ
        if target_player.hand[Id] == 0:
            continue

        # 鳴きの喰い替え禁止
        if Id%34 in target_player.prohibit:
            continue

        # 牌を一度外して，手牌解析を行う
        target_player.hand[Id] -= 1
        analyzer = SyantenAnalyzer()
        result = analyzer.analyze(target_player)
        target_player.hand[Id] += 1
        
        # minimum_result = {
        #     0: { "syanten":S, "combination":None, "waiting":list(int), "waiting_method":str }
        #     1: { "syanten":S, "combination":None, "waiting":list(int), "waiting_method":str }
        #     ...
        #     "syanten" : S
        #     "waiting" : [t1, t2, ... ]
        #     "waiting_method" : { t1:str, t2:str, ... }
        # }

        # テンパイに関係なく手牌14枚中好きな牌を切れる
        possible_actions.append( Dump(Id, result["syanten"], result["waiting"], result["waiting_method"]) )

    # 喰い替え禁止牌をリセット
    target_player.prohibit = []

    return possible_actions

def get_next_status(status, action):

    if status.phase == 0:

        #=== player whoの行動を確認
        check = status.who

        # Dumpの場合
        if action[check].name == "dump":
            
            # 手牌から捨て牌に牌Xを移動
            status.players[check].Dump( action[check].dump_Id )

            # 待ち牌・待ち方をセット
            status.players[check].waiting = action[check].waiting
            status.players[check].waiting_method = action[check].waiting_method

            # 同順内フリテンを解除
            if status.players[check].furiten == 1:
                status.players[check].furiten = 0

            # 一発フラグをオフに
            status.players[check].one_panch = False

            # 共通処理
            ## phaseは2へ
            ## whoはそのまま
            ## 一発は関係なし
            ## 嶺上は関係なし
            ## 初巡は関係なし
            ## 槓は関係なし
            ## 鳴きは関係なし
            common_processing(status, next_phase=2, next_who=check, all_one_panch_off=False, rinsyan_bool=False, first_turn_off=False, kan=False, squeal=False)

        # Reach_Dumpの場合
        elif action[check].name == "reach_dump":
            
            # 手牌から捨て牌に牌Xを移動
            status.players[check].Dump( action[check].dump_Id )

            # リーチフラグをオンにする（初順ならダブリーをオンにする）
            status.players[check].reach = 1 + status.first_turn
            
            # 一発フラグをオンにする
            status.players[check].one_panch = True

            # 待ち牌をセット
            status.players[check].waiting = action[check].waiting
            status.players[check].waiting_method = action[check].waiting_method

            # 共通処理
            ## phaseは2へ
            ## whoはそのまま
            ## 一発は関係なし
            ## 嶺上は関係なし
            ## 初巡は関係なし
            ## 槓は関係なし
            ## 鳴きは関係なし
            common_processing(status, next_phase=2, next_who=check, all_one_panch_off=False, rinsyan_bool=False, first_turn_off=False, kan=False, squeal=False)            

        # Dark_Kanの場合
        elif action[check].name == "dark_kan":
            
            # 手牌から暗槓へ牌を移動
            status.players[check].Squeal( "ankan", action[check].already_Id, None )

            # 嶺上牌をplayer whoの手牌に移動（嶺上自摸）
            drawed_tile = status.field.rinsyan_tumo()
            status.players[check].Tumo(drawed_tile)
            status.players[check].last_draw = drawed_tile

            # 共通処理
            ## phaseはそのまま
            ## whoはそのまま
            ## 一発消滅
            ## 嶺上オン
            ## 初巡消滅
            ## 槓追加
            ## 鳴きはなし
            common_processing(status, next_phase=0, next_who=check, all_one_panch_off=True, rinsyan_bool=True, first_turn_off=False, kan=True,squeal=False)     

        # Add_Kanの場合
        elif action[check].name == "add_kan":
            
            # 手牌とポンから指定の牌を加槓に移動
            status.players[check].Squeal( "kakan", None, None,action[check].pos_in_pon )
            
            # 共通処理
            ## phaseはそのまま
            ## whoはそのまま
            ## 一発は槍槓判定までわからない
            ## 嶺上は槍槓判定までわからない
            ## 加槓が発動してる時点で初巡ではない
            ## 槓追加は槍槓判定までわからない
            ## 鳴き追加は槍槓判定までわからない
            common_processing(status, next_phase=1, next_who=check, all_one_panch_off=False, rinsyan_bool=False, first_turn_off=False, kan=False, squeal=False)     

        # Draw_Killの場合
        elif action[check].name == "draw_kill":
            
            # phaseを3に変更
            status.phase = 3
            
            # statusに結果を記録
            status.method = "Draw"
            status.winner = check

            # 報酬を指定
            reward = [None,None,None,None]
            reward[check] = action[check].result
            return status, reward
            
        # Nine_Burstの場合 
        elif action[check].name == "nine_burst":
            
            # phaseを3に変更
            status.phase = 3

            # 報酬を指定
            reward = [None,None,None,None]
            reward[check] = "nine"
            return status, reward

    elif status.phase == 1:

        #=== player who 以外が槍槓する確認
        check_players = [ player_no for player_no in range(N_Player) if player_no != status.who ]
        
        # === 誰かが槍槓する場合
        for check in check_players:
            if action[check].name == "spear_kill":
            
                # phaseを3に変更
                status.phase = 3

                # statusに結果を記録
                status.method = "Spear"
                status.winner = check
                status.loser = status.who

                # 手牌にロン牌を移動
                speared_tile = status.players[status.who].last_draw
                status.players[check].Tumo( speared_tile )
                status.players[check].last_draw = speared_tile

                # 報酬を指定
                reward = [None,None,None,None]
                reward[check] = action[check].result
                return status,reward

        # === 誰も何もしない場合

        # 槍槓発動者がいないため槓が成立
        # 嶺上牌をplayer whoの手牌に移動（嶺上自摸）
        drawed_tile = status.field.rinsyan_tumo()
        status.players[status.who].Tumo(drawed_tile)
        status.players[status.who].last_draw = drawed_tile

        # 共通処理
        ## phaseは0へ
        ## whoはそのまま
        ## 槓成立のため一発消滅
        ## 槓成立のため嶺上オン
        ## 加槓が発動してる時点で初巡でない
        ## 槓成立のため槓追加
        ## 鳴き追加
        common_processing(status, next_phase=0, next_who=status.who, all_one_panch_off=True, rinsyan_bool=True, first_turn_off=False, kan=True, squeal=True)     


    elif status.phase == 2:
        
        #=== player who 以外の行動を確認
        check_players = [ player_no for player_no in range(N_Player) if player_no != status.who ]
        
        # 誰かがShoot_Killする場合
        for check in check_players:
            if action[check].name == "shoot_kill":

                # phaseを3に変更
                status.phase = 3

                # statusに結果を記録
                status.method = "Shoot"
                status.winner = check
                status.loser = status.who

                # 手牌にロン牌を移動
                shooted_tile = status.players[status.who].garbege[-1]
                status.players[check].Tumo( shooted_tile )
                status.players[check].last_draw = shooted_tile

                # 報酬を指定
                reward = [None,None,None,None]
                reward[check] = action[check].result
                return status,reward

        # 誰もShoot_Killをしなかった場合、もしできた人がいたらフリテン
        for check in check_players:
            if status.players[check].possible_shoot:
                status.players[check].furiten = 1 + (status.players[check].reach!=0)
                status.players[check].possible_shoot = False

        # 誰かがLight_Kanする場合
        for check in check_players:
            if action[check].name == "light_kan":
                
                # そのプレイヤーの手牌から明槓へ指定の牌を移動
                status.players[check].Squeal( "minkan", action[check].already_Id, status.players[status.who].garbege[-1], from_who = (check-status.who)%N_Player-1 )

                # 嶺上牌からその人の手牌に移動
                drawed_tile = status.field.rinsyan_tumo()
                status.players[check].Tumo(drawed_tile)
                status.players[check].last_draw = drawed_tile

                # 共通処理
                ## phaseは0へ
                ## whoは槓した人へ
                ## 一発消滅
                ## 嶺上オン
                ## 初巡消滅
                ## 槓追加
                ## 鳴き追加
                common_processing(status, next_phase=0, next_who=check, all_one_panch_off=True, rinsyan_bool=True, first_turn_off=True, kan=True, squeal=True)   

                return status,[None,None,None,None]

        # 誰かがPonする場合
        for check in check_players:
            if action[check].name == "pon":

                # そのプレイヤーの手牌からポンへ指定の牌を移動
                status.players[check].Squeal( "pon", action[check].already_Id, status.players[status.who].garbege[-1], from_who = (check-status.who)%N_Player-1 )

                # 喰い替え禁止
                status.players[check].prohibit = [ status.players[status.who].garbege[-1]%34 ]

                # 共通処理
                ## phaseは0へ
                ## whoはポンした人へ
                ## 一発消滅
                ## 嶺上オン
                ## 初巡消滅
                ## 槓追加
                ## 鳴き追加
                common_processing(status, next_phase=4, next_who=check, all_one_panch_off=True, rinsyan_bool=False, first_turn_off=True, kan=False,squeal=True)   

                return status,[None,None,None,None]

        # 上家がTiする場合
        right_player = (status.who+1)%N_Player
        if action[ right_player ].name == "ti":

            # そのプレイヤーの手牌からチーへ指定の牌を移動
            status.players[right_player].Squeal( "ti", action[right_player].already_Id, status.players[status.who].garbege[-1])

            # 喰い替え禁止
            status.players[right_player].prohibit = action[ right_player ].prohibit

            # 共通処理
            ## phaseは0へ
            ## whoはチーした人へ
            ## 一発消滅
            ## 嶺上オン
            ## 初巡消滅
            ## 槓追加
            ## 鳴き追加
            common_processing(status, next_phase=4, next_who=right_player, all_one_panch_off=True, rinsyan_bool=False, first_turn_off=True, kan=False,squeal=True)   

            # チーの結果，喰い替え牌しか切れなくなった場合
            hand34 = status.players[right_player].hand[:34]+status.players[right_player].hand[34:]
            if np.sum( hand34[ status.players[right_player].prohibit ] ) == np.sum( hand34 ):
                status.phase = 3
                return status, ["death" if right_player else None for i in range(N_Player)]
            else:
                return status,[None,None,None,None]

        # === 誰も何しない場合

        # 四風連打判定
        if status.first_turn and four_wind_burst(status):
            status.phase = 3
            return status,["four_wind","four_wind","four_wind","four_wind"]

        # 初旬終了判定（鳴き無しで全員の捨て牌が空でなくなる）
        if status.first_turn and sum([ len(status.players[i].garbege) for i in range(N_Player) ]) == N_Player:
            status.first_turn = False

        # もし最終順であれば報酬を指定
        if status.last_turn:
            status.phase = 3
            return status,["flow","flow","flow","flow"]

        # 次が最後であれば、ラスフラグをオン
        elif status.left() <= 3 + len(status.kan):
            status.last_turn = True

        # 四開槓判定
        if four_kan_open(status):
            status.phase = 3
            return status,["four_kan","four_kan","four_kan","four_kan"]
        else:
            status.phase = 0
            status.who = (status.who+1)%N_Player
            drawed_tile = status.field.tumo()
            status.players[status.who].Tumo(drawed_tile)
            status.players[status.who].last_draw = drawed_tile
    
    elif status.phase == 4:

        #=== player whoの行動を確認
        check = status.who

        # Dumpの場合
        if action[check].name == "dump":
            
            # 手牌から捨て牌に牌Xを移動
            status.players[check].Dump( action[check].dump_Id )

            # 待ち牌・待ち方をセット
            status.players[check].waiting = action[check].waiting
            status.players[check].waiting_method = action[check].waiting_method

            # 同順内フリテンを解除
            if status.players[check].furiten == 1:
                status.players[check].furiten = 0

            # 共通処理
            ## phaseは2へ
            ## whoはそのまま
            ## 一発は関係なし
            ## 嶺上は関係なし
            ## 初巡は関係なし
            ## 槓は関係なし
            ## 鳴きは関係なし
            common_processing(status, next_phase=2, next_who=check, all_one_panch_off=False, rinsyan_bool=False, first_turn_off=False, kan=False, squeal=False)

    return status, [None, None, None, None]

def point_market(status):

    winner = status.winner
    loser = status.loser
    parent = status.parent
    
    # 勝者がいない場合
    if winner == None:
        return [0]*N_Player
    
    # 自摸和了
    if loser==None:
        if winner == parent:
            result = [-1/3]*N_Player
        else:
            result = [-1/4]*N_Player
            result[parent] = (-1/2)    
    # ロン・槍槓和了
    else:
        result = [0]*N_Player
        result[loser]=-1

    result[winner]=1
    return result


def common_processing( status, all_one_panch_off, rinsyan_bool, first_turn_off, next_phase, next_who, kan , squeal):

    # 次のphase
    status.phase = next_phase

    # 次のwho
    status.who = next_who

    # 槓の回数を増やす
    if kan:
        status.kan += [next_who]

    # 嶺上フラグをオンにする
    status.flower = rinsyan_bool

    # 全員の一発フラグをオフにする
    if all_one_panch_off:
        for i in range(N_Player):
            status.players[i].one_panch = False

    # 初旬無効判定
    if first_turn_off:
        status.first_turn = False
    
    # 鳴いたかどうかの判定
    if squeal:
        status.players[next_who].once_squeal = True

# statusオブジェクトを可視化
def visualize_status(status, show = True):

    background = Picture("./image/background.png")
    background.resize(4000,4000)
    
    center = Picture("./image/center.jpg")
    center.expand(6,6)

    background.set_picture(center, background.H//2-center.H//2, background.W//2-center.W//2 )

    s1 = 350
    s2 = 100

    Pg = { "h": background.H//2 + 396 ,"w": background.W//2 - 396 } # garbege point
    Pm = { "h": background.H//2 + 396 + 540 + s1 ,"w": background.W//2 + 1122 - 132 } # mountain point
    Ph = { "h": background.H//2 + 396 + 540 + 360 + s1 + s2 ,"w": background.W//2 - 924 } # hand point

    tiles_Id = [i for i in range(34)]
    tiles_Id.insert(23,56)
    tiles_Id.insert(14,47)
    tiles_Id.insert(5,38)

    show_dora =  [z for sublist in [[x, y] for x, y in zip(status.field.show_dora[::-1], status.field.show_uradora[::-1])] for z in sublist]
    mountain = status.field.mountain + show_dora + status.field.rinsyan[2:] + status.field.rinsyan[:2]

    for pi in range(4):

        for i,Id in enumerate(mountain[34*pi:34*(pi+1)]):
            
            if Id == None:
                continue

            h = i % 2
            w = i // 2

            tile = Picture("./image/new_tile/" + tile_name[Id] + ".png")
            tile.expand(2,2)

            background.set_picture(tile,Pm["h"]+tile.H*h,Pm["w"]-tile.W*w)
        
        # 画面を回す
        background.turn(1)


    for pi in range(N_Player):

        for i,Id in enumerate(status.players[pi].garbege):

            h = i // 6
            w = i % 6

            tile = Picture("./image/new_tile/" + tile_name[Id] + ".png")
            tile.expand(2,2)

            if status.method == "Shoot" and status.loser == pi and i == len(status.players[pi].garbege)-1:
                tile.color()

            background.set_picture(tile,Pg["h"]+tile.H*h,Pg["w"]+tile.W*w)
            

        tile_counter = 0
        color_checker = True
        for Id in tiles_Id:

            for _ in range( status.players[pi].hand[Id] ):

                tile = Picture("./image/new_tile/" + tile_name[Id] + ".png")
                tile.expand(2,2)

                if status.method != None and status.winner == pi and status.players[pi].last_draw == Id and color_checker:
                    tile.color()
                    color_checker = False

                background.set_picture(tile, Ph["h"], Ph["w"]+tile.W*(tile_counter))
                tile_counter += 1
            
            # 鳴き牌の塊の最左端
            ments_left = background.W

            for ments in status.players[pi].squeal["pon"]:

                # 面子ごとに最左端をずらす(ments_leftは面子描画中は不変で，tile_leftだけ右にずれていく)
                ments_left -= (132*2 + 180)
                tile_left = ments_left

                for i,Id in enumerate(ments.get()):

                    tile = Picture("./image/new_tile/" + tile_name[Id] + ".png")
                    tile.expand(2,2)

                    # 横で描画
                    if ments.from_who == i:
                        
                        tile.turn(3)
                        background.set_picture(tile, background.H-132 ,tile_left)
                        tile_left += 180

                    # 縦で描画
                    else:

                        background.set_picture(tile, background.H-180 ,tile_left)
                        tile_left += 132


            for ments in status.players[pi].squeal["ti"]:
                
                # 面子ごとに最左端をずらす(ments_leftは面子描画中は不変で，tile_leftだけ右にずれていく)
                ments_left -= (132*2 + 180)
                tile_left = ments_left
                
                # 左端の牌は先に描画
                tile = Picture("./image/new_tile/" + tile_name[ments.what] + ".png")
                tile.expand(2,2)
                tile.turn(3)
                background.set_picture(tile, background.H-132 ,tile_left)
                tile_left += 180

                for i,Id in enumerate(ments.get()):
                    
                    if Id == ments.what:
                        continue

                    tile = Picture("./image/new_tile/" + tile_name[Id] + ".png")
                    tile.expand(2,2)

                    background.set_picture(tile, background.H-180 ,tile_left)
                    tile_left += 132

            for ments in status.players[pi].squeal["minkan"]:

                if ments.kind == "kakan":

                    # 面子ごとに最左端をずらす(ments_leftは面子描画中は不変で，tile_leftだけ右にずれていく)
                    ments_left -= (132*2 + 180)
                    tile_left = ments_left
                    slide_left = None # 横に倒して箇所

                    for i,Id in enumerate(ments.get()):
                    
                        tile = Picture("./image/new_tile/" + tile_name[Id] + ".png")
                        tile.expand(2,2)

                        # 横牌の上に重ねて描画
                        if i == 3:

                            tile.turn(3)

                            if status.method == "Spear" and status.loser == pi:
                                tile.color()

                            background.set_picture(tile, background.H-132*2 ,slide_left)

                        # 横で描画
                        elif ments.from_who == i:
                            
                            tile.turn(3)
                            background.set_picture(tile, background.H-132 ,tile_left)
                            slide_left = tile_left
                            tile_left += 180

                        # 縦で描画
                        else:

                            background.set_picture(tile, background.H-180 ,tile_left)
                            tile_left += 132
                else:

                    # 面子ごとに最左端をずらす(ments_leftは面子描画中は不変で，tile_leftだけ右にずれていく)
                    ments_left -= (132*3 + 180)
                    tile_left = ments_left

                    for i,Id in enumerate(ments.get()):
                    
                        tile = Picture("./image/new_tile/" + tile_name[Id] + ".png")
                        tile.expand(2,2)

                        # 横で描画
                        if ments.from_who + (ments.from_who==2) == i:
                            
                            tile.turn(3)
                            background.set_picture(tile, background.H-132 ,tile_left)
                            tile_left += 180

                        # 縦で描画
                        else:

                            background.set_picture(tile, background.H-180 ,tile_left)
                            tile_left += 132
        
            for ments in status.players[pi].squeal["ankan"]:

                # 面子ごとに最左端をずらす(ments_leftは面子描画中は不変で，tile_leftだけ右にずれていく)
                ments_left -= (132*4)
                tile_left = ments_left

                for i,Id in enumerate(ments.get()):

                    # 横で描画
                    if 1 <= i <= 2:
                        tile = Picture("./image/new_tile/ura.png")
                        tile.expand(2,2)
                    else:
                        tile = Picture("./image/new_tile/" + tile_name[Id] + ".png")
                        tile.expand(2,2)

                    background.set_picture(tile, background.H-180 ,tile_left)
                    tile_left += 132
        
        if status.players[pi].reach:

            stick = Picture("./image/new_tile/stick.png")
            stick.expand(3,3)
            background.set_picture(stick, background.H//2 + 396 - 100, background.W//2-stick.W//2 )

        # 画面を回す
        background.turn(3)

    # 表示
    background.resize(1000,1000)
    if show:
        background.show()
    return background

# 四風連打判定
def four_wind_burst(status):
    return N_Player == 4 and sum([ len(status.players[i].garbege) for i in range(N_Player) ]) == 4 and { status.players[i].garbege[0] for i in range(4) } == {27,28,29,30}
        
# 四開槓判定
def four_kan_open(status):
    return len(status.kan) == 4 and len(set(status.kan))>1
        
# 捨て牌によるフリテンのチェック
def is_dust_furiten(player):
    
    x={Id%34 for Id in player.waiting}
    
    return len({ Id%34 for Id in player.waiting }&{ Id%34 for Id in player.garbege }) > 0

def decide_action(possible_action):

    rank = np.array( [3,2,1,1,2,0,0,0,1,2,2,4 ] )
    
    rank_list = np.array( [ rank[action.no] for action in possible_action ])
    minimum_rank = rank_list.min()

        
    minimum_indexes = np.where( rank_list == minimum_rank )[0]

    if minimum_rank == 3:
        minimum_syanten = min([ possible_action[i].syanten for i in minimum_indexes ])
        syanten_index = np.where( np.array([ possible_action[i].syanten for i in minimum_indexes ]) == minimum_syanten )[0]
        minimum_syanten_index = np.random.choice( syanten_index )
        return possible_action[minimum_syanten_index]
    else:
        x = np.random.choice( minimum_indexes )
        return possible_action[x]
