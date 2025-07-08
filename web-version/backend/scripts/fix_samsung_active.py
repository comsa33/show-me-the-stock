#!/usr/bin/env python3
"""삼성전자 is_active 필드 수정 스크립트"""
from app.database.mongodb_client import get_mongodb_client

db = get_mongodb_client()

# 삼성전자에 is_active 필드 추가
result = db.db.stock_list.update_one(
    {"symbol": "005930"},
    {"$set": {"is_active": True}}
)

print(f"삼성전자 업데이트 결과: {result.modified_count}개 수정됨")

# 확인
samsung = db.db.stock_list.find_one({"symbol": "005930"})
print(f"\n업데이트 후 삼성전자: is_active = {samsung.get('is_active')}")

# is_active 필드가 없는 모든 종목에 True 추가
result_all = db.db.stock_list.update_many(
    {"is_active": {"$exists": False}},
    {"$set": {"is_active": True}}
)

print(f"\n전체 업데이트 결과: {result_all.modified_count}개 수정됨")

# 최종 확인
active_kr = db.db.stock_list.count_documents({"market": "KR", "is_active": True})
total_kr = db.db.stock_list.count_documents({"market": "KR"})
print(f"\n최종 is_active=True인 한국 종목: {active_kr}개 / 전체: {total_kr}개")