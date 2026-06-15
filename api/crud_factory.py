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
    router = APIRouter(prefix=prefix, tags=tags, dependencies=[Depends(auth_dep)])

    @router.get("/", response_model=List[schema_out])
    def list_all(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        session: Session = Depends(get_session_dep),
    ):
        return session.query(model).offset(skip).limit(limit).all()

    @router.get("/{item_id}", response_model=schema_out)
    def get_by_id(
        item_id: int,
        session: Session = Depends(get_session_dep),
    ):
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
        obj = session.get(model, item_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model.__name__} not found",
            )
        session.delete(obj)
        session.commit()

    return router
