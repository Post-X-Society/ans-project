-- Initialize Ans database with pgvector extension

-- Create pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension is installed
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Log success
DO $$
BEGIN
  RAISE NOTICE 'pgvector extension installed successfully';
END $$;
