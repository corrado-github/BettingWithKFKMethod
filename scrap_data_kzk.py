#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 21 09:48:04 2023

@author: corrado
"""

from bs4 import BeautifulSoup
import requests
import pandas as pd
import datetime as dt
import os, sys
import pdb
from scrap_data_funcs import *

import numpy as np





#%%
####################################
cols_odds = ['WebSite', 'LeagueName', 'MatchTime', 'MatchDay', 'HomeTeam', 'GuestTeam', 'odd1', 'oddX', 'odd2', 'DayTime']
df_odds_mean = pd.DataFrame(columns=cols_odds)
df_odds = pd.DataFrame(columns=cols_odds)
#
cols_results = ['WebSite', 'LeagueName', 'MatchTime', 'MatchDay', 'HomeTeam', 'GuestTeam', 'HomeScore', 'GuestScore', 'DayTime']
#
#%%
# set service and options for firefox/selenium
def init_firefox():
    profile_path = '/home/corrado/snap/firefox/common/.cache/mozilla/firefox/5m2b7fvi.default-1427110999701'
    options=Options()
    options.headless = True #for headless
    options.set_preference('profile', profile_path)
    service = Service('/snap/bin/firefox.geckodriver')
    return options, service
#%%
#get the data in a dataframe
from scrap_data_funcs import *
options, service = init_firefox()
df_odds_mean = get_betexplorer(df_odds_mean, service, options)

#%%
# compute corrected odds
def compute_corr_odds(row):
    prob1 = 1./row.odd1
    probX = 1./row.oddX
    prob2 = 1./row.odd2
    probs = np.array([prob1, probX, prob2])
    #pdb.set_trace()
    rounding = probs.sum() - 1.
    #probs_corr = probs - rounding/3.
    probs_corr = np.where(probs>rounding, probs - rounding/3., 0.01)
    return 1./probs_corr[0], 1./probs_corr[1], 1./probs_corr[2]

df_odds_mean[['odd1_corr', 'oddX_corr', 'odd2_corr']] = df_odds_mean.apply(lambda row: pd.Series(compute_corr_odds(row)), axis=1)


#%%
from scrap_data_funcs import *
options, service = init_firefox()
df_odds = scrap_eurobet(df_odds, service, options)
#%%
from scrap_data_funcs import *
options, service = init_firefox()
df_odds = scrap_sisal(df_odds, service, options)
#%%
from scrap_data_funcs import *
options, service = init_firefox()
df_odds = scrap_888sport(df_odds, service, options)
#remove duplicates
dup_bool=df_odds.duplicated()
idx2drop = df_odds[dup_bool].index
df_odds.drop(idx2drop, inplace=True)


#%%
from scrap_data_funcs import *
options, service = init_firefox()
df_results = get_betexplorer_results(cols_results, service, options)


#%%
from scrap_data_funcs import *
idx_ll = join_games_lists(df_odds_mean, df_odds)
df_bets = crossmatch_odds(idx_ll, df_odds_mean, df_odds)

#%%
#make a dataframe

#join it with the archive
curr_dir = os.getcwd()
bets_file_name = '/bet_to_place.csv'
bets_file_path = curr_dir + bets_file_name
if os.path.isfile(bets_file_path):
    df_bets_old = pd.read_csv(bets_file_path, index_col=False)
    df_bets2write = pd.concat([df_bets_old, df_bets], ignore_index=True)
    # write it
    df_bets2write.to_csv(path_or_buf=bets_file_path, index=False)
else:
    df_bets.to_csv(path_or_buf=bets_file_path, index=False)
        
#%%
# check if there are bets for days that had no downloaded results
#ll_res = df_bets_results_old.DayTime.apply(lambda x: x[:10]).drop_duplicates().values.tolist()
#ll_bets = df_bets_old.DayTime.apply(lambda x: x[:10]).drop_duplicates().values.tolist()
#missing_ll = [item for item in ll_bets if item not in ll_res]


#%%
from scrap_data_funcs import *
#df_test = df_results.iloc[1229:]
idx_ll = join_games_lists(df_bets_old, df_results)
df_bets_results = crossmatch_bets_results(idx_ll, df_bets_old, df_results)

bets_file_name = '/bet_placed_profit.csv'
bets_file_path = curr_dir + bets_file_name
if os.path.isfile(bets_file_path):
    df_bets_results_old = pd.read_csv(bets_file_path, index_col=False)
    df_bets_results2write = pd.concat([df_bets_results_old, df_bets_results], ignore_index=True)
    #remove duplicates
    dup_bool=df_bets_results2write.duplicated()
    idx2drop = df_bets_results2write[dup_bool].index
    df_bets_results2write.drop(idx2drop, inplace=True)
    df_bets_results2write.to_csv(path_or_buf=bets_file_path, index=False)
else:
    df_bets_results.to_csv(path_or_buf=bets_file_path, index=False)

#%%
import seaborn as sns
df_bets_results2write['cumsum'] = df_bets_results2write.Profit.cumsum()
sns.lineplot(data=df_bets_results2write.reset_index(), y="cumsum", x="index")