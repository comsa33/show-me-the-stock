# Supabase Database Setup Instructions

## Issue Resolved
The error was due to a table name mismatch. The actual table name is `watchlists` (plural) not `watchlist` (singular).

## Solution Applied
The watchlistService has been updated to use the correct table name `watchlists`.

## If You Still Have Issues

### Check RLS Policies
If you're still having issues accessing data:
1. Go to your Supabase Dashboard
2. Navigate to SQL Editor
3. Copy and paste the contents of `/src/sql/009_check_rls_policies.sql`
4. Update the script to use `watchlists` instead of `watchlist`
5. Click "Run" to check and fix RLS policies

## Verification
After running the SQL scripts:
1. Refresh your application
2. The "Loading..." issue should be resolved
3. You should be able to view your profile
4. Watchlist functionality should work properly

## Debug Information
The SessionDebug component (bottom-right corner) shows:
- Current session status
- User authentication state
- Any session-related errors

Once everything is working, you can remove the debug component by following the instructions in `LOADING_ISSUE_FIX.md`.

## Important Notes
- Make sure to run the SQL in the correct Supabase project
- The trigger for automatic profile creation uses `$$` delimiter (not single `$`)
- All tables have Row Level Security (RLS) enabled for data protection
- Each user can only access their own data