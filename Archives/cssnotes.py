
import webbrowser

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash import dcc, html, Input, Output, State, callback
from dash.exceptions import PreventUpdate


app = dash.Dash(__name__, external_stylesheets = [dbc.themes.BOOTSTRAP])

app.title = "My First Dash App"

app.layout = html.Div(
    [
        html.Div(
            'Hello World',
            style={'border': '2px solid green'},
            className='w-100 text-center'
        )
    ]
), html.P('My first html.P()'),html.P('My second html.P()')



if __name__ == '__main__':
    webbrowser.open('http://127.0.0.1:8050', autoraise=True)
    app.run()
