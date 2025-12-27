-- Aureon by Rhematek Solutions
-- PostgreSQL Initialization Script
-- Multi-Tenancy Database Setup

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For full-text search
CREATE EXTENSION IF NOT EXISTS "btree_gin";  -- For advanced indexing
CREATE EXTENSION IF NOT EXISTS "btree_gist";  -- For advanced indexing

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE aureon_db TO aureon_user;

-- Set timezone to UTC
ALTER DATABASE aureon_db SET timezone TO 'UTC';

-- Performance tuning
ALTER DATABASE aureon_db SET shared_buffers TO '256MB';
ALTER DATABASE aureon_db SET effective_cache_size TO '1GB';
ALTER DATABASE aureon_db SET maintenance_work_mem TO '64MB';
ALTER DATABASE aureon_db SET checkpoint_completion_target TO '0.9';
ALTER DATABASE aureon_db SET wal_buffers TO '16MB';
ALTER DATABASE aureon_db SET default_statistics_target TO '100';
ALTER DATABASE aureon_db SET random_page_cost TO '1.1';
ALTER DATABASE aureon_db SET effective_io_concurrency TO '200';
ALTER DATABASE aureon_db SET work_mem TO '4MB';
ALTER DATABASE aureon_db SET min_wal_size TO '1GB';
ALTER DATABASE aureon_db SET max_wal_size TO '4GB';

-- Create custom functions
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Aureon database initialized successfully';
    RAISE NOTICE 'Database: aureon_db';
    RAISE NOTICE 'User: aureon_user';
    RAISE NOTICE 'Extensions: uuid-ossp, pg_trgm, btree_gin, btree_gist';
    RAISE NOTICE 'Multi-tenancy ready with django-tenants';
END $$;
