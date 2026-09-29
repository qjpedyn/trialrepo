import dash
import psycopg2
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate

from app import app
from apps.dbconnect import getDataFromDB, modifyDB
from urllib.parse import parse_qs, urlparse

layout = html.Div(
    [
        dcc.Store(id='movieprofile_movieid', storage_type='memory', data=0),
        html.H2('Movie Details'), # Page Header
        html.Hr(),
        dbc.Alert(id='movieprofile_alert', is_open=False), # For feedback purposes
        dbc.Form(
            [
                dbc.Row(
                    [
                        dbc.Label("Title", width=1),
                        dbc.Col(
                            dbc.Input(
                                type='text', 
                                id='movieprofile_title',
                                placeholder="Title"
                            ),
                            width=5
                        )
                    ],
                    className='mb-3'
                ),
                dbc.Row(
                    [
                        dbc.Label("Genre", width=1),
                        dbc.Col(
                            html.Div(
                                dcc.Dropdown(
                                    id='movieprofile_genre',
                                    placeholder='Genre'
                                ),
                                className='dash-bootstrap'
                            ),
                            width=5,
                        )
                    ],
                    className='mb-3'
                ),
                dbc.Row(
                    [
                        dbc.Label("Release Date", width=1),
                        dbc.Col(
                            dcc.DatePickerSingle(
                                id='movieprofile_releasedate',
                                placeholder='Release Date',
                                month_format='MMM Do, YY',
                            ),
                            width=5, 
                            className='dash-bootstrap'
                        )
                    ],
                    className='mb-3'
                ),
                html.Div(
                    [
                        dbc.Checklist(
                            id='movieprofile_deleteind',
                            options= [dict(value=1, label="Mark as Deleted")],
                            value=[] 
                        )
                    ], 
                    id='movieprofile_deletediv'
                )

            ]
        ),
          dbc.Button(
            'Submit',
            id='movieprofile_submit',
            n_clicks=0 # Initialize number of clicks
        ),
        dbc.Modal( # Modal = dialog box; feedback for successful saving.
            [
                dbc.ModalHeader(
                    html.H4(id='movieprofile_modal_header')
                ),
                dbc.ModalBody(
                    'Success!'
                ),
                dbc.ModalFooter(
                    dbc.Button(
                        "Proceed",
                        href='/movies/movie_management' # Clicking this would lead to a change of pages
                    )
                )
            ],
            centered=True,
            id='movieprofile_successmodal',
            backdrop='static' # Dialog box does not go away if you click at the background
        )
    ]
)

@app.callback(
    [
        Output('movieprofile_genre', 'options'),
        Output('movieprofile_movieid', 'data'),
        Output('movieprofile_deletediv', 'className')
    ],
    [
        Input('url', 'pathname'),
    ],
    [
        State('url', 'search'),
    ]
)

def movieprofile_populategenres(pathname, urlsearch):
    if pathname == '/movies/movie_management_profile':
        sql = """
        SELECT genre_name as label, genre_id as value
        FROM genres 
        WHERE genre_delete_ind = False
        """
        values = []
        cols = ['label', 'value']

        df = getDataFromDB(sql, values, cols)

        # If no genres found, return an empty options list
        genre_options = df.to_dict('records') if not df.empty else []

        # Safely parse URL search params
        parsed = urlparse(urlsearch or '')
        qs = parse_qs(parsed.query)

        create_mode = qs.get('mode', ['add'])[0]
        if create_mode == 'add':
            movieid = 0
            deletediv = 'd-none'
        else:
            # If id is missing or invalid, fall back to 0 and hide delete div
            try:
                movieid = int(qs.get('id', [0])[0])
                deletediv = ''
            except (ValueError, TypeError):
                movieid = 0
                deletediv = 'd-none'

        return [genre_options, movieid, deletediv]
    else:
        raise PreventUpdate



