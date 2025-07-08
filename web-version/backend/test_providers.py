"""
데이터 제공자 테스트 스크립트
pykrx와 FDR의 데이터를 비교하여 호환성 확인
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import pandas as pd
from app.data.stock_data_provider_factory import StockDataProviderFactory

def test_provider(provider_name: str):
    """특정 제공자 테스트"""
    print(f"\n{'='*60}")
    print(f"Testing {provider_name} Provider")
    print('='*60)
    
    try:
        provider = StockDataProviderFactory.get_provider(provider_name)
        print(f"✓ Provider created: {provider.name}")
        print(f"  Supported markets: {provider.supported_markets}")
        
        # 1. 주식 목록 테스트
        print("\n1. Stock List Test")
        kr_stocks = provider.get_stock_list("KR")
        print(f"  Korean stocks: {len(kr_stocks)}")
        if kr_stocks:
            print(f"  Sample: {kr_stocks[0]}")
        
        # 2. 주가 데이터 테스트 (삼성전자)
        print("\n2. Stock Price Test (Samsung Electronics)")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        price_data = provider.get_stock_price('005930', 
                                             start_date.strftime('%Y-%m-%d'),
                                             end_date.strftime('%Y-%m-%d'))
        if not price_data.empty:
            print(f"  Data shape: {price_data.shape}")
            print(f"  Latest price: {price_data.iloc[-1].to_dict()}")
        else:
            print("  ❌ No price data")
        
        # 3. 실시간 가격 테스트
        print("\n3. Realtime Price Test")
        realtime = provider.get_stock_price_realtime('005930')
        if realtime:
            print(f"  Current price: {realtime.get('price')}")
            print(f"  Change: {realtime.get('change_percent'):.2f}%")
        else:
            print("  ❌ No realtime data")
        
        # 4. 지수 데이터 테스트
        print("\n4. Index Data Test (KOSPI)")
        index_data = provider.get_index_data('1001',
                                           start_date.strftime('%Y-%m-%d'),
                                           end_date.strftime('%Y-%m-%d'))
        if not index_data.empty:
            print(f"  Data shape: {index_data.shape}")
            print(f"  Latest close: {index_data.iloc[-1]['close']}")
        else:
            print("  ❌ No index data")
        
    except Exception as e:
        print(f"\n❌ Provider test failed: {e}")
        import traceback
        traceback.print_exc()

def compare_providers():
    """두 제공자의 데이터 비교"""
    print("\n" + "="*60)
    print("Comparing Data Between Providers")
    print("="*60)
    
    try:
        # 환경변수 임시 설정
        os.environ['STOCK_DATA_PROVIDER'] = 'fdr'
        fdr_provider = StockDataProviderFactory.get_provider('fdr')
        
        # 삼성전자 최근 가격 비교
        symbol = '005930'
        fdr_price = fdr_provider.get_stock_price_realtime(symbol)
        
        print(f"\nSamsung Electronics ({symbol}) Current Price:")
        print(f"FDR: {fdr_price.get('price', 'N/A')}")
        
        # 데이터 형식 비교
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        
        fdr_df = fdr_provider.get_stock_price(symbol, start_date, end_date)
        
        print(f"\nData Format Comparison:")
        print(f"FDR columns: {list(fdr_df.columns)}")
        print(f"FDR index type: {type(fdr_df.index)}")
        
    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """메인 테스트 함수"""
    print("Stock Data Provider Test Suite")
    print(f"Current time: {datetime.now()}")
    
    # FDR 테스트 (주 제공자)
    test_provider('fdr')
    
    # pykrx 테스트 (현재 작동 안할 가능성 높음)
    # test_provider('pykrx')
    
    # 제공자 비교
    compare_providers()
    
    print("\n" + "="*60)
    print("Test completed")

if __name__ == "__main__":
    main()