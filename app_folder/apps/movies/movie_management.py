import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash import Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate

from app import app
from apps.dbconnect import getDataFromDB

layout = html.Div(
    [
        html.H2('Movies'), # Page Header
        html.Hr(),
        dbc.Card( # Card Container
            [
                dbc.CardHeader( # Define Card Header
                    [
                        html.H3('Manage Records')
                    ]
                ),
                dbc.CardBody( # Define Card Contents
                    [
                        html.Div( # Add Movie Btn
                            [
                                # Add movie button will work like a 
                                # hyperlink that leads to another page
                                dbc.Button(
                                    "Add Movie",
                                    href='/movies/movie_management_profile?mode=add'
                                )
                            ]
                        ),
                        html.Hr(),
                        html.Div( # Create section to show list of movies
                            [
                                html.H4('Find Movies'),
                                html.Div(
                                    dbc.Form(
                                        dbc.Row(
                                            [
                                                dbc.Label("Search Title", width=1),
                                                dbc.Col(
                                                    dbc.Input(
                                                        type='text',
                                                        id='movie_titlefilter',
                                                        placeholder='Movie Title'
                                                    ),
                                                    width=5
                                                )
                                            ],
                                        )
                                    )
                                ),
                                html.Div(
                                    dbc.Checklist(
                                        id='movie_showdeleted',
                                        options=[dict(value=1, label='Show Deleted Records')],
                                        value=[],
                                        switch=True,
                                    ),
                                    className='mb-3'
                                ),
                                html.Div(
                                    "Table with movies will go here.",
                                    id='movie_movielist'
                                )
                            ]
                        )
                    ]
                )
            ]
        )
    ]
)

@app.callback(
    [
        Output('movie_movielist', 'children'),
    ],
    [
        Input('url', 'pathname'),
        Input('movie_titlefilter', 'value'),
        Input('movie_showdeleted', 'value'),
    ],
)
def updateRecordsTable(pathname, titlefilter, showdeleted):
    
    if pathname == '/movies/movie_management' or titlefilter:
            sql = """ SELECT movie_name, genre_name, movie_delete_ind, to_char(movie_release_date, 'DD Mon YYYY'), 
                movie_id
            FROM movies m
                INNER JOIN genres g ON m.genre_id = g.genre_id
            WHERE 1=1
            """
            val = []

            if not (showdeleted and 1 in showdeleted):
                sql += """ AND NOT movie_delete_ind"""

            if titlefilter:
                sql += """ AND movie_name ilike %s"""
                val += [f'%{titlefilter}%']
            
            col = ["Movie Title", "Genre", "deleteid", "Release Date", 'id']

            df = getDataFromDB(sql, val, col)

            editButtons = []
            for movie_id in df['id']:
                editButtons += [
                    html.Div(
                        dbc.Button("Edit", color='warning', size='sm', 
                                href = f'/movies/movie_management_profile?mode=edit&id={movie_id}'),
                        className='text-center'
                    )
                ]
            
            df['Action'] = editButtons
            df['Status'] = df['deleteid'].apply(lambda deleted: 'Deleted' if deleted else 'Active')
            
            # we don't want to display the 'id' column -- let's exclude it
            df = df[['Movie Title', 'Genre', 'Release Date', 'Status', 'Action']]

            movie_table = dbc.Table.from_dataframe(df, striped=True, bordered=True,
                hover=True, size='sm')
    else:
        raise PreventUpdate

    # movie_table = []
    
    return [movie_table]