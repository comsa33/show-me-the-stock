"""
FinanceDataReader 기본 기능 테스트
"""
import FinanceDataReader as fdr
from datetime import datetime, timedelta
import pandas as pd

print("=== FinanceDataReader 테스트 ===\n")

# 1. 한국 주식 목록 가져오기
print("1. 한국 주식 목록 테스트")
try:
    krx_list = fdr.StockListing('KRX')
    print(f"전체 종목 수: {len(krx_list)}")
    print(f"컬럼: {krx_list.columns.tolist()}")
    print("\n샘플 데이터 (삼성전자):")
    samsung = krx_list[krx_list['Name'].str.contains('삼성전자')]
    print(samsung[['Code', 'Name', 'Market']].head())
except Exception as e:
    print(f"에러 발생: {e}")

# 2. 주식 가격 데이터 가져오기
print("\n\n2. 주식 가격 데이터 테스트 (삼성전자)")
try:
    # 최근 30일 데이터
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    price_data = fdr.DataReader('005930', start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    print(f"데이터 shape: {price_data.shape}")
    print(f"컬럼: {price_data.columns.tolist()}")
    print("\n최근 5일 데이터:")
    print(price_data.tail())
except Exception as e:
    print(f"에러 발생: {e}")

# 3. 한국 지수 데이터 가져오기
print("\n\n3. 한국 지수 데이터 테스트")
try:
    # KOSPI 지수
    kospi = fdr.DataReader('KS11', start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    print(f"KOSPI 데이터 shape: {kospi.shape}")
    print(f"최근 데이터:")
    print(kospi.tail(3))
    
    # KOSDAQ 지수
    kosdaq = fdr.DataReader('KQ11', start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    print(f"\nKOSDAQ 데이터 shape: {kosdaq.shape}")
except Exception as e:
    print(f"에러 발생: {e}")

# 4. 미국 주식 데이터 테스트
print("\n\n4. 미국 주식 데이터 테스트 (Apple)")
try:
    aapl = fdr.DataReader('AAPL', start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    print(f"AAPL 데이터 shape: {aapl.shape}")
    print(f"최근 데이터:")
    print(aapl.tail(3))
except Exception as e:
    print(f"에러 발생: {e}")

# 5. 환율 데이터 테스트
print("\n\n5. 환율 데이터 테스트 (USD/KRW)")
try:
    usdkrw = fdr.DataReader('USD/KRW', start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    print(f"환율 데이터 shape: {usdkrw.shape}")
    print(f"최근 데이터:")
    print(usdkrw.tail(3))
except Exception as e:
    print(f"에러 발생: {e}")

# 6. 데이터 소스 확인
print("\n\n6. 사용 가능한 데이터 소스")
print("- KRX (한국거래소)")
print("- NASDAQ, NYSE, AMEX")
print("- Yahoo Finance")
print("- FRED (연준 경제 데이터)")

print("\n=== 테스트 완료 ===")