#!/usr/bin/env python3
"""
Example script for using the new data collection APIs
Shows how to collect stock data without pykrx
"""
import requests
import time
import json
from datetime import datetime, timedelta


BASE_URL = "http://localhost:8000/api/v1/data"


def print_status(response):
    """Print API response status"""
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data.get('message', 'Success')}")
        if 'details' in data:
            print(f"   Details: {json.dumps(data['details'], indent=2)}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")


def get_collection_status():
    """Get current collection status"""
    print("\n📊 Getting Collection Status...")
    response = requests.get(f"{BASE_URL}/status")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nStock Counts:")
        print(f"  - Korean: {data['stocks']['KR']:,}")
        print(f"  - US: {data['stocks']['US']:,}")
        print(f"  - Total: {data['stocks']['total']:,}")
        
        print(f"\nPrice Data:")
        print(f"  - Korean: {data['price_data']['KR']['count']:,} records (latest: {data['price_data']['KR']['latest_date']})")
        print(f"  - US: {data['price_data']['US']['count']:,} records (latest: {data['price_data']['US']['latest_date']})")
        
        print(f"\nFinancial Data:")
        print(f"  - Korean: {data['financial_data']['KR']:,} records")
        print(f"  - US: {data['financial_data']['US']:,} records")
        
        print(f"\nData Providers:")
        for market, provider in data['data_providers'].items():
            print(f"  - {market}: {provider}")
    else:
        print_status(response)


def collect_stock_lists():
    """Collect stock lists for both markets"""
    print("\n📋 Collecting Stock Lists...")
    
    # Korean stocks
    print("  - Collecting Korean stocks...")
    response = requests.post(f"{BASE_URL}/stocks/list/KR")
    print_status(response)
    
    # US stocks
    print("  - Collecting US stocks...")
    response = requests.post(f"{BASE_URL}/stocks/list/US")
    print_status(response)


def collect_sample_historical_data():
    """Collect historical data for sample stocks"""
    print("\n📈 Collecting Sample Historical Data...")
    
    # Sample Korean stocks
    kr_samples = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, NAVER
    
    # Last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    data = {
        "symbols": kr_samples,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "market": "KR"
    }
    
    print(f"  - Collecting 30 days of data for {len(kr_samples)} Korean stocks...")
    response = requests.post(f"{BASE_URL}/prices/historical", json=data)
    print_status(response)
    
    # Sample US stocks
    us_samples = ["AAPL", "GOOGL", "MSFT"]
    
    data["symbols"] = us_samples
    data["market"] = "US"
    
    print(f"  - Collecting 30 days of data for {len(us_samples)} US stocks...")
    response = requests.post(f"{BASE_URL}/prices/historical", json=data)
    print_status(response)


def collect_financial_data():
    """Collect financial data for sample stocks"""
    print("\n💰 Collecting Financial Data...")
    
    # Korean stocks
    print("  - Collecting financial data for 5 Korean stocks...")
    response = requests.post(
        f"{BASE_URL}/financial/KR",
        params={"limit": 5}
    )
    print_status(response)
    
    # Specific US stocks
    us_symbols = ["AAPL", "TSLA", "NVDA"]
    print(f"  - Collecting financial data for {len(us_symbols)} US stocks...")
    response = requests.post(
        f"{BASE_URL}/financial/US",
        params={"symbols": us_symbols}
    )
    print_status(response)


def collect_yearly_batch():
    """Example of collecting data for a specific year in batches"""
    print("\n📅 Collecting Yearly Data in Batches...")
    
    # Collect 2024 Korean stock data, 10 stocks at a time
    response = requests.post(
        f"{BASE_URL}/batch/yearly",
        params={
            "market": "KR",
            "year": 2024,
            "batch_size": 10,
            "offset": 0
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print_status(response)
        
        # Show batch information
        if 'details' in data:
            details = data['details']
            print(f"\n  Batch Progress:")
            print(f"    - Processed: {details['offset']} - {details['offset'] + details['stocks_in_batch']}")
            print(f"    - Total stocks: {details['total_stocks']}")
            print(f"    - Has more: {details['has_more']}")
            if details['has_more']:
                print(f"    - Next offset: {details['next_offset']}")


def collect_daily_data():
    """Collect today's data"""
    print("\n📆 Collecting Daily Data...")
    
    # Korean market
    print("  - Collecting today's Korean market data...")
    response = requests.post(f"{BASE_URL}/daily/KR")
    print_status(response)
    
    # Note: This would skip weekends automatically


def main():
    """Main example workflow"""
    print("=" * 60)
    print("Data Collection V3 Example")
    print("Using new data providers instead of pykrx")
    print("=" * 60)
    
    # 1. Check current status
    get_collection_status()
    
    # 2. Update stock lists (if needed)
    # collect_stock_lists()
    
    # 3. Collect sample historical data
    collect_sample_historical_data()
    
    # 4. Collect financial data
    collect_financial_data()
    
    # 5. Show yearly batch collection
    collect_yearly_batch()
    
    # 6. Daily collection (skip on weekends)
    if datetime.now().weekday() not in [5, 6]:
        collect_daily_data()
    else:
        print("\n⚠️  Skipping daily collection (weekend)")
    
    print("\n✅ Example completed!")
    print("\nNote: All collections run in background. Check logs for progress.")
    print("Rate limiting is automatically applied to avoid being blocked.")


if __name__ == "__main__":
    main()