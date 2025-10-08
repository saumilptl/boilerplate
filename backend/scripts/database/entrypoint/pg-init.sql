\set ON_ERROR_STOP on
\echo 'Starting pg-init.sql'

-- Set defaults for local development if not provided
\if :{?db_name}
\else
\set db_name app_db
\endif

\if :{?db_user}
\else
\set db_user app
\endif

\if :{?db_password}
\else
\set db_password app_password
\endif

\echo 'Creating user if needed (with password)...'
SELECT
  CASE
    WHEN NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'db_user')
    THEN 'CREATE USER "' || :'db_user' || '" WITH ENCRYPTED PASSWORD ''' || :'db_password' || ''' LOGIN'
    ELSE 'SELECT ''User already exists'''
  END AS create_user_sql
\gexec

\echo 'Creating database if needed...'
SELECT
  CASE
    WHEN NOT EXISTS (SELECT FROM pg_database WHERE datname = :'db_name')
    THEN 'CREATE DATABASE "' || :'db_name' || '"'
    ELSE 'SELECT ''Database already exists'''
  END AS create_db_sql
\gexec

\echo 'Connecting to database...'
\c :db_name

\echo 'Granting privileges...'
GRANT ALL PRIVILEGES ON DATABASE :"db_name" TO :"db_user";
GRANT ALL ON SCHEMA public TO :"db_user";

\echo 'Database and user initialization complete.'
