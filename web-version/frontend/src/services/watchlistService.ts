import { supabase } from '../lib/supabase'

export interface WatchlistItem {
  id: string
  user_id: string
  stock_symbol: string
  market: 'KR' | 'US'
  added_at: string
}

export const watchlistService = {
  // 관심종목 추가
  async add(stockSymbol: string, market: 'KR' | 'US') {
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) throw new Error('User not authenticated')
    
    const { data, error } = await supabase
      .from('watchlists')
      .insert({ 
        user_id: user.id, 
        stock_symbol: stockSymbol, 
        market 
      })
      .select()
      .single()
    
    if (error) throw error
    return data
  },
  
  // 관심종목 제거
  async remove(stockSymbol: string, market: 'KR' | 'US') {
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) throw new Error('User not authenticated')
    
    const { error } = await supabase
      .from('watchlists')
      .delete()
      .eq('user_id', user.id)
      .eq('stock_symbol', stockSymbol)
      .eq('market', market)
    
    if (error) throw error
  },
  
  // 사용자의 관심종목 조회
  async getAll(): Promise<WatchlistItem[]> {
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) throw new Error('User not authenticated')
    
    const { data, error } = await supabase
      .from('watchlists')
      .select('*')
      .eq('user_id', user.id)
      .order('added_at', { ascending: false })
    
    if (error) throw error
    return data || []
  },
  
  // 특정 종목이 관심종목인지 확인
  async isInWatchlist(stockSymbol: string, market: 'KR' | 'US'): Promise<boolean> {
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return false
    
    const { data, error } = await supabase
      .from('watchlists')
      .select('id')
      .eq('user_id', user.id)
      .eq('stock_symbol', stockSymbol)
      .eq('market', market)
      .single()
    
    return !error && !!data
  }
}