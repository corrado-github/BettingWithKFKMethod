#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 27 15:35:01 2023

@author: corrado

sites hard to scrap: 1xbet, bet365, betfair
"""

from bs4 import BeautifulSoup
import requests
import pandas as pd
import datetime as dt
import time
import os, sys
import pdb

import numpy as np
from thefuzz import fuzz
from difflib import SequenceMatcher

from selenium import webdriver

from selenium.webdriver import Firefox
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
####################
def get_soup(url):

    data  = requests.get(url, headers={'User-Agent':'foo'}).text
    soup = BeautifulSoup(data, "html5lib") # "html.parser") #"html5lib")
    time = dt.datetime.now()
    return soup, time
###################  
def make_macth_dict(df):
    match_dict = dict.fromkeys(list(df.columns))
    for key in match_dict.keys():
        match_dict[key] = []
        
    return match_dict
#####################
def get_betexplorer_results(cols_results, service, options):
    url = "https://www.betexplorer.com/football/results/"

    df = pd.DataFrame(columns=cols_results)

    driver = Firefox(service=service, options=options)
    driver.implicitly_wait(10)
    driver.get(url)
    #time to load the page
    time.sleep(3)

    #scroll down the page
    #find footer
    elem = driver.find_element(By.CSS_SELECTOR, "footer.footer")
    #scroll down
    elems = driver.find_elements(By.CSS_SELECTOR, "tbody")
    items_len = len(elems)
    while True:
        driver.execute_script("arguments[0].scrollIntoView();", elem)
        time.sleep(1)
        elems = driver.find_elements(By.CSS_SELECTOR, "tbody")
        if len(elems) == items_len:
            break
        else:
            items_len = len(elems)

    element_html= driver.find_element(By.CLASS_NAME,"wrap-section").get_attribute('outerHTML')
    #quit the browser
    #driver.quit()

    nowtime = dt.datetime.now()
    soup = BeautifulSoup(element_html, 'html.parser')
    #quit the browser
    driver.quit()
    #prepare the dictionary
    match_dict = make_macth_dict(df)
    
    ll = soup.find_all("tbody")
    
    #pdb.set_trace()

    date = soup.find('a', class_="in-date-navigation__cal")

    for league in ll:
        if 'js-nrbanner-tbody' in str(league):
            continue
        rows_ll = league.find_all('tr')
        league_name = rows_ll[0].find('a').text.strip()

        for match in rows_ll[1:]:
            matchtime = match.find('td').span.text.strip()
            match_details_ll = match.find_all('a')
            try:
                teams_ll = match_details_ll[0].text.split(' - ')
                if len(teams_ll) == 2:
                    hometeam, guestteam = teams_ll
                else:
                    team_strong = match_details_ll[0].strong.text
                    subtr_str = match_details_ll[0].text.replace(match_details_ll[0].strong.text, '').replace(' - ','')
                    if team_strong[:3] == teams_ll[0][:3]:
                        hometeam = team_strong
                        guestteam = teams_ll[0]
                    else:
                        hometeam = teams_ll[0]
                        guestteam = team_strong
                                
            except:
                pdb.set_trace()
            if len(match_details_ll) == 2:
                #pdb.set_trace()
                #hometeam = match_details_ll[0].a.next.text
                #guestteam = match_details_ll[0].a.next.next.text
    
                score_ll = match_details_ll[1].text.strip().split(' ')
                score_partial_ll = match.find_all('td')[-1].text.replace('(','').replace(')','').split(', ')

                
                if len(score_ll) == 2:
                    #pdb.set_trace()
                    if score_ll[1] == 'PEN.':
                        home_gols = 0
                        guest_gols = 0
                        for item in score_partial_ll[:-1]:
                            gols = item.split(':')
                            home_gols = home_gols + int(gols[0])
                            guest_gols = guest_gols + int(gols[1])
                        homescore, guestscore = [str(home_gols), str(guest_gols)]
                        note = 'PEN.'
                    elif score_ll[1] == 'ET':
                        homescore, guestscore = score_ll[0].split(':')
                        note = 'ET'

                elif len(score_ll) == 1:
                    if score_ll[0] == 'POSTP.':
                        homescore, guestscore = ['0','0']
                        note = 'POSTP.'
                    elif score_ll[0] == 'CAN.':
                            homescore, guestscore = ['0','0']
                            note = 'CAN.'
                    elif score_ll[0] == 'AWA.':
                            homescore, guestscore = ['0','0']
                            note = 'AWA.'
                    else:
                        try:
                            homescore, guestscore = score_ll[0].split(':')
                        except:
                            pdb.set_trace()
                        note = None
                else:
                    print('No result for ', league_name, ' ', hometeam, ' ', guestteam)
                    homescore, guestscore = ['0','0']
                    note = 'NO RES.'
                    continue
            else:
                #pdb.set_trace()
                homescore, guestscore = ['0','0']
                note = 'NO RES.'
            
        
            match_dict['WebSite'].append('BetExplorer')
            match_dict['LeagueName'].append(league_name)
            match_dict['HomeTeam'].append(hometeam.strip())
            match_dict['GuestTeam'].append(guestteam.strip())
            match_dict['HomeScore'].append(int(homescore.strip()))
            match_dict['GuestScore'].append(int(guestscore.strip()))
            match_dict['DayTime'].append(nowtime)
            match_dict['MatchTime'].append(matchtime)
            match_dict['MatchDay'].append(date.text.strip())
            match_dict['Note'].append(note)

    df_ = pd.DataFrame(match_dict)
    return  pd.concat([df, df_], ignore_index=True)
#####################
def get_betexplorer(df, service, options):
    url = "https://www.betexplorer.com/"

    driver = Firefox(service=service, options=options)
    driver.implicitly_wait(10)
    driver.get(url)

    #time to load the page
    time.sleep(3)
    #click on accept cookies
    button = driver.find_element(By.ID, "onetrust-accept-btn-handler")
    button.click()
    time.sleep(2)
    #scroll down the page
    #find footer
    elem = driver.find_element(By.CLASS_NAME, "footer__bottom")
    #scroll down
    elems = driver.find_elements(By.CSS_SELECTOR, "ul.leagues-list")
    items_len = len(elems)
    while True:
        driver.execute_script("arguments[0].scrollIntoView();", elem)
        time.sleep(1)
        elems = driver.find_elements(By.CSS_SELECTOR, "ul.leagues-list")
        if len(elems) == items_len:
            break
        else:
            items_len = len(elems)
    
    #pdb.set_trace()
    
    element_html= driver.find_element(By.XPATH,"//*[@id='nr-ko-all']").get_attribute('outerHTML')
    #quit the browser
    driver.quit()
    
    nowtime = dt.datetime.now()
    soup = BeautifulSoup(element_html, 'html.parser')
    ll = soup.find_all('ul', class_="leagues-list")
    #make the dictionary
    match_dict = make_macth_dict(df)


    for item_league in ll:
        ll_matches = item_league.find_all('li',class_="table-main__tournamentLiContent")
        for match in ll_matches:
            leaguename = item_league.find('p').text.strip()
                
            match_time = match.find('span', class_="matchDateStatus").text.strip()
            if ':' not in match_time:
                continue
            
            ll_odds = match.find_all('div',class_="table-main__odd")
            ll_odds[0] = ll_odds[0].text.strip()
            ll_odds[1] = ll_odds[1].text.strip()
            ll_odds[2] = ll_odds[2].text.strip()
            

            if len(ll_odds) == 3 and all([len(item)>3 for item in ll_odds]):

                match_dict['WebSite'].append('BetExplorer')
                match_dict['LeagueName'].append(leaguename)
                match_dict['DayTime'].append(nowtime)
                match_dict['MatchTime'].append(match_time)
                match_dict['MatchDay'].append(nowtime.strftime('%d.%m.%Y'))
                ll_teams = match.find_all('p')
                match_dict['HomeTeam'].append(ll_teams[0].text)
                match_dict['GuestTeam'].append(ll_teams[1].text)
                match_dict['odd1'].append(float(ll_odds[0]))
                match_dict['oddX'].append(float(ll_odds[1]))
                match_dict['odd2'].append(float(ll_odds[2]))

    df_ = pd.DataFrame(match_dict)
    return  pd.concat([df, df_])
#####################
def scrap_bwin(df, service, options):

    driver = Firefox(service=service, options=options)
    driver.implicitly_wait(10)
    url = "https://sports.bwin.it/it/sports/calcio-4/oggi"
    driver.get(url)
    time.sleep(7)
    nowtime = dt.datetime.now()
    
    

    buttons = driver.find_elements(By.CSS_SELECTOR, "span.ui-icon")
    buttons[1].click()
    time.sleep(2)
    button = driver.find_element(By.ID, "onetrust-accept-btn-handler")
    button.click()
    time.sleep(2)

    #find footer
    elem = driver.find_element(By.CSS_SELECTOR, "vn-clock")
    #scroll down
    elems = driver.find_elements(By.CSS_SELECTOR, "ms-event")
    items_len = len(elems)
    while True:
        driver.execute_script("arguments[0].scrollIntoView();", elem)
        time.sleep(1)
        elems = driver.find_elements(By.CSS_SELECTOR, "ms-event")
        if len(elems) == items_len:
            break
        else:
            items_len = len(elems)

    #pdb.set_trace()
    
    element_html= driver.find_element(By.CLASS_NAME,'grid-wrapper').get_attribute('outerHTML')
    driver.quit()
    match_dict = make_macth_dict(df)
    web_site = "bwin"
    
    soup = BeautifulSoup(element_html, 'html.parser')
    league_ll = soup.find_all('ms-event-group', class_='event-group')

    for league_item in league_ll:
        #pdb.set_trace()
        league_name = league_item.find('div', class_='title').text.replace('|','')
        if 'Combi+' in league_name.split(): #skip this
            continue

        match_ll = league_item.find_all('ms-event')
        
        for match_item in match_ll:
            match_time = match_item.find('ms-event-timer', class_='grid-event-timer').text
            
            match_time_ll = match_time.split()
            if 'Fra' == match_time_ll[0]: #the match starts in n minutes
                match_time = nowtime + dt.timedelta(minutes = int(match_time_ll[1]) + 1)
                match_time = match_time.strftime('%H:%M')
            elif 'T' in match_time_ll[0]: #the match has already started
                continue
            elif 'Inizio' in match_time_ll[0]: #the match is going to start
                continue
            elif 'Intervallo' in match_time_ll[0]: #the match has already started
                continue
            else:
                pass

            ll_teams = match_item.find_all('div', class_='participant')
            ll_odds = match_item.find_all('ms-option', class_='grid-option')
            #if the odds are missing, continue
            if len(ll_odds) == 0:
                continue
            
            #if one odd is missing, continue
            missing_odd = False
            if len(ll_odds)<3:
                continue
            for odd in ll_odds[:3]:
                if len(odd.text) == 0:
                    missing_odd = True
            if missing_odd:
                continue

    
            #the rest of the rows
            match_dict['WebSite'].append(web_site)
            match_dict['DayTime'].append(nowtime)
            match_dict['LeagueName'].append(league_name)
            match_dict['MatchTime'].append(match_time)
            match_dict['MatchDay'].append(nowtime.strftime('%d.%m.%Y'))
            match_dict['HomeTeam'].append(ll_teams[0].text.strip())
            match_dict['GuestTeam'].append(ll_teams[1].text.strip())
            try:
                match_dict['odd1'].append(float(ll_odds[0].text.strip()))
            except:
                pdb.set_trace()
            match_dict['oddX'].append(float(ll_odds[1].text.strip()))
            match_dict['odd2'].append(float(ll_odds[2].text.strip()))

    df_ = pd.DataFrame(match_dict)
    
    return  pd.concat([df, df_], ignore_index=True)
#####################
def scrap_eurobet(df, service, options):

    driver = Firefox(service=service, options=options)
    driver.implicitly_wait(10)
    url = "https://www.eurobet.it/it/scommesse/#!/calcio/?temporalFilter=TEMPORAL_FILTER_OGGI"
    driver.get(url)

    #ele = WebDriverWait(driver, 100).until(EC.presence_of_element_located(((By.CLASS_NAME,'footer'))))

    time.sleep(5)
    nowtime = dt.datetime.now()

    element_html= driver.find_element(By.CLASS_NAME,'baseAnimation').get_attribute('outerHTML')
    driver.quit()

    soup = BeautifulSoup(element_html, 'html.parser')
    ele = soup.find(class_='anti-row')
    
    match_dict = make_macth_dict(df)

    web_site = "EuroBet"
    league_name = None

    ll = ele.contents
    #pdb.set_trace()
    for item in ll:
        #check for empty rows
        if item.name == None:
            continue
    
        if item.find(class_='breadcrumb-meeting') != None:
            league_name = item.find('div', class_="breadcrumb-meeting").text
            
        ll_odds = item.find(class_="group-quote-new").find_all('a')
        if len(ll_odds) != 3: #in case one of the odds has a lock on it
            continue
        
        #the rest of the rows
        match_dict['WebSite'].append(web_site)
        match_dict['DayTime'].append(nowtime)
        match_dict['LeagueName'].append(league_name)
        match_dict['MatchTime'].append(item.find(class_="time-box").text)
        match_dict['MatchDay'].append(nowtime.strftime('%d.%m.%Y'))
        ll_teams = item.find(class_="event-players").text.split(' - ')
        match_dict['HomeTeam'].append(ll_teams[0].strip())
        match_dict['GuestTeam'].append(ll_teams[1].strip())
        match_dict['odd1'].append(float(ll_odds[0].text.strip()))
        match_dict['oddX'].append(float(ll_odds[1].text.strip()))
        match_dict['odd2'].append(float(ll_odds[2].text.strip()))

    #pdb.set_trace()

    df_ = pd.DataFrame(match_dict)
    
    return  pd.concat([df, df_], ignore_index=True)
#######################
def scrap_sisal(df, service, options):


    driver = Firefox(service=service, options=options)
    url = "https://www.sisal.it/scommesse-matchpoint/palinsesto/calcio?day=today"
    driver.get(url)
    nowtime = dt.datetime.now()
    web_site = 'sisal'

    ele = WebDriverWait(driver, 100).until(EC.presence_of_element_located(((By.TAG_NAME,'footer'))))
    time.sleep(10)
    #pdb.set_trace()
    #click on accept cookies
    buttons_ll = driver.find_elements(By.ID,'onetrust-accept-btn-handler')   
    if len(buttons_ll) != 0:
        button.click()
    
    #button.click()
    
    #click on the league bar to show the match of every league 
    container_ll = driver.find_elements(By.CSS_SELECTOR, "i.icon-Arrow-Down")
    for button in container_ll:
        button.click()
        #time.sleep(1)

    element_html = driver.find_element(By.CLASS_NAME,'sportsbook_rootWrapper__mknyB').get_attribute('outerHTML')
    
    soup = BeautifulSoup(element_html, 'html.parser')
    driver.quit()

    ele = soup.find('div', class_="justify-content-between")
    match_dict = make_macth_dict(df)
    

    
    for item in ele.next_siblings:
        league_name = item.find(class_="competitionHeader_labelCompetitionHeader__9Qeoz").text
        
        ll_rows = item.find_all(class_="grid_mg-row-wrapper__usTh4")
        
        for row in ll_rows:
            ll_cols = row.find_all(class_='mg-cell')
            #pdb.set_trace()
            
            ll_teams = []
            for i in ll_cols[0].find(class_='regulator_container__SDVHD').strings:
                ll_teams.append(i)
            
            ll_odds = ll_cols[1].find_all(class_='selectionButton_selectionPrice__B-6jq')
            if len(ll_odds) != 3: #in case one of the odds has a lock on it
                continue
    
            #the rest of the rows
            match_dict['WebSite'].append(web_site)
            match_dict['DayTime'].append(nowtime)
            match_dict['LeagueName'].append(league_name)
            match_dict['MatchTime'].append(row.find(class_='dateTimeBox_regulatorTime__ilXmi').text[5:])
            match_dict['MatchDay'].append(nowtime.strftime('%d.%m.%Y'))
            match_dict['HomeTeam'].append(ll_teams[0].strip())
            match_dict['GuestTeam'].append(ll_teams[1].strip())
            match_dict['odd1'].append(float(ll_odds[0].text.strip()))
            match_dict['oddX'].append(float(ll_odds[1].text.strip()))
            match_dict['odd2'].append(float(ll_odds[2].text.strip()))
             
    #pdb.set_trace()
    df_ = pd.DataFrame(match_dict)
    
    return  pd.concat([df, df_], ignore_index=True)
#######################
def scrap_888sport(df, service, options):

    weekday_dict = {'Mon': 'lun', 'Tue': 'mar', 'Wed': 'mer', 'Thu': 'gio', 'Fri': 'ven', 'Sat': 'sab', 'Sun': 'dom'}

    driver = Firefox(service=service, options=options)
    url = "https://www.888sport.it/calcio/#/filter/football"
    driver.get(url)
    nowtime = dt.datetime.now()
    web_site = '888sport'

    #ele = WebDriverWait(driver, 100).until(EC.presence_of_element_located(((By.XPATH,"//div[@id='uc-cms-container']"))))
    time.sleep(5)
    button = driver.find_element(By.ID, "onetrust-accept-btn-handler")
    button.click()
    time.sleep(3)
    
    container_ll = driver.find_elements(By.CSS_SELECTOR, "div.KambiBC-mod-event-group-container")
    
    #pdb.set_trace()
    for button in container_ll[1:]:
        tt =  button.get_attribute('outerHTML')
        soup = BeautifulSoup(tt, 'html.parser')
        if soup.find('div', class_="KambiBC-expanded") is None:
            button.click()
            #time.sleep(1) 
        else:
            continue
        
    #pdb.set_trace()
    container_ll = driver.find_elements(By.CSS_SELECTOR, "div.KambiBC-betty-collapsible-container")
    for button in container_ll:
        tt =  button.get_attribute('outerHTML')
        soup = BeautifulSoup(tt, 'html.parser')
        if 'totali' not in soup.text.split():
            button.click()
            #time.sleep(1)
         
    element_html = driver.find_element(By.CLASS_NAME,'KambiBC-event-groups-list').get_attribute('outerHTML')
    soup = BeautifulSoup(element_html, 'html.parser')
    match_dict = make_macth_dict(df)
    driver.quit()
    nations_ll = soup.find_all('div', class_="KambiBC-mod-event-group-container")
    
    
    for nation in nations_ll[1:]:
        land_name = nation.header.div.text.strip()
        #print(land_name)
        #pdb.set_trace()
        nation_container = nation.find('div',class_="KambiBC-mod-event-group-event-container")

        try:
            titles_ll = nation_container.find_all(class_="KambiBC-betoffer-labels--with-title")
        except:
            print('nation_container')
            pdb.set_trace()
        league_ll = nation_container.find_all(class_="KambiBC-list-view__event-list")
        #
        try:
            assert len(titles_ll) == len(league_ll), 'the two list have different lengths'
        except:
            print(land_name, ': the two list have different lengths')
            #pdb.set_trace()
            continue
        
        for i,item in enumerate(league_ll):
            league_name = titles_ll[i].div.header.div.text.strip()
            matches_ll = item.find_all('li')
            
            for match in matches_ll:
                hour = match.span.next_sibling.text.strip()
                day = match.span.text.strip()
                weekday_today = weekday_dict[nowtime.strftime('%a')]
                if day != weekday_today:
                    continue
                
                ll_teams  = []
                for name in match.find('div',class_="KambiBC-event-item__details").strings:
                    ll_teams.append(name)
                ll_odds = []
                for odd in match.find('div',class_="KambiBC-bet-offers-list__column--num-3").strings:
                    ll_odds.append(odd)
            
                #sometimes this list has lenght=0, so check it and, in case, skip this match
                if len(ll_odds) < 3:
                    continue
                
                match_dict['WebSite'].append(web_site)
                match_dict['LeagueName'].append(land_name + ' ' + league_name)
                match_dict['MatchTime'].append(hour)
                match_dict['MatchDay'].append(nowtime.strftime('%d.%m.%Y'))
                match_dict['HomeTeam'].append(ll_teams[0].strip())
                match_dict['GuestTeam'].append(ll_teams[1].strip())
                match_dict['odd1'].append(float(ll_odds[0].strip()))
                match_dict['oddX'].append(float(ll_odds[1].strip()))
                match_dict['odd2'].append(float(ll_odds[2].strip()))
                match_dict['DayTime'].append(nowtime)
    
    df_ = pd.DataFrame(match_dict)
    
    return  pd.concat([df, df_], ignore_index=True)


#######################
def join_games_lists(df1, df2):
    idx_ll = []
    #pdb.set_trace()
    for idx1, row1 in df1.iterrows():
        found_bool = False
        ratios_df = pd.DataFrame()
        match_name_bet = row1.LeagueName + ' ' + row1.HomeTeam + ' ' + row1.GuestTeam

        for idx2, row2 in df2.iterrows():
            match_name_mean = row2.LeagueName + ' ' + row2.HomeTeam + ' ' + row2.GuestTeam

            #r_home = SequenceMatcher(None, row1.HomeTeam,row2.HomeTeam).ratio()
            #r_guest = SequenceMatcher(None, row1.GuestTeam,row2.GuestTeam).ratio()
            #r_league = SequenceMatcher(None, row1.LeagueName,row2.LeagueName).ratio()
            #pdb.set_trace()
            r_home = fuzz.token_sort_ratio(row1.HomeTeam,row2.HomeTeam)
            r_guest = fuzz.token_sort_ratio(row1.GuestTeam,row2.GuestTeam)
            r_league = fuzz.token_sort_ratio(row1.LeagueName,row2.LeagueName)
            r_matchtime = fuzz.token_sort_ratio(row1.MatchTime,row2.MatchTime)
        
            
            min_match_bool = (r_home > 50) and (r_guest > 50) and (r_league > 50) and (r_matchtime>80)
            r_sum = r_home + r_guest + r_league
            
            ds = pd.Series([row2.HomeTeam, row2.GuestTeam, r_sum,min_match_bool ,idx1, idx2], index=['home','guest','r_sum', 'bool','idx1','idx2'])
            ratios_df = ratios_df.append(ds, ignore_index=True)
            
            #if idx1 == 123 and idx2 == 55:
            #    pdb.set_trace()
            #print(match_name_bet, ' ', match_name_mean, ' ', r_sum, min_match_bool, r_home, r_guest, r_league, r_matchtime)
            #pdb.set_trace()
            
        ratios_df.sort_values(by='r_sum', ascending=False, inplace=True)
        #print(ratios_df.iloc[0])

        #pdb.set_trace()
        if ratios_df.iloc[0].bool and ratios_df.iloc[0].r_sum.astype(int) > 150:
            #pdb.set_trace()
            idx_ll.append((ratios_df.iloc[0].idx1.astype(int), ratios_df.iloc[0].idx2.astype(int), ratios_df.iloc[0].r_sum.astype(int)))
        
        if found_bool == False:
            print('missing bet', match_name_bet, ' idx=', idx1)
    
    return idx_ll
#################
def crossmatch_odds(idx_ll, df_odds, df_odds_mean):
    cols_bets = ['WebSite','LeagueName','MatchDay', 'MatchTime', 'HomeTeam','GuestTeam','odd1','oddX','odd2','BetOn', 'DeltaProb','DayTime','r_sum','idx1','idx2']
    df_bets = pd.DataFrame(columns=cols_bets)
    bets_dict = make_macth_dict(df_bets)

    for (idx_odds, idx_mean, r_sum) in idx_ll:
        #pdb.set_trace()
        row_mean = df_odds_mean.loc[idx_mean]
        row_odds = df_odds.loc[idx_odds]
        odds_bool = [False, False, False]
        

            
        prob1_diff = round(1./row_mean.odd1_corr - 1./row_odds.odd1, 3)
        probX_diff = round(1./row_mean.oddX_corr - 1./row_odds.oddX, 3)
        prob2_diff = round(1./row_mean.odd2_corr - 1./row_odds.odd2, 3)
        probs_diff_ll = [prob1_diff, probX_diff, prob2_diff]
        probs_diff_bool = [(True if item>0.000 else False)  for item in probs_diff_ll]
        
        #pdb.set_trace()
        #odds_names = ['odd1_diff','oddX_diff','odd2_diff']
        odds_diff_array = np.where(probs_diff_bool, probs_diff_ll, [None, None, None])
        
        #if r_sum<170:
        #    pdb.set_trace()
        
        for i, bet in enumerate(probs_diff_bool):
            if bet:

                if i==0:
                    bets_dict['BetOn'].append('1')
                    bets_dict['DeltaProb'].append(round(odds_diff_array[i], 3))
                elif i==1:
                    bets_dict['BetOn'].append('X')
                    bets_dict['DeltaProb'].append(round(odds_diff_array[i], 3))
                elif i==2:
                    bets_dict['BetOn'].append('2')
                    bets_dict['DeltaProb'].append(round(odds_diff_array[i], 3))
                #
                bets_dict['WebSite'].append(row_odds.WebSite)
                bets_dict['LeagueName'].append(row_mean.LeagueName)
                bets_dict['MatchDay'].append(row_mean.MatchDay)
                bets_dict['MatchTime'].append(row_mean.MatchTime)
                bets_dict['HomeTeam'].append(row_mean.HomeTeam)
                bets_dict['GuestTeam'].append(row_mean.GuestTeam)
                bets_dict['odd1'].append(row_odds.odd1)
                bets_dict['oddX'].append(row_odds.oddX)
                bets_dict['odd2'].append(row_odds.odd2)
                bets_dict['DayTime'].append(row_mean.DayTime)
                bets_dict['r_sum'].append(r_sum)
                bets_dict['idx1'].append(idx_odds)
                bets_dict['idx2'].append(idx_mean)
            else:
                continue
    #pdb.set_trace()
    return pd.DataFrame(bets_dict)
#####################################
def compute_1X2(row_res,row_bets):
    #pdb.set_trace()
    invalid_res = ['POSTP.', 'CAN.','AWA.']
    res_bool = np.array([False,False,False])
    diff = row_res.HomeScore - row_res.GuestScore
    if diff>0:
        res = '1'
        res_bool[0] = True
    elif diff == 0:
        res = 'X'
        res_bool[1] = True
    else:
        res = '2'
        res_bool[2] = True
    
    if row_bets.BetOn == '1':
        bets_bool = [True, False, False]
    elif row_bets.BetOn == 'X':
        bets_bool = [False, True, False]
    elif row_bets.BetOn == '2':
        bets_bool = [False, False, True]
        
    odds_array = row_bets[['odd1','oddX','odd2']].values
    try:
        earn_array = np.where(bets_bool & res_bool, odds_array, 0)
    except:
        pdb.set_trace()
    earn = round(np.sum(earn_array - 1., where=bets_bool, initial=0),2)
    #if the match was postponed or canceled
    if row_res.Note in invalid_res:
        earn = 0
    
    return res, earn
#####################################
def crossmatch_bets_results(idx_ll, df_bets, df_results):
    #pdb.set_trace()
    cols_res = ['WebSite','LeagueName','HomeTeam','GuestTeam','odd1','oddX','odd2','BetOn','DeltaProb','Result','Profit','DayTime','Note']
    df_bets_results = pd.DataFrame(columns=cols_res)
    bets_res = make_macth_dict(df_bets_results)
    bets_dict = {0:'BetOn1', 1:'BetOnX', 2:'BetOn2'}    

    for (idx_bets, idx_res) in idx_ll:
        #pdb.set_trace()
        row_bets = df_bets.loc[idx_bets]
        row_res = df_results.loc[idx_res]
        
        bets_res['WebSite'].append(row_bets.WebSite)
        bets_res['LeagueName'].append(row_bets.LeagueName)
        bets_res['HomeTeam'].append(row_bets.HomeTeam)
        bets_res['GuestTeam'].append(row_bets.GuestTeam)
        bets_res['odd1'].append(row_bets.odd1)
        bets_res['oddX'].append(row_bets.oddX)
        bets_res['odd2'].append(row_bets.odd2)
        bets_res['BetOn'].append(row_bets.BetOn)
        bets_res['DeltaProb'].append(row_bets.DeltaProb)
        bets_res['DayTime'].append(row_bets.DayTime)
        res_1X2, earn = compute_1X2(row_res,row_bets)
        bets_res['Result'].append(res_1X2)
        bets_res['Profit'].append(earn)
        bets_res['Note'].append(row_res.Note)

    return pd.DataFrame(bets_res)
############################
'''

def scrap_sisal_serieA(df, service, options):


    driver = Firefox(service=service, options=options)
    url = "https://www.sisal.it/scommesse-matchpoint/quote/calcio/serie-a"
    driver.get(url)
    nowtime = dt.datetime.now()

    element_html= driver.find_element(By.XPATH,"//*[@id='fr-competition-detail-1-209']").get_attribute('outerHTML')
    driver.quit()

    soup = BeautifulSoup(element_html, 'html.parser')
    match_dict = make_macth_dict(df)
    list_rows = soup.find_all(class_="grid_mg-row__bvy-G")



    for row in list_rows:
        match_time_str = row.find_all(class_="dateTimeBox_regulatorTime__ilXmi")[0].text.split('br')[0]
        #pdb.set_trace()
        match_time = match_time_str[0:5] + ' ' + match_time_str[5:]
        home_team = row.find_all(class_="regulator_team__0DTi8")[0].text
        guest_team = row.find_all(class_="regulator_team__0DTi8")[1].text
        odd1 = float(row.find_all(class_="selectionButton_selectionPrice__B-6jq")[0].text)
        oddX = float(row.find_all(class_="selectionButton_selectionPrice__B-6jq")[1].text)
        odd2 = float(row.find_all(class_="selectionButton_selectionPrice__B-6jq")[2].text)
        match_dict['WebSite'].append('sisal') 
        match_dict['DayTime'].append(nowtime)
        match_dict['MatchTime'].append(match_time)
        match_dict['HomeTeam'].append(home_team)
        match_dict['GuestTeam'].append(guest_team)
        match_dict['odd1'].append(odd1)
        match_dict['oddX'].append(oddX)
        match_dict['odd2'].append(odd2)
        
    df_ = pd.DataFrame(match_dict)
    return  pd.concat([df, df_])
######################
#####################

def get_betexplorer_serieA(url, df):

    #get the soup
    soup, time = get_soup(url)

    match_dict = dict.fromkeys(list(df.columns))
    for key in match_dict.keys():
        match_dict[key] = []

    soup_list = soup.find_all('table')

    list_match = soup_list[0].find_all('tr')

    for item in list_match[1:]:
        match_tr = item.find_all('a')[0]
        home_team = match_tr.find_all('span')[0].text
        guest_team = match_tr.find_all('span')[1].text
    
        odd1 = item.find_all('td', class_='table-main__odds')[0].find_all('button')[0]['data-odd']
        oddX = item.find_all('td', class_='table-main__odds')[1].find_all('button')[0]['data-odd']
        odd2 = item.find_all('td', class_='table-main__odds')[2].find_all('button')[0]['data-odd']

        match_time_list = item.find_all('td', class_='h-text-right')[0].text.split()
        time_hour_list = match_time_list[1].split(':')
        match_time_ini = dt.datetime(time.year,time.month,time.day, int(time_hour_list[0]),int(time_hour_list[1]))

        if match_time_list[0] == 'Today':
            match_time = match_time_ini
        elif match_time_list[0] == 'Tomorrow':
            match_time = match_time_ini + dt.timedelta(1)
        else:
            match_day = int(match_time_list[0].split('.')[0])
            match_month = int(match_time_list[0].split('.')[1])
            match_time = dt.datetime(time.year,match_month, match_day, int(time_hour_list[0]),int(time_hour_list[1]))
            
        match_dict['WebSite'] = 'betexplorer'
        match_dict['DayTime'].append(time) 
        match_dict['MatchTime'].append(match_time) 
        match_dict['LeagueName'] = 'SerieA'
        match_dict['HomeTeam'].append(home_team)
        match_dict['GuestTeam'].append(guest_team)
        match_dict['odd1'].append(float(odd1))
        match_dict['oddX'].append(float(oddX))
        match_dict['odd2'].append(float(odd2))

    df_ = pd.DataFrame(match_dict)
    
    return  pd.concat([df, df_])
'''



