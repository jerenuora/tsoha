CREATE TABLE forums (
    id SERIAL PRIMARY KEY, 
    name TEXT
);

CREATE TABLE threads (
    id SERIAL PRIMARY KEY, 
    title TEXT, 
    owner TEXT,
    forum_id INTEGER REFERENCES forums ON DELETE CASCADE
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY, 
    writer TEXT NOT NULL,
    message TEXT NOT NULL,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    thread_id INTEGER REFERENCES threads ON DELETE CASCADE
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    admin BOOLEAN
);