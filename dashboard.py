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

#Create app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
colors = {'background': 'black','text': 'white'}

curr_dir = os.getcwd()
bets_placed_name = '/bet_placed_prova.csv'
bet2place_name = '/bet_to_place.csv'
bets_placed_path = curr_dir + bets_placed_name
bets2place_path = curr_dir + bet2place_name

df_placed =  pd.read_csv(bets_placed_path, index_col=False)
df_2place =  pd.read_csv(bets2place_path, index_col=False)
df_2place.drop(columns=['DayTime'], inplace=True)

app.layout = html.Div(style={'backgroundColor': colors['background']},
    children=[html.Div(
        children=[html.H1('Soccer betting with the KFK method', 
                                style={'textAlign': 'center', 'color': colors['text'],
                                'font-size': 26})]),
    html.Br(),
    dcc.Dropdown(['>0.00', '>0.01', '>0.02'], value='>0.01', id='limit', clearable=False,
        style={'backgroundColor': colors['background']}),
    dcc.Graph(figure={}, id='graph', style={'backgroundColor': colors['background']}),
    dash.dash_table.DataTable(data=df_2place.to_dict('records'), page_size=5)
    ])

    # Add controls to build the interaction
@app.callback(
    Output(component_id='graph', component_property='figure'),
    Input(component_id='limit', component_property='value')
    )

def update_graph(val_chosen):
    if val_chosen == '>0.00':
        df_ = df_placed[df_placed.DeltaProb>0.00]
    elif val_chosen == '>0.01':
        df_ = df_placed[df_placed.DeltaProb>0.01]
    elif val_chosen == '>0.02':
        df_ = df_placed[df_placed.DeltaProb>0.02] 
    
    df_['Profit_cumsum'] = df_.Profit.cumsum()
    df_.reset_index(inplace=True)
    fig = px.line(df_, x='index', y='Profit_cumsum')
    fig.update_layout(plot_bgcolor='black', paper_bgcolor='black')
    fig.update_xaxes(linecolor='black', gridcolor='lightgrey')
    fig.update_yaxes(linecolor='black', gridcolor='lightgrey')
    return fig

# Run the app
if __name__ == '__main__':
    app.run(debug=True)