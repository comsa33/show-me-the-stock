-- SQL query to check current RLS policies and potential issues

-- Check if RLS is enabled on our tables
SELECT 
    tablename, 
    pg_class.relrowsecurity as rls_enabled
FROM pg_tables
LEFT JOIN pg_class ON pg_tables.tablename = pg_class.relname
WHERE schemaname = 'public' 
AND tablename IN ('profiles', 'user_settings', 'watchlists');

-- Check existing policies on profiles table
SELECT 
    tablename,
    policyname,
    cmd,
    qual,
    with_check
FROM pg_policies 
WHERE tablename = 'profiles';

-- Check existing policies on user_settings table
SELECT 
    tablename,
    policyname,
    cmd,
    qual,
    with_check
FROM pg_policies 
WHERE tablename = 'user_settings';

-- Check existing policies on watchlists table
SELECT 
    tablename,
    policyname,
    cmd,
    qual,
    with_check
FROM pg_policies 
WHERE tablename = 'watchlists';

-- Create or update RLS policies to ensure proper access
-- Profiles table
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any
DROP POLICY IF EXISTS "Users can view own profile" ON profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON profiles;
DROP POLICY IF EXISTS "Users can insert own profile" ON profiles;

-- Create new policies
CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON profiles
    FOR INSERT WITH CHECK (auth.uid() = id);

-- User settings table
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any
DROP POLICY IF EXISTS "Users can view own settings" ON user_settings;
DROP POLICY IF EXISTS "Users can update own settings" ON user_settings;
DROP POLICY IF EXISTS "Users can insert own settings" ON user_settings;

-- Create new policies
CREATE POLICY "Users can view own settings" ON user_settings
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own settings" ON user_settings
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own settings" ON user_settings
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Watchlists table
ALTER TABLE watchlists ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any
DROP POLICY IF EXISTS "Users can view own watchlist" ON watchlists;
DROP POLICY IF EXISTS "Users can manage own watchlist" ON watchlists;

-- Create new policies
CREATE POLICY "Users can view own watchlist" ON watchlists
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own watchlist" ON watchlists
    FOR ALL USING (auth.uid() = user_id);