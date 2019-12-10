from .settings import *

def show_result(result):
    
    result_list = []
    
    for ments in result:
        result_list += ments.get()
    
    return "|"+"|".join( [ tile_formal_name[Id] for Id in result_list ] )+"|"


def show_reward(reward):

    for i in range(N_Player):
        if reward[i] == None:
            print("None")
        elif type(reward[i]) == str:
            print(reward[i])
        else:
            print( show_result( reward[i]["combination"] ) )
            print( reward[i]["kind"],reward[i]["point"],reward[i]["message"] )
    print()