"""
Data Cleanup API endpoints
For removing duplicate data and maintaining data integrity
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict
import logging
from pymongo import ASCENDING
from pydantic import BaseModel

from ...database.mongodb_client import get_mongodb_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cleanup", tags=["data-cleanup"])


class CleanupResponse(BaseModel):
    """Response model for cleanup operations"""
    status: str
    message: str
    details: Optional[Dict] = None


class DuplicateStats(BaseModel):
    """Statistics about duplicates found"""
    collection: str
    total_documents: int
    unique_documents: int
    duplicates_found: int
    duplicates_removed: int


@router.get("/check-duplicates")
async def check_duplicates(collection: Optional[str] = None):
    """
    Check for duplicate documents in MongoDB collections
    Returns statistics without removing anything
    """
    try:
        db = get_mongodb_client()
        collections = ["stock_list", "stock_price_daily", "stock_financial", 
                      "market_indices", "stock_realtime"]
        
        if collection:
            if collection not in collections:
                raise HTTPException(status_code=400, detail=f"Invalid collection: {collection}")
            collections = [collection]
        
        stats = []
        
        for coll_name in collections:
            coll = db.db[coll_name]
            
            # Define unique keys for each collection
            if coll_name == "stock_list":
                # For stock_list, symbol should be unique
                pipeline = [
                    {"$group": {
                        "_id": "$symbol",
                        "count": {"$sum": 1},
                        "docs": {"$push": {
                            "id": "$_id",
                            "updated_at": "$updated_at"
                        }}
                    }},
                    {"$match": {"count": {"$gt": 1}}}
                ]
            elif coll_name == "stock_price_daily":
                # For price data, symbol+date should be unique
                pipeline = [
                    {"$group": {
                        "_id": {"symbol": "$symbol", "date": "$date"},
                        "count": {"$sum": 1},
                        "docs": {"$push": {
                            "id": "$_id",
                            "updated_at": "$updated_at"
                        }}
                    }},
                    {"$match": {"count": {"$gt": 1}}}
                ]
            elif coll_name == "stock_financial":
                # For financial data, symbol+date should be unique
                pipeline = [
                    {"$group": {
                        "_id": {"symbol": "$symbol", "date": "$date"},
                        "count": {"$sum": 1},
                        "docs": {"$push": {
                            "id": "$_id",
                            "updated_at": "$updated_at"
                        }}
                    }},
                    {"$match": {"count": {"$gt": 1}}}
                ]
            elif coll_name == "market_indices":
                # For indices, code+date should be unique
                pipeline = [
                    {"$group": {
                        "_id": {"code": "$code", "date": "$date"},
                        "count": {"$sum": 1},
                        "docs": {"$push": {
                            "id": "$_id",
                            "updated_at": "$updated_at"
                        }}
                    }},
                    {"$match": {"count": {"$gt": 1}}}
                ]
            elif coll_name == "stock_realtime":
                # For realtime data, symbol should be unique
                pipeline = [
                    {"$group": {
                        "_id": "$symbol",
                        "count": {"$sum": 1},
                        "docs": {"$push": {
                            "id": "$_id",
                            "last_updated": "$last_updated"
                        }}
                    }},
                    {"$match": {"count": {"$gt": 1}}}
                ]
            
            # Execute aggregation
            duplicates = list(coll.aggregate(pipeline))
            total_docs = coll.count_documents({})
            duplicate_count = sum(d["count"] - 1 for d in duplicates)
            
            stats.append(DuplicateStats(
                collection=coll_name,
                total_documents=total_docs,
                unique_documents=total_docs - duplicate_count,
                duplicates_found=duplicate_count,
                duplicates_removed=0
            ))
            
            logger.info(f"Collection {coll_name}: {duplicate_count} duplicates found")
        
        return {
            "status": "success",
            "message": "Duplicate check completed",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error checking duplicates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remove-duplicates")
async def remove_duplicates(background_tasks: BackgroundTasks,
                          collection: Optional[str] = None,
                          dry_run: bool = True):
    """
    Remove duplicate documents from MongoDB collections
    Keeps the most recently updated document and removes older ones
    
    Args:
        collection: Specific collection to clean (optional)
        dry_run: If True, only simulate removal without actually deleting
    """
    try:
        if dry_run:
            # Just check duplicates without removing
            result = await check_duplicates(collection)
            return CleanupResponse(
                status="dry_run",
                message="Dry run completed - no data was removed",
                details=result
            )
        
        # Actual removal
        background_tasks.add_task(
            _remove_duplicates_task,
            collection
        )
        
        return CleanupResponse(
            status="started",
            message=f"Duplicate removal started for {collection or 'all collections'}"
        )
        
    except Exception as e:
        logger.error(f"Error starting duplicate removal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _remove_duplicates_task(collection: Optional[str] = None):
    """Background task to remove duplicates"""
    try:
        db = get_mongodb_client()
        collections = ["stock_list", "stock_price_daily", "stock_financial", 
                      "market_indices", "stock_realtime"]
        
        if collection:
            collections = [collection] if collection in collections else []
        
        total_removed = 0
        
        for coll_name in collections:
            coll = db.db[coll_name]
            removed_count = 0
            
            # Define unique keys and sort field for each collection
            if coll_name == "stock_list":
                # Group by symbol
                pipeline = [
                    {"$group": {
                        "_id": "$symbol",
                        "count": {"$sum": 1},
                        "docs": {"$push": {
                            "id": "$_id",
                            "updated_at": "$updated_at"
                        }}
                    }},
                    {"$match": {"count": {"$gt": 1}}}
                ]
            elif coll_name == "stock_price_daily":
                # Group by symbol+date
                pipeline = [
                    {"$group": {
                        "_id": {"symbol": "$symbol", "date": "$date"},
                        "count": {"$sum": 1},
                        "docs": {"$push": {
                            "id": "$_id",
                            "updated_at": "$updated_at"
                        }}
                    }},
                    {"$match": {"count": {"$gt": 1}}}
                ]
            elif coll_name == "stock_financial":
                # Group by symbol+date
                pipeline = [
                    {"$group": {
                        "_id": {"symbol": "$symbol", "date": "$date"},
                        "count": {"$sum": 1},
                        "docs": {"$push": {
                            "id": "$_id",
                            "updated_at": "$updated_at"
                        }}
                    }},
                    {"$match": {"count": {"$gt": 1}}}
                ]
            elif coll_name == "market_indices":
                # Group by code+date
                pipeline = [
                    {"$group": {
                        "_id": {"code": "$code", "date": "$date"},
                        "count": {"$sum": 1},
                        "docs": {"$push": {
                            "id": "$_id",
                            "updated_at": "$updated_at"
                        }}
                    }},
                    {"$match": {"count": {"$gt": 1}}}
                ]
            elif coll_name == "stock_realtime":
                # Group by symbol
                pipeline = [
                    {"$group": {
                        "_id": "$symbol",
                        "count": {"$sum": 1},
                        "docs": {"$push": {
                            "id": "$_id",
                            "last_updated": "$last_updated"
                        }}
                    }},
                    {"$match": {"count": {"$gt": 1}}}
                ]
            
            # Find duplicates
            duplicates = list(coll.aggregate(pipeline))
            
            for dup in duplicates:
                # Sort documents by update time (newest first)
                docs = dup["docs"]
                
                # Handle different timestamp fields
                if coll_name == "stock_realtime":
                    docs.sort(key=lambda x: x.get("last_updated", ""), reverse=True)
                else:
                    docs.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
                
                # Keep the first (newest) and remove the rest
                docs_to_remove = [doc["id"] for doc in docs[1:]]
                
                if docs_to_remove:
                    result = coll.delete_many({"_id": {"$in": docs_to_remove}})
                    removed_count += result.deleted_count
            
            total_removed += removed_count
            logger.info(f"Removed {removed_count} duplicates from {coll_name}")
        
        logger.info(f"Total duplicates removed: {total_removed}")
        
    except Exception as e:
        logger.error(f"Error in duplicate removal task: {e}")


@router.post("/rebuild-indexes")
async def rebuild_indexes():
    """
    Rebuild unique indexes to prevent future duplicates
    This will fail if duplicates exist, so run remove-duplicates first
    """
    try:
        db = get_mongodb_client()
        
        # Drop and recreate indexes with unique constraints
        results = []
        
        # stock_list: symbol should be unique
        try:
            db.db.stock_list.drop_index("symbol_1")
        except:
            pass
        db.db.stock_list.create_index("symbol", unique=True)
        results.append("stock_list: created unique index on symbol")
        
        # stock_price_daily: symbol+date should be unique
        try:
            db.db.stock_price_daily.drop_index("symbol_1_date_1")
        except:
            pass
        db.db.stock_price_daily.create_index([("symbol", ASCENDING), ("date", ASCENDING)], unique=True)
        results.append("stock_price_daily: created unique index on symbol+date")
        
        # stock_financial: symbol+date should be unique
        try:
            db.db.stock_financial.drop_index("symbol_1_date_1")
        except:
            pass
        db.db.stock_financial.create_index([("symbol", ASCENDING), ("date", ASCENDING)], unique=True)
        results.append("stock_financial: created unique index on symbol+date")
        
        # market_indices: code+date should be unique
        try:
            db.db.market_indices.drop_index("code_1_date_1")
        except:
            pass
        db.db.market_indices.create_index([("code", ASCENDING), ("date", ASCENDING)], unique=True)
        results.append("market_indices: created unique index on code+date")
        
        # stock_realtime: symbol should be unique
        try:
            db.db.stock_realtime.drop_index("symbol_1")
        except:
            pass
        db.db.stock_realtime.create_index("symbol", unique=True)
        results.append("stock_realtime: created unique index on symbol")
        
        return CleanupResponse(
            status="success",
            message="Indexes rebuilt successfully",
            details={"results": results}
        )
        
    except Exception as e:
        logger.error(f"Error rebuilding indexes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data-integrity-report")
async def data_integrity_report():
    """
    Generate a comprehensive data integrity report
    """
    try:
        db = get_mongodb_client()
        report = {}
        
        # Check each collection
        collections = {
            "stock_list": {"KR": 0, "US": 0},
            "stock_price_daily": {"KR": 0, "US": 0},
            "stock_financial": {"KR": 0, "US": 0},
            "market_indices": {"KR": 0, "US": 0},
            "stock_realtime": {"KR": 0, "US": 0}
        }
        
        for coll_name in collections:
            coll = db.db[coll_name]
            
            # Get counts by market
            kr_count = coll.count_documents({"market": "KR"})
            us_count = coll.count_documents({"market": "US"})
            
            # Get date range for time-series collections
            date_info = {}
            if coll_name in ["stock_price_daily", "stock_financial", "market_indices"]:
                oldest = coll.find_one(sort=[("date", 1)])
                newest = coll.find_one(sort=[("date", -1)])
                if oldest and newest:
                    date_info = {
                        "oldest_date": oldest.get("date"),
                        "newest_date": newest.get("date")
                    }
            
            report[coll_name] = {
                "total": kr_count + us_count,
                "KR": kr_count,
                "US": us_count,
                **date_info
            }
        
        # Check for missing financial data
        stocks_with_prices = db.db.stock_price_daily.distinct("symbol")
        stocks_with_financials = db.db.stock_financial.distinct("symbol")
        missing_financials = set(stocks_with_prices) - set(stocks_with_financials)
        
        report["data_gaps"] = {
            "stocks_missing_financial_data": len(missing_financials),
            "examples": list(missing_financials)[:10]  # Show first 10 examples
        }
        
        return {
            "status": "success",
            "report": report,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating integrity report: {e}")
        raise HTTPException(status_code=500, detail=str(e))