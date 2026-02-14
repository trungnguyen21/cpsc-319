-- Create a new database user for the project
CREATE USER benevity_user WITH PASSWORD 'alpine';

-- Create a new database
CREATE DATABASE Benevity;

-- Grant privileges to the user on the database
GRANT ALL PRIVILEGES ON DATABASE Benevity TO benevity_user;

-- Connect to the new database
\c Benevity

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO benevity_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO benevity_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO benevity_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO benevity_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO benevity_user;
