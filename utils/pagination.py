from typing import Dict, List, Any
from math import ceil

def paginate(query, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
    """
    Paginates a SQLAlchemy query object with error handling.
    
    Args:
        query: SQLAlchemy query object
        page (int): Current page number (default: 1)
        per_page (int): Number of items per page (default: 10)
    
    Returns:
        Dict containing pagination metadata and results
        
    Raises:
        ValueError: If page or per_page are invalid
    """
    try:
        # Validate input parameters
        if page < 1:
            raise ValueError("Page number must be greater than 0")
        if per_page < 1:
            raise ValueError("Items per page must be greater than 0")
            
        # Ensure reasonable limits
        per_page = min(per_page, 100)  # Maximum 100 items per page
        
        # Get total number of items
        try:
            total = query.count()
        except Exception as e:
            print(f"Error counting total items: {str(e)}")
            raise ValueError(f"Database error: {str(e)}")
        
        # Calculate total pages
        pages = ceil(total / per_page) if total > 0 else 1
        
        # Adjust page if it exceeds total pages
        if page > pages:
            page = pages
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get items for current page
        try:
            items = query.offset(offset).limit(per_page).all()
        except Exception as e:
            print(f"Error fetching items: {str(e)}")
            raise ValueError(f"Database error: {str(e)}")
        
        # Calculate pagination metadata
        has_next = page < pages
        has_prev = page > 1
        
        return {
            "success": True,
            "pages": pages,
            "results": items,
            "total": total,
            "current_page": page,
            "has_next": has_next,
            "has_prev": has_prev,
            "per_page": per_page
        }
    except ValueError as e:
        print(f"Pagination error: {str(e)}")
        raise
    except Exception as e:
        print(f"Unexpected error in pagination: {str(e)}")
        raise ValueError(f"Pagination error: {str(e)}")
