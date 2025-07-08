"""
Stock Data Collector V2 테스트
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app.collectors.stock_data_collector_v2 import StockDataCollectorV2

def test_collector():
    """컬렉터 테스트"""
    print("=== Stock Data Collector V2 Test ===\n")
    
    collector = StockDataCollectorV2()
    
    # 1. 주식 목록 수집 테스트
    print("1. Testing Korean Stock List Collection...")
    result = collector.collect_kr_stock_list()
    print(f"Result: {result}")
    
    # 2. 일일 가격 수집 테스트 (오늘)
    print("\n2. Testing Daily Price Collection...")
    today = datetime.now().strftime('%Y-%m-%d')
    result = collector.collect_kr_daily_prices(today)
    print(f"Result: {result}")
    
    # 3. 과거 데이터 수집 테스트 (삼성전자 최근 30일)
    print("\n3. Testing Historical Data Collection (Samsung Electronics)...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    success = collector.collect_historical_data(
        '005930', 
        'KR',
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )
    print(f"Success: {success}")
    
    # 4. 지수 데이터 수집 테스트
    print("\n4. Testing Index Data Collection...")
    result = collector.collect_indices_data(today)
    print(f"Result: {result}")
    
    print("\n=== Test Completed ===")

if __name__ == "__main__":
    test_collector()