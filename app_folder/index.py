import webbrowser

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from apps import home, commonmodules

from apps.movies import movie_management_profile_cp, movie_management


# Importing your app variable from app.py so we can use it
from app import app

app.layout = html.Div(
    [
        # Location Variable -- contains details about the url
        dcc.Location(id='url', refresh=True),
        commonmodules.navbar,

        # Page Content -- Div that contains page layout
        html.Div(id='page_content', className='m-2 p-2'),
    ]
)

@app.callback(
    [
        Output('page_content', 'children')
    ],
    [
        Input('url', 'pathname')
    ]
)

def displaypage (pathname):
    
    # This code block extracts the id of the triggered input
    ctx = dash.callback_context
    if ctx.triggered:
        eventid = ctx.triggered[0]['prop_id'].split('.')[0]   
    else:
        raise PreventUpdate

        
    # This code block executes action based on the value of eventid
    if eventid == 'url':
        if pathname == '/' or pathname == '/home':
            returnlayout = home.layout

        elif pathname == '/movies':
            returnlayout = 'moviepage'

        elif pathname == '/movies/movie_management':
            returnlayout = movie_management.layout

        elif pathname == '/movies/movie_management_profile':
            returnlayout = movie_management_profile_cp.layout

        else:
            returnlayout = 'error404'
    
    else: 
        raise PreventUpdate
    
    return [returnlayout]

if __name__ == '__main__':
    webbrowser.open('http://127.0.0.1:8050/', new=0, autoraise=True)
    app.run(debug=False)

#comment
