"""
Database-related API endpoints for MongoDB operations.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Path, Query, Depends
from ..models.base import ItemCreate, ItemResponse, ItemUpdate, BaseResponse
from ..models.mongodb import Item
from ..repository.item_repository import ItemRepository


router = APIRouter()


def get_item_repository() -> ItemRepository:
    """Dependency to get item repository."""
    return ItemRepository()


@router.get(
    "/items",
    response_model=List[ItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get All Items",
    description="Retrieve all items with optional filtering"
)
async def get_items(
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    repository: ItemRepository = Depends(get_item_repository)
) -> List[ItemResponse]:
    """
    Retrieve all items with optional filtering and pagination.
    """
    try:
        items = await repository.get_all(
            skip=offset, 
            limit=limit, 
            category=category, 
            is_active=is_active
        )
        
        # Convert MongoDB items to response models
        return [
            ItemResponse(
                id=str(item.id),
                name=item.name,
                description=item.description,
                category=item.category,
                tags=item.tags,
                is_active=item.is_active,
                created_at=item.created_at,
                updated_at=item.updated_at
            )
            for item in items
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving items: {str(e)}"
        )


@router.get(
    "/items/{item_id}",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Item by ID",
    description="Retrieve a specific item by its ID"
)
async def get_item(
    item_id: str = Path(..., description="The ID of the item to retrieve"),
    repository: ItemRepository = Depends(get_item_repository)
) -> ItemResponse:
    """
    Retrieve a specific item by its ID.
    """
    item = await repository.get_by_id(item_id)
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found"
        )
    
    return ItemResponse(
        id=str(item.id),
        name=item.name,
        description=item.description,
        category=item.category,
        tags=item.tags,
        is_active=item.is_active,
        created_at=item.created_at,
        updated_at=item.updated_at
    )


@router.post(
    "/items",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create New Item",
    description="Create a new item"
)
async def create_item(
    item: ItemCreate,
    repository: ItemRepository = Depends(get_item_repository)
) -> ItemResponse:
    """
    Create a new item.
    """
    try:
        # Create MongoDB document from request
        item_doc = Item(
            name=item.name,
            description=item.description,
            category=item.category,
            tags=item.tags,
            is_active=item.is_active
        )
        
        created_item = await repository.create(item_doc)
        
        return ItemResponse(
            id=str(created_item.id),
            name=created_item.name,
            description=created_item.description,
            category=created_item.category,
            tags=created_item.tags,
            is_active=created_item.is_active,
            created_at=created_item.created_at,
            updated_at=created_item.updated_at
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating item: {str(e)}"
        )


@router.put(
    "/items/{item_id}",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Item",
    description="Update an existing item"
)
async def update_item(
    item_update: ItemUpdate,
    item_id: str = Path(..., description="The ID of the item to update"),
    repository: ItemRepository = Depends(get_item_repository)
) -> ItemResponse:
    """
    Update an existing item.
    """
    # Convert update model to dict, excluding unset fields
    update_data = item_update.dict(exclude_unset=True)
    
    updated_item = await repository.update(item_id, update_data)
    
    if not updated_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found"
        )
    
    return ItemResponse(
        id=str(updated_item.id),
        name=updated_item.name,
        description=updated_item.description,
        category=updated_item.category,
        tags=updated_item.tags,
        is_active=updated_item.is_active,
        created_at=updated_item.created_at,
        updated_at=updated_item.updated_at
    )


@router.delete(
    "/items/{item_id}",
    response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete Item",
    description="Delete an existing item"
)
async def delete_item(
    item_id: str = Path(..., description="The ID of the item to delete"),
    repository: ItemRepository = Depends(get_item_repository)
) -> BaseResponse:
    """
    Delete an existing item.
    """
    deleted = await repository.delete(item_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found"
        )
    
    return BaseResponse(
        message=f"Item with ID {item_id} has been successfully deleted"
    )
