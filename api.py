from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from supabase import create_client, Client
from typing import Optional, List, Dict, Any
import os
from datetime import datetime
import json
import subprocess
from dotenv import load_dotenv
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="News Feed API",
    description="API to fetch paginated news data from Supabase",
    version="1.0.0"
)

# Supabase configuration - Replace with your actual values
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

# Initialize Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Error initializing Supabase client: {e}")
    supabase = None

# Constants
NEWS_PER_PAGE = 100

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "News Feed API",
        "version": "1.0.0",
        "endpoints": {
            "/api/news/{page}": "Get paginated news data",
            "/api/news/search": "Search news with filters",
            "/health": "Health check"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
    
    try:
        # Test connection with a simple count query
        result = supabase.table("news_feed").select("id", count="exact").limit(1).execute()
        return {
            "status": "healthy",
            "database": "connected",
            "total_records": result.count if hasattr(result, 'count') else "unknown"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.get("/api/news/{page}")
async def get_news_page(page: int):
    """
    Get paginated news data
    
    Args:
        page: Page number (starts from 1)
    
    Returns:
        JSON response with news data and pagination info
    """
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
    
    if page < 1:
        raise HTTPException(status_code=400, detail="Page number must be greater than 0")
    
    try:
        # Calculate offset
        offset = (page - 1) * NEWS_PER_PAGE
        
        # Get total count for pagination info
        count_result = supabase.table("news_feed").select("id", count="exact").execute()
        total_records = count_result.count if hasattr(count_result, 'count') else 0
        
        # Calculate pagination info
        total_pages = (total_records + NEWS_PER_PAGE - 1) // NEWS_PER_PAGE
        has_next = page < total_pages
        has_previous = page > 1
        
        # Fetch paginated data
        result = supabase.table("news_feed")\
            .select("*")\
            .order("scraped_timestamp", desc=True)\
            .range(offset, offset + NEWS_PER_PAGE - 1)\
            .execute()
        
        news_data = result.data if result.data else []
        
        # Format response
        response_data = {
            "success": True,
            "data": news_data,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_records": total_records,
                "records_per_page": NEWS_PER_PAGE,
                "records_in_current_page": len(news_data),
                "has_next": has_next,
                "has_previous": has_previous,
                "next_page": page + 1 if has_next else None,
                "previous_page": page - 1 if has_previous else None
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching news data: {str(e)}")

@app.get("/api/news/search")
async def search_news(
    page: int = Query(1, ge=1, description="Page number"),
    category: Optional[str] = Query(None, description="Filter by category"),
    source: Optional[str] = Query(None, description="Filter by source"),
    country: Optional[str] = Query(None, description="Filter by country"),
    language: Optional[str] = Query(None, description="Filter by language"),
    author: Optional[str] = Query(None, description="Filter by author"),
    search_title: Optional[str] = Query(None, description="Search in title"),
    limit: int = Query(NEWS_PER_PAGE, ge=1, le=500, description="Records per page")
):
    """
    Search and filter news data with pagination
    
    Args:
        page: Page number
        category: Filter by category
        source: Filter by source
        country: Filter by country
        language: Filter by language
        author: Filter by author
        search_title: Search term in title
        limit: Number of records per page (max 500)
    
    Returns:
        JSON response with filtered news data and pagination info
    """
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
    
    try:
        # Build query
        query = supabase.table("news_feed").select("*")
        count_query = supabase.table("news_feed").select("id", count="exact")
        
        # Apply filters
        if category:
            query = query.eq("category", category)
            count_query = count_query.eq("category", category)
        
        if source:
            query = query.eq("source", source)
            count_query = count_query.eq("source", source)
        
        if country:
            query = query.eq("country", country)
            count_query = count_query.eq("country", country)
        
        if language:
            query = query.eq("language", language)
            count_query = count_query.eq("language", language)
        
        if author:
            query = query.eq("author", author)
            count_query = count_query.eq("author", author)
        
        if search_title:
            query = query.ilike("title", f"%{search_title}%")
            count_query = count_query.ilike("title", f"%{search_title}%")
        
        # Get total count
        count_result = count_query.execute()
        total_records = count_result.count if hasattr(count_result, 'count') else 0
        
        # Calculate pagination
        offset = (page - 1) * limit
        total_pages = (total_records + limit - 1) // limit
        has_next = page < total_pages
        has_previous = page > 1
        
        # Execute main query with pagination
        result = query.order("scraped_timestamp", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        news_data = result.data if result.data else []
        
        # Format response
        response_data = {
            "success": True,
            "data": news_data,
            "filters": {
                "category": category,
                "source": source,
                "country": country,
                "language": language,
                "author": author,
                "search_title": search_title
            },
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_records": total_records,
                "records_per_page": limit,
                "records_in_current_page": len(news_data),
                "has_next": has_next,
                "has_previous": has_previous,
                "next_page": page + 1 if has_next else None,
                "previous_page": page - 1 if has_previous else None
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching news data: {str(e)}")

@app.get("/api/news/latest")
async def get_latest_news(limit: int = Query(10, ge=1, le=100, description="Number of latest news items")):
    """
    Get the latest news items
    
    Args:
        limit: Number of latest news items to fetch (max 100)
    
    Returns:
        JSON response with latest news data
    """
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
    
    try:
        result = supabase.table("news_feed")\
            .select("*")\
            .order("scraped_timestamp", desc=True)\
            .limit(limit)\
            .execute()
        
        news_data = result.data if result.data else []
        
        response_data = {
            "success": True,
            "data": news_data,
            "count": len(news_data),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching latest news: {str(e)}")

@app.get("/api/stats")
async def get_news_stats():
    """
    Get statistics about the news database
    
    Returns:
        JSON response with database statistics
    """
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
    
    try:
        # Total count
        total_result = supabase.table("news_feed").select("id", count="exact").execute()
        total_count = total_result.count if hasattr(total_result, 'count') else 0
        
        # Count by category
        categories_result = supabase.rpc("get_category_counts").execute()
        categories = categories_result.data if categories_result.data else []
        
        # Count by source
        sources_result = supabase.rpc("get_source_counts").execute()
        sources = sources_result.data if sources_result.data else []
        
        response_data = {
            "success": True,
            "total_records": total_count,
            "categories": categories,
            "sources": sources,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        # Fallback if RPC functions don't exist
        response_data = {
            "success": True,
            "total_records": total_count if 'total_count' in locals() else 0,
            "note": "Detailed statistics require custom RPC functions in Supabase",
            "timestamp": datetime.utcnow().isoformat()
        }
        return JSONResponse(content=response_data)

@app.post("/update")
async def update_data():
    """
    Run rss_scraper_db_save.py once when this endpoint is hit
    """
    try:
        result = subprocess.run(
            ["python", "rss_scraper_db_save.py"],
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True,
            check=True
        )
        return {
            "success": True,
            "message": "Script executed successfully",
            "output": result.stdout
        }
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Script execution failed: {e.stderr}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)