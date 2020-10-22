import pandas as pd 
import warnings 

def fxn():
    warnings.warn("deprecated", DeprecationWarning)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    fxn()

#import moneyline csv file
bov=pd.read_csv("nba_bets12.csv") 

class Bets():
    def __init__(self):
        pass

    def bets_calc(self):
        
        def ev_calc(row):
            bet=10 
            p_fav=row['o_fav_open']/(row['o_fav_open']+100)
            p_under=100/(row['o_under_open']+100)

            #remove vig and get vegas open probabilities 
            vig=p_fav+p_under
            p_fav_veg=p_fav/vig
            p_under_veg=p_under/vig 

            EV_fav=(p_fav_veg*(100/row['o_fav_bov'])*bet)-(p_under_veg*bet)
            EV_under=(p_under_veg*(row['o_under_bov']/100)*bet)-(p_fav_veg*bet)

            return EV_fav,EV_under 

        bov['ev']=bov.apply(ev_calc,axis=1) 

        bet=10 #establish baseline bet 
    
        #split expected value column (for favorite and underdog) 
        ev_cols=pd.DataFrame(bov['ev'])
        ev_cols=ev_cols.astype('str')

        ev_cols=ev_cols['ev'].str.split(' ', expand=True)
        ev_cols.columns=['ev_fav','ev_under']
        ev_cols['ev_fav'] = ev_cols['ev_fav'].map(lambda x: x.lstrip('+(').rstrip('aAbBcC'))
        ev_cols['ev_fav'] = ev_cols['ev_fav'].astype('str').str[0:10]
        ev_cols['ev_fav'] = ev_cols['ev_fav'].map(lambda x: x.lstrip(')').rstrip('aAbBcC'))
        ev_cols['ev_under'] = ev_cols['ev_under'].astype('str').str[0:10]
        ev_cols['ev_under'] = ev_cols['ev_under'].str.replace(')', '')
        bov_final=pd.concat([ev_cols,bov],axis=1)
        bov_final=bov_final.loc[:,~bov_final.columns.duplicated()]
        bov_final.to_csv("updated_bets.csv")
        bf=bov_final[["Game","ev_fav","ev_under","o_fav_bov","o_under_bov","Source","date","win","o_fav_open","o_under_open"]] #add bet amount later???? 
        bf= bf.loc[:,~bf.columns.duplicated()]
        bf['ev_fav'] = bf['ev_fav'].str.replace(',', '')
        bf['ev_under'] = bf['ev_under'].str.replace(',', '')

        #win probabilities (based on vegas opening lines)
        bf['win_fav']=bf['o_fav_open']/(bf['o_fav_open']+100)
        bf['win_under']=100/(bf['o_under_open']+100)

        #remove vig and get vegas open probabilities
        vig=bf['win_fav']+bf['win_under']
        bf['win_fav']=bf['win_fav']/vig 
        bf['win_under']=bf['win_under']/vig 

        #subset games that have been played only
        bf1=bf[(bf.win==1) | (bf.win==0)] 
        bf1['ev_fav']=bf1['ev_fav'].astype(float)
        bf1['ev_under']=bf1['ev_under'].astype(float)

        #positive EV bets (favorite team)
        plus_fav=bf1[bf1.ev_fav>0.25] #set expected value threshold 

        def fav_profit(row):
            if row['win']==1:
                return bet*2 
            else:
                return -(row['o_fav_bov']/10)

        plus_fav['total_money']=plus_fav.apply(fav_profit,axis=1)

        #check favorite profits
        w_fav=plus_fav[plus_fav.win==1]
        p1_fav=w_fav.total_money.sum()-(w_fav.shape[0]*bet)
        l_fav=plus_fav[plus_fav.win==0]
        p2_fav=l_fav.total_money.sum()
        p2_fav=p2_fav*-1 
        profit_money_fav=p1_fav-p2_fav 
        money_bet_fav=profit_money_fav/plus_fav.shape[0]
        print(money_bet_fav)
       
        #positive EV bets (underdog)
        plus_under=bf1[bf1.ev_under>0.25] 
        plus_under['o_under_bov']=plus_under['o_under_bov'].astype(float)

        def under_profit(row):
            if row['win']==0:
                return ((row['o_under_bov']/10)+bet)
            else:
                return -bet  

        plus_under['total_money']=plus_under.apply(under_profit,axis=1)

        #check underdog profits
        w_under=plus_under[plus_under.win==0]
        p1_under=w_under.total_money.sum()-(w_under.shape[0]*bet)
        l_under=plus_under[plus_under.win==1]
        p2_under=l_under.total_money.sum()
        p2_under=p2_under*-1 
        profit_money_under=p1_under-p2_under  
        money_bet_under=profit_money_under/plus_under.shape[0]
        print(money_bet_under)

        #total profits 
        total_profits=profit_money_fav+profit_money_under
        print(total_profits)

        #select null rows
        hoy=bf.loc[bf['win'].isnull()]
        hoy['ev_fav']=hoy['ev_fav'].astype(float)
        hoy['ev_under']=hoy['ev_under'].astype(float)

        #favorites today 
        fav_hoy=hoy[hoy.ev_fav>0.20]
        fav_hoy1=hoy[hoy.ev_under>0.20]
        print(fav_hoy)
        print(fav_hoy1) 

        #save plus over and plus over to dataframes
        plus_fav1=plus_fav[plus_fav.total_money<0]
        plus_fav1['profit']=plus_fav1['total_money']
        plus_fav2=plus_fav[plus_fav.total_money>=0]
        plus_fav2['profit']=plus_fav2['total_money']-bet 
        plus_fav=pd.concat([plus_fav1,plus_fav2],axis=0)

        plus_under1=plus_under[plus_under.total_money<0]
        plus_under1['profit']=plus_under1['total_money']
        plus_under2=plus_under[plus_under.total_money>=0]
        plus_under2['profit']=plus_under2['total_money']-bet 
        plus_under=pd.concat([plus_under1,plus_under2],axis=0)

        plus_fav.to_csv("plus_fav.csv")
        plus_under.to_csv("plus_under.csv")

if __name__=='__main__':
    mlb_bets=Bets() 
    mlb_bets.bets_calc() 


