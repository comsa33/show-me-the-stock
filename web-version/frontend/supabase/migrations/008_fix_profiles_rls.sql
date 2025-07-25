-- Fix RLS policies for profiles table
-- This ensures users can properly read their own profiles

-- Enable RLS if not already enabled
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view their own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can update their own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can insert their own profile" ON public.profiles;

-- Create simple, clear policies
CREATE POLICY "Enable read access for users based on user_id" ON public.profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Enable insert for users based on user_id" ON public.profiles
  FOR INSERT WITH CHECK (auth.uid() = id);

CREATE POLICY "Enable update for users based on user_id" ON public.profiles
  FOR UPDATE USING (auth.uid() = id);

-- Do the same for user_settings
ALTER TABLE public.user_settings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own settings" ON public.user_settings;
DROP POLICY IF EXISTS "Users can update their own settings" ON public.user_settings;
DROP POLICY IF EXISTS "Users can insert their own settings" ON public.user_settings;

CREATE POLICY "Enable read access for user settings" ON public.user_settings
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Enable insert for user settings" ON public.user_settings
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Enable update for user settings" ON public.user_settings
  FOR UPDATE USING (auth.uid() = user_id);

-- Test the policies
SELECT tablename, policyname, cmd, permissive
FROM pg_policies
WHERE tablename IN ('profiles', 'user_settings')
ORDER BY tablename, policyname;