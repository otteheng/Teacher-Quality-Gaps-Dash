# Dependencies for project
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_colorscales
import plotly.graph_objs as go
import plotly.plotly as py
import pandas as pd
import numpy as np
from dash.dependencies import Input, Output, State
import flask
import os
from random import randint
import requests
import json

# Setup the app
# Make sure not to change this file name or the variable names below,
# the template is configured to execute 'server' on 'app.py'
server = flask.Flask(__name__)
server.secret_key = os.environ.get('secret_key', str(randint(0, 1000000)))
app = dash.Dash(__name__, server=server)

app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})

DEFAULT_COLORSCALE = ["#2a4858", "#265465", "#1e6172", "#106e7c", "#007b84", \
	"#00898a", "#00968e", "#19a390", "#31b08f", "#4abd8c", "#64c988"]

DEFAULT_OPACITY = 0.8

mapbox_access_token = 'pk.eyJ1Ijoib3R0ZWhlbmciLCJhIjoiY2plaXltZW1pMHE4YjJxbmw1ZGgxbmJqdiJ9.wqmpkvPainkE7w-Wy-4tlA'

washbins = pd.read_csv('https://raw.githubusercontent.com/otteheng/Teacher-Quality-Gaps-Dash/master/Washington-Bins.csv')

YEARS = sorted(washbins['survyear'].unique().tolist())
TCH_QUALITY = ['experience_gap', 'novice_gap','westb_average_gap', 'westb_quartile_gap',
       'vam_average_gap', 'vam_quartile_gap']
STU_DISADV = ['experience_gap_frl','novice_gap_frl',
       'FRL_westb_average_gap', 'FRL_westb_quartile_gap','vam_quartile_gap_frl']
STATE = ['Washington', 'North Carolina']
BINS = list(washbins[(washbins.survyear == 1988) & (washbins.variable == 'experience_gap')].outcome_bins.unique())
BINS = [str(i) for i in BINS]

DEFAULT_DF = washbins[(washbins.survyear == 1988) & (washbins.variable == 'experience_gap')]

# Organize where items will be on the page
app.layout = html.Div([
    html.H3(
        children='Teacher Quality Gaps',
        style={'textAlign': 'center', 'fontFamily': 'Georgia'}
    ),

    html.Div([
        html.Div([
            html.Div([html.P('Measure of Teacher Quality', id='tch-quality-title')],
                     style={'textAlign': 'center', 'fontFamily': 'Georgia'}),
            dcc.Dropdown(
                id='tch-quality-dropdown',
                options=[{'label': i, 'value': i} for i in TCH_QUALITY],
                value='experience_gap'
            )
        ],
            style={'width': '30%', 'display': 'inline-block', 'fontFamily': 'Georgia', 'float': 'left'}),

        html.Div([
            html.Div([html.P('Measures of Student Disadvantage', id='stu-disadv-title')],
                     style={'textAlign': 'center', 'fontFamily': 'Georgia'}),
            dcc.Dropdown(
                id='stu-disadv-dropdown',
                options=[{'label': i, 'value': i} for i in STU_DISADV],
                value='',
            )
        ],
            style={'width': '30%', 'display': 'inline-block', 'fontFamily': 'Georgia', 'marginLeft': '80',
                   'marginRight': '10'}),

        html.Div([
            html.Div([html.P('States', id='state-title')],
                     style={'textAlign': 'center', 'fontFamily': 'Georgia'}),
            dcc.Dropdown(
                id='state-dropdown',
                options=[{'label': i, 'value': i} for i in STATE],
                value='Washington',
            )
        ],
            style={'width': '30%', 'display': 'inline-block', 'fontFamily': 'Georgia', 'float': 'right'})
    ]),
    html.Div([
        dash_colorscales.DashColorscales(
            id='colorscale-picker',
            colorscale=DEFAULT_COLORSCALE,
            nSwatches=len(BINS),
            fixSwatches=True
        )
    ], style={'display': 'inline-block', 'marginLeft': '10', 'float': 'left', 'fontFamily': 'Georgia'}),

    html.Div([
        dcc.Checklist(
            options=[{'label': 'Hide legend', 'value': 'hide_legend'}],
            values=[],
            labelStyle={'display': 'inline-block'},
            id='hide-map-legend',
        )
    ], style={'display': 'inline-block', 'fontFamily': 'Georgia', 'float': 'left', 'marginLeft': '5'}),

    html.Br(),

    html.Center('Heatmap of Measures of Teacher Quality in Year {0}'.format(min(YEARS)),
                id='heatmap-title',
                style={'fontWeight': 600, 'fontFamily': 'Georgia'}
                ),
    dcc.Graph(
        id='state-choropleth',
        figure=dict(
            data=dict(
                lat=DEFAULT_DF['latitude'],
                lon=DEFAULT_DF['longitude'],
                text=DEFAULT_DF['hover'],
                type='scattermapbox'
            ),
            layout=dict(
                mapbox=dict(
                    layers=[],
                    accesstoken=mapbox_access_token,
                    style='light',
                    center=dict(
                        lat=47.5,
                        lon=-120,
                    ),
                    pitch=0,
                    zoom=5.9
                )
            )
        )
    ),

    html.Div([
        dcc.Slider(
            id='years-slider',
            min=min(YEARS),
            max=max(YEARS),
            value=min(YEARS),
            marks={str(year): str(year) for year in YEARS},
        )
    ],
        style={'fontFamily': 'Georgia', 'width': '80%', 'marginLeft': '100', 'marginRight': '100'})
])


