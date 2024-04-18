#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  8 15:44:25 2024

@author: corrado
"""

from dash import Dash, html

import os
import pandas as pd
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from dash import no_update
import datetime as dt

nowtime = dt.datetime.now()
today_date = nowtime.strftime('%d.%m.%Y')

#Create app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
colors = {'background': 'black','text': 'white'}

curr_dir = os.getcwd()
bets_placed_name = '/bet_placed_profit.csv'
bet2place_name = '/bet_to_place.csv'
bets_placed_path = curr_dir + bets_placed_name
bets2place_path = curr_dir + bet2place_name

df_placed =  pd.read_csv(bets_placed_path, index_col=False)
df_2place =  pd.read_csv(bets2place_path, index_col=False)
df_2place.drop(columns=['DayTime'], inplace=True)

#table to show
bool_today = df_2place.MatchDay == today_date
df_2show = df_2place.drop(columns=['MatchDay'])[bool_today]
df_2show['DeltaProb'] = df_2show.DeltaProb.apply(lambda x: str(round(x,3)))
df_2show.reset_index(inplace=True, drop=True)

#%%
#components
title = dcc.Markdown(children='# Betting with the KFK method')
graph = dcc.Graph(figure={})
value_widget = dcc.RadioItems(options=['>0.000', '>0.005', '>0.010', '>0.015'], value='>0.000')
#value_widget = dcc.Slider(0,0.05, 0.01, value=0.0)

item = html.Div([
         dbc.Row([
             #html.H1('Betting with the KFK Method', 
             #                   style={'textAlign': 'center', 'color': 'white',
             #                   'font-size': 36})], align='center'),
         dcc.Markdown('# Betting with the KFK Method')], justify='center'),
         html.Br(),
         dbc.Row([
             dbc.Col(dcc.Markdown('DeltaProb'), width=1),
             dbc.Col(dcc.Markdown('### Cumulative Earning per Bet'), width=5),
             dbc.Col(dcc.Markdown("### Today's  match to bet on"), width=6)
             ]),
         html.Br(),
         dbc.Row([
            dbc.Col(value_widget, width=1, align='start'),
            dbc.Col(graph, width=5, align='center'),
            dbc.Col(dbc.Table.from_dataframe(df_2show, striped=True, bordered=True, 
                                             hover=True, size='sm')
                    , width=6,align='start')
            
         ], align='start', justify='start')
       ])#, className="pad-row")

#customize container
app.layout = dbc.Container([item], fluid=True)

    # Add controls to build the interaction
@app.callback(
    Output(component_id=graph, component_property='figure'),
    Input(component_id=value_widget, component_property='value')
    )

def update_graph(val_chosen):
    if val_chosen == '>0.000':
        df_ = df_placed[df_placed.DeltaProb>0.00].reset_index(drop=True).copy()
    elif val_chosen == '>0.005':
        df_ = df_placed[df_placed.DeltaProb>0.005].reset_index(drop=True).copy()
    elif val_chosen == '>0.010':
        df_ = df_placed[df_placed.DeltaProb>0.010].reset_index(drop=True).copy()
    elif val_chosen == '>0.015':
        df_ = df_placed[df_placed.DeltaProb>0.015].reset_index(drop=True).copy()
    
    df_['Cumulative Earnings'] = df_.Profit.cumsum()
    df_.reset_index(inplace=True)
    df_.rename(columns={'index':'# Bet'}, inplace=True)
    fig = px.line(df_, x='# Bet', y='Cumulative Earnings')
    fig.update_layout(plot_bgcolor='black', paper_bgcolor='black')
    fig.update_xaxes(linecolor='black', gridcolor='lightgrey')
    fig.update_yaxes(linecolor='black', gridcolor='lightgrey')
    return fig

# Run the app
if __name__ == '__main__':
    app.run(debug=True)