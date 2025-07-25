-- Clean up orphaned data and fix data inconsistency
-- Run this in Supabase SQL Editor to clean up data

-- First, check for users without profiles
SELECT 
  au.id as user_id,
  au.email,
  au.created_at,
  p.id as profile_id
FROM auth.users au
LEFT JOIN public.profiles p ON au.id = p.id
WHERE p.id IS NULL;

-- Create missing profiles for existing users
INSERT INTO public.profiles (id, username, full_name, avatar_url)
SELECT 
  au.id,
  COALESCE(au.raw_user_meta_data->>'username', split_part(au.email, '@', 1)),
  COALESCE(au.raw_user_meta_data->>'full_name', ''),
  COALESCE(au.raw_user_meta_data->>'avatar_url', '')
FROM auth.users au
LEFT JOIN public.profiles p ON au.id = p.id
WHERE p.id IS NULL;

-- Create missing user_settings for existing users
INSERT INTO public.user_settings (user_id)
SELECT 
  au.id
FROM auth.users au
LEFT JOIN public.user_settings us ON au.id = us.user_id
WHERE us.user_id IS NULL;

-- To delete a specific user and all related data (replace USER_ID with actual ID)
-- CAUTION: This will delete all user data
/*
DO $$
DECLARE
  target_user_id UUID := '61cae2a9-45ca-4bfd-b998-87f84240d1c1'; -- Replace with actual user ID
BEGIN
  -- Delete in reverse order of foreign key dependencies
  DELETE FROM public.watchlist WHERE user_id = target_user_id;
  DELETE FROM public.portfolios WHERE user_id = target_user_id;
  DELETE FROM public.user_settings WHERE user_id = target_user_id;
  DELETE FROM public.profiles WHERE id = target_user_id;
  -- Finally delete from auth.users
  DELETE FROM auth.users WHERE id = target_user_id;
END $$;
*/

-- Check data consistency
SELECT 
  'Users without profiles' as issue,
  COUNT(*) as count
FROM auth.users au
LEFT JOIN public.profiles p ON au.id = p.id
WHERE p.id IS NULL
UNION ALL
SELECT 
  'Users without settings' as issue,
  COUNT(*) as count
FROM auth.users au
LEFT JOIN public.user_settings us ON au.id = us.user_id
WHERE us.user_id IS NULL
UNION ALL
SELECT 
  'Orphaned profiles' as issue,
  COUNT(*) as count
FROM public.profiles p
LEFT JOIN auth.users au ON p.id = au.id
WHERE au.id IS NULL;