@app.callback(
    Output('state-choropleth', 'figure'),
    [Input('years-slider', 'value'),
     Input('colorscale-picker', 'colorscale'),
     Input('tch-quality-dropdown', 'value'),
     Input('hide-map-legend', 'values')],
    [State('state-choropleth', 'figure')])
def display_map(year, colorscale, tch_quality_dropdown, hide_map_legend, figure):
    BINS = list(
        washbins[(washbins.survyear == year) & (washbins.variable == str(tch_quality_dropdown))].outcome_bins.unique())
    BINS = [str(i) for i in BINS]

    # Reorder ranges in BINS to be from highest to lowest
    pos = []
    neg = []
    for i in BINS:
        if i[0] == '-':
            neg.append(i)
        elif i[0] != '-' and i != 'nan':
            pos.append(i)
    pos.sort(reverse=True)
    neg.sort()
    bins = []
    for i in pos:
        bins.append(i)
    for i in neg:
        bins.append(i)
    cm = dict(zip(bins, colorscale))

    df = washbins[(washbins.survyear == year) & (washbins.variable == str(tch_quality_dropdown))]
    data = [dict(
        lat=df['latitude'],
        lon=df['longitude'],
        text=df['hover'],
        type='scattermapbox',
        hoverinfo='text',
        marker=dict(size=3),
        opacity=0
    )]

    annotations = [dict(
        showarrow=False,
        align='right',
        text='<b>{0} per<br>School District per year</b>'.format(str(tch_quality_dropdown)),
        x=0.95,
        y=0.95,
    )]

    for i, bin in enumerate(bins):
        color = cm[bin]
        annotations.append(
            dict(
                arrowcolor=color,
                text=bin,
                x=0.95,
                y=0.85 - (i / 20),
                ax=-60,
                ay=0,
                arrowwidth=5,
                arrowhead=0,
                bgcolor='#EFEFEE'
            )
        )

    if 'hide_legend' in hide_map_legend:
        annotations = []

    if 'layout' in figure:
        lat = figure['layout']['mapbox']['center']['lat']
        lon = figure['layout']['mapbox']['center']['lon']
        zoom = figure['layout']['mapbox']['zoom']
    else:
        lat = 47.5,
        lon = -120,
        zoom = 5.9

    layout = dict(
        mapbox=dict(
            layers=[],
            accesstoken=mapbox_access_token,
            style='light',
            center=dict(lat=lat, lon=lon),
            zoom=zoom
        ),
        hovermode='closest',
        margin=dict(r=0, l=0, t=0, b=0),
        annotations=annotations,
        dragmode='lasso'
    )
    #     path = r'H:\CALDER\CALDER Data Visualizations\Data\Teacher Quality Gap - Washington\Geo'
    base_url = 'https://raw.githubusercontent.com/otteheng/Teacher-Quality-Gaps-Dash/master/'
    state = 'washington'
    for bin in bins:
        # Files off of Github
        obj = requests.get(base_url + str(year) + '/' + state + '_' + str(tch_quality_dropdown) + '_'
                           + bin + '.geojson?_sm_au_=iMVkWD4ks1RjnJZn')
        geo_layer = dict(
            sourcetype='geojson',
            source=obj.json(),
            type='fill',
            color=cm[bin],
            opacity=0.6
        )
        # Local Files
        #         obj = path + '\\' + str(year) + '\\' + 'washington_' + str(tch_quality_dropdown) + '_' +bin + '.geojson'
        #         with open(obj) as f:
        #             geo = json.load(f)
        #         geo_layer = dict(
        #             sourcetype = 'geojson',
        #             source = geo,
        #             type = 'fill',
        #             color = cm[bin],
        #             opacity = 0.6
        #         )
        layout['mapbox']['layers'].append(geo_layer)

    fig = dict(data=data, layout=layout)
    return fig


@app.callback(
    Output('heatmap-title', 'children'),
    [Input('years-slider', 'value')])
def update_map_title(year):
    return 'Heatmap of Measures of Teacher Quality in Year {0}'.format(str(year))

# Run the Dash app
if __name__ == '__main__':
    app.server.run(debug=True, threaded=True)