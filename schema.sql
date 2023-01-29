CREATE TABLE forums (
    id SERIAL PRIMARY KEY, 
    name TEXT
);

CREATE TABLE threads (
    id SERIAL PRIMARY KEY, 
    title TEXT, 
    owner TEXT,
    forum_id INTEGER REFERENCES forums
);