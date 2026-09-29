




CREATE TABLE genres (
    genre_id serial primary key not null,
    genre_name varchar(128),
    genre_modified_on timestamp without time zone default now(),
    genre_delete_ind boolean default false
);

CREATE TABLE movies (
    movie_id serial primary key not null,
    movie_name varchar(256),
    genre_id int references genres(genre_id),
    movie_release_date date,
    movie_delete_ind boolean default false
);