@app.callback(
    [
        # dbc.Alert Properties
        Output('movieprofile_alert', 'color'),
        Output('movieprofile_alert', 'children'),
        Output('movieprofile_alert', 'is_open'),
        # dbc.Modal Properties
        Output('movieprofile_successmodal', 'is_open'),
        Output('movieprofile_modal_header', 'children'),
    ],
    [
        # For buttons, the property n_clicks 
        Input('movieprofile_submit', 'n_clicks')
    ],
    [
        # The values of the fields are States 
        State('movieprofile_title', 'value'),
        State('movieprofile_genre', 'value'),
        State('movieprofile_releasedate', 'date'),
        State('url', 'search'),
        State('movieprofile_movieid', 'data'),
        State('movieprofile_deleteind', 'value'),
    ]
)
def movieprofile_saveprofile(submitbtn, title, genre, releasedate, 
                             urlsearch, movieid, deleteind):
    ctx = dash.callback_context
    if ctx.triggered:
        eventid = ctx.triggered[0]['prop_id'].split('.')[0]
        parsed = urlparse(urlsearch)
        create_mode = parse_qs(parsed.query)['mode'][0]
    else:
        raise PreventUpdate

    if eventid == 'movieprofile_submit' and submitbtn:
        alert_open = False
        modal_open = False
        alert_color = ''
        alert_text = ''
        modal_header = 'Save Success' if create_mode == 'add' else 'Update Success'

        # Basic input validation
        if not title:
            alert_open = True
            alert_color = 'danger'
            alert_text = 'Check your inputs. Please supply the movie title.'
        elif not genre:
            alert_open = True
            alert_color = 'danger'
            alert_text = 'Check your inputs. Please supply the movie genre.'
        elif not releasedate:
            alert_open = True
            alert_color = 'danger'
            alert_text = 'Check your inputs. Please supply the movie release date.'
        else:
            # Duplicate-title validation (only in Add Mode)
            
            title = title.strip() if title else title

            duplicate_found = False

            if title:
                if create_mode == 'add':
                    dupe_sql = """
                        SELECT COUNT(*) as cnt
                        FROM movies
                        WHERE lower(movie_name) = lower(%s)
                          AND NOT movie_delete_ind
                    """
                    dupe_values = [title]
                    dupe_alert_text = 'A movie with this title already exists. Please enter a unique movie title.'

                elif create_mode == 'edit':
                    dupe_sql = """
                        SELECT COUNT(*) as cnt
                        FROM movies
                        WHERE lower(movie_name) = lower(%s)
                          AND genre_id = %s
                          AND movie_release_date = %s
                          AND NOT movie_delete_ind
                          AND movie_id != %s
                    """
                    dupe_values = [title, genre, releasedate, movieid]
                    dupe_alert_text = 'A movie with this title, genre, and release date already exists.'

                else:
                    dupe_sql = None

                if dupe_sql:
                    dupe_cols = ['cnt']
                    dupe_df = getDataFromDB(dupe_sql, dupe_values, dupe_cols)

                    if int(dupe_df['cnt'].iloc[0]) > 0:
                        duplicate_found = True
                        alert_open = True
                        alert_color = 'danger'
                        alert_text = dupe_alert_text

            if not duplicate_found:
                # Prepare SQL for add or edit
                if create_mode == 'add':
                    sql = '''
                        INSERT INTO movies (movie_name, genre_id,
                            movie_release_date, movie_delete_ind)
                        VALUES (%s, %s, %s, %s)
                    '''
                    values = [title, genre, releasedate, False]

                elif create_mode == 'edit':
                    sql = '''
                        UPDATE movies 
                        SET 
                            movie_name = %s,
                            genre_id = %s,
                            movie_release_date = %s, 
                            movie_delete_ind = %s
                        WHERE
                            movie_id = %s
                    '''
                    deleteindval = True if 1 in deleteind else False
                    values = [title, genre, releasedate, deleteindval, movieid]
                else:
                    raise PreventUpdate

                # Execute DB write with IntegrityError fallback
                try:
                    modifyDB(sql, values)
                    modal_open = True
                except psycopg2.IntegrityError:
                    alert_open = True
                    alert_color = 'danger'
                    alert_text = 'A record with that title already exists.'
                except Exception as e:
                    import traceback
                    print("SAVE ERROR:", repr(e))
                    traceback.print_exc()
                    alert_open = True
                    alert_color = 'danger'
                    alert_text = 'An unexpected error occurred while saving.'

        return [alert_color, alert_text, alert_open, modal_open, modal_header]

    else:
        raise PreventUpdate



@app.callback(
    [
        Output('movieprofile_title', 'value'),
        Output('movieprofile_genre', 'value'),
        Output('movieprofile_releasedate', 'date'),
    ],
    [
        Input('movieprofile_movieid', 'modified_timestamp')
    ],
    [
        State('movieprofile_movieid', 'data'),
    ]
)

def movieprofile_loadprofile(timestamp, movieid):
    if movieid:  # check if movieid > 0

        # Query from db
        sql = """
            SELECT movie_name, genre_id, movie_release_date
            FROM movies
            WHERE movie_id = %s
        """
        values = [movieid]
        col = ['moviename', 'genreid', 'releasedate']

        df = getDataFromDB(sql, values, col)

        if df.empty:
            raise PreventUpdate

        moviename = df['moviename'].iloc[0]

        # genreid may be NULL in the DB; handle that safely
        raw_genreid = df['genreid'].iloc[0]
        genreid = int(raw_genreid) if raw_genreid is not None else None

        releasedate = df['releasedate'].iloc[0]

        return [moviename, genreid, releasedate]

    else:
        raise PreventUpdate

#changes color when mark as deleted checkbox is ticked
@app.callback(
    [
        Output('movieprofile_submit', 'children'),
        Output('movieprofile_submit', 'color')
    ],
    Input('movieprofile_deleteind', 'value')
)

def movieprofile_submit_toggle(deleteind):
    #checks if checkbox is ticked (1) or not ([])
    if 1 in deleteind:
        return "Delete Record", "danger"
    else:
        return "Submit", "primary"