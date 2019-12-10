import numpy as np
import random
import json

# 設定ファイルを読み込み
f = open("./settings.json","r",encoding="utf-8")
data = json.load(f)
f.close()

# 各値を設定
N_Player = data["player"] # プレイヤー人数（2~4）
N_Ments = data["ments"] # 構成面子数
N_Color = data["color"] # 色の数(1~3で萬→索→筒の順に使用)
N_Tehai = 3*N_Ments+1 # 3N+1(N面子1雀頭)
Num = { "min":data["number_min"], "max":data["number_max"] } #最小は1、最大は5以上推奨 （ (1,5)なら一萬~五萬を使用（他の色も同様） ）
Zihai = data["zihai"] #自由

# 鳴きの設定
Possible_Pon = data["possible_pon"]
Possible_Ti = data["possible_ti"]

# 赤牌の設定
Exist_Red = data["exist_red"]

tile_name=["m1","m2","m3","m4","m5","m6","m7","m8","m9",
           "s1","s2","s3","s4","s5","s6","s7","s8","s9",
           "p1","p2","p3","p4","p5","p6","p7","p8","p9",
           "T","N","S","P","Hk","Ht","Ch"] +\
          ["-","-","-","-","mr","-","-","-","-",
           "-","-","-","-","sr","-","-","-","-",
           "-","-","-","-","pr","-","-","-","-",
           "-","-","-","-","-","-","-"]

tile_formal_name=("一萬","二萬","三萬","四萬","五萬","六萬","七萬","八萬","九萬",
                  "一索","二索","三索","四索","五索","六索","七索","八索","九索",
                  "一筒","二筒","三筒","四筒","五筒","六筒","七筒","八筒","九筒",
                  "東","南","西","北","白","發","中") +\
                  ("-","-","-","-","赤五萬","-","-","-","-",
                   "-","-","-","-","赤五索","-","-","-","-",
                   "-","-","-","-","赤五筒","-","-","-","-",
                   "-","-","-","-","-","-","-")

zihai_name_to_id={"T":27,"N":28,"S":29,"P":30,"Hk":31,"Ht":32,"Ch":33}

#各使用Id
Used = {}
Used["First"] = [ Num["min"]-1+c*9 for c in range(N_Color) ] + [ Num["max"]-1+c*9 for c in range(N_Color) ]
Used["Second"] = [ Num["min"]+c*9 for c in range(N_Color) ] + [ Num["max"]-2+c*9 for c in range(N_Color) ]
Used["Third"] = [ n+c*9 for c in range(N_Color) for n in range(Num["min"]+1,Num["max"]-2) ]
Used["Kaze"] = [ zihai_name_to_id[z] for z in Zihai if zihai_name_to_id[z] <= 30 ]
Used["Yaku"] = [ zihai_name_to_id[z] for z in Zihai if zihai_name_to_id[z] > 30 ]
Used["Zihai"] = Used["Kaze"] + Used["Yaku"]
Used["Yaochu"] = Used["First"] + Used["Zihai"]
Used["Id"] = Used["First"] + Used["Second"] + Used["Third"] + Used["Zihai"]
Used["Ryuiso"] = [10,11,12,14,16,32]