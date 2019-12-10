from lib.api import game_init, possible_action, get_next_status, decide_action, visualize_status
from lib.settings import *
from lib.utils import show_result
import numpy as np
import time
from lib.gui import Camera

def main():

    camera = Camera(0)
    
    # ゲームを初期化。返り値は状態インスタンス
    status = game_init()

    # 現在の状態がphase3となったら終了
    while status.phase != 3:

        # 現在の状態に対して、各プレイヤーが選択し得る行動インスタンスを取得
        possible_list = possible_action(status)

        # ランダムで各プレイヤーが行動（適当です）
        # action = { i : np.random.choice(possible_list[i]) for i in range(N_Player)} 
        action = { i: decide_action(possible_list[i]) for i in range(N_Player) }

        # 現在の状態に対して、各プレイヤーが適当な行動を実行した際に得られる次の状態と報酬を取得
        status, reward = get_next_status(status,action)

        background = visualize_status( status, False )
        camera.show(background)
    
    # 最終的に得られた状態と報酬を表示（一応）
    #print(status.get())
    for i in range(N_Player):
        if reward[i] == None:
            print("None")
        elif type(reward[i]) == str:
            print(reward[i])
        else:
            print( show_result( reward[i]["combination"] ) )
            print( reward[i]["kind"],reward[i]["point"],reward[i]["message"] )
    print()
    
if __name__ == "__main__":
    main()