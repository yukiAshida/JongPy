from lib.api import game_init, possible_action, get_next_status, decide_action, visualize_status, point_market
from lib.settings import N_Player
from lib.gui import Camera
from lib.utils import show_result
from pprint import pprint
import pickle

def main():

    # ゲームを初期化。返り値は状態インスタンス
    status = game_init()

    # 現在の状態がphase3となったら終了
    while status.phase != 3:

        # 現在の状態に対して、各プレイヤーが選択し得る行動インスタンスを取得
        possible_list = possible_action(status)
        
        # ランダムで各プレイヤーが行動（適当です）
        action = { i: decide_action(possible_list[i]) for i in range(N_Player) }
        # print(*[action[i] for i in range(4) ] ,sep=",   ")

        # 現在の状態に対して、各プレイヤーが適当な行動を実行した際に得られる次の状態と報酬を取得
        status, reward = get_next_status(status,action)

        # 状態オブジェクトから全情報をわかりやすい形で引き抜く
        all_infomation = status.get()

    # 状態オブジェクトを可視化する
    for i in range(N_Player):
        if reward[i] == None:
            print("None")
        elif type(reward[i]) == str:
            print(reward[i])
        else:
            print( show_result( reward[i]["combination"] ) )
            print( reward[i]["kind"],reward[i]["point"],reward[i]["message"] )
    print()

    camera = Camera(0)
    camera.show(visualize_status(status, False))
    

if __name__ == "__main__":
    main()