-- Eliminates the autoshorts_db database if it exists and then creates it
DROP DATABASE IF EXISTS autoshorts_db;
CREATE DATABASE autoshorts_db;

-- Connects to the autoshorts_db
\c autoshorts_db

-- Creates the tables for the database

-- Users table to hold the identity and the voice info
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    voice_id TEXT NOT NULL
);

-- Prompt config table to hold the specific prompt details of the user
CREATE TABLE prompt_config (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    topic TEXT NOT NULL,
    scope TEXT,
    covered_topics TEXT[] DEFAULT '{}',
    wpm INT NOT NULL DEFAULT 125
);

-- Social tokens table to hold the platform to automate/schedule posting
CREATE TABLE social_tokens (
    id SERIAL PRIMARY KEY,
    -- TODO: Strongly consider implementing encription in this table
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    platform TEXT,

    -- OAuth style tokens (eg, Youtube)
    access_token TEXT,
    refresh_token TEXT,
    token_expiry TIMESTAMP,

    -- Username/Password fields for login based automation (eg, Instagram)
    username TEXT,
    password TEXT
);

-- User posting shedule table
CREATE TABLE user_schedule (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    schedule_day VARCHAR NOT NULL,
    schedule_hour INT NOT NULL, 
    UNIQUE(user_id, schedule_day, schedule_hour)  -- Prevents duplicates
    -- schedule_time TIME NOT NULL 
);