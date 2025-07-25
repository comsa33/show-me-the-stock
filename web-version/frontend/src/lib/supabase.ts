import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL!
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  }
})

// 타입 정의
export type Database = {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string
          username: string | null
          full_name: string | null
          avatar_url: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id: string
          username?: string | null
          full_name?: string | null
          avatar_url?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          username?: string | null
          full_name?: string | null
          avatar_url?: string | null
          created_at?: string
          updated_at?: string
        }
      }
      portfolios: {
        Row: {
          id: string
          user_id: string
          stock_symbol: string
          market: 'KR' | 'US'
          quantity: number
          purchase_price: number | null
          purchase_date: string | null
          created_at: string
        }
      }
      watchlists: {
        Row: {
          id: string
          user_id: string
          stock_symbol: string
          market: 'KR' | 'US'
          added_at: string
        }
      }
      user_settings: {
        Row: {
          user_id: string
          theme: string
          language: string
          real_time_alerts: boolean
          email_notifications: boolean
          updated_at: string
        }
      }
    }
  }
}