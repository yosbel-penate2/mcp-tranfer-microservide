"""Dynamic CRUD router factory.

Generates standard REST endpoints (GET list, GET by id, POST, PUT, DELETE)
for any SQLAlchemy model with Pydantic schemas, minimizing boilerplate.
"""

from typing import Any, Callable, List, Optional, Tuple, Type

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from api.dependencies import get_session
from api.security import get_current_user


def create_crud_router(
    model: Any,
    schema_in: Type[BaseModel],
    schema_out: Type[BaseModel],
    prefix: str,
    tags: List[str],
    identifier: str = "id",
    get_session_dep: Callable = get_session,
    auth_dep: Callable = get_current_user,
) -> APIRouter:
    """Factory that creates a fully-featured CRUD router for a given model.

    All endpoints require JWT authentication (via auth_dep).

    Generated endpoints:
        GET    /{prefix}/       — List all (paginated via skip/limit)
        GET    /{prefix}/{id}   — Get by primary key
        POST   /{prefix}/       — Create new entity
        PUT    /{prefix}/{id}   — Full update
        DELETE /{prefix}/{id}   — Delete by primary key

    Args:
        model: SQLAlchemy model class.
        schema_in: Pydantic schema for create/update request body.
        schema_out: Pydantic schema for response serialization.
        prefix: URL prefix (e.g. "/clientes").
        tags: OpenAPI tags for endpoint grouping.
        identifier: Primary key field name (default "id").
        get_session_dep: FastAPI dependency for DB sessions.
        auth_dep: FastAPI dependency for authentication.

    Returns:
        Configured APIRouter instance.
    """
    router = APIRouter(prefix=prefix, tags=tags, dependencies=[Depends(auth_dep)])

    @router.get("/", response_model=List[schema_out])
    def list_all(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        session: Session = Depends(get_session_dep),
    ):
        """List all entities with pagination."""
        return session.query(model).offset(skip).limit(limit).all()

    @router.get("/{item_id}", response_model=schema_out)
    def get_by_id(
        item_id: int,
        session: Session = Depends(get_session_dep),
    ):
        """Get a single entity by its primary key."""
        obj = session.get(model, item_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model.__name__} not found",
            )
        return obj

    @router.post("/", response_model=schema_out, status_code=status.HTTP_201_CREATED)
    def create(
        data: schema_in,
        session: Session = Depends(get_session_dep),
    ):
        """Create a new entity."""
        obj = model(**data.model_dump())
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj

    @router.put("/{item_id}", response_model=schema_out)
    def update(
        item_id: int,
        data: schema_in,
        session: Session = Depends(get_session_dep),
    ):
        """Fully update an existing entity."""
        obj = session.get(model, item_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model.__name__} not found",
            )
        for key, value in data.model_dump().items():
            setattr(obj, key, value)
        session.commit()
        session.refresh(obj)
        return obj

    @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete(
        item_id: int,
        session: Session = Depends(get_session_dep),
    ):
        """Delete an entity by primary key."""
        obj = session.get(model, item_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model.__name__} not found",
            )
        session.delete(obj)
        session.commit()

    return router
