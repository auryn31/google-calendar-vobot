-- Create the user_auth table
CREATE TABLE user_auth (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL,
  google_tokens JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_auth_updated_at
    BEFORE UPDATE ON user_auth
    FOR EACH ROW
    EXECUTE PROCEDURE update_updated_at_column();