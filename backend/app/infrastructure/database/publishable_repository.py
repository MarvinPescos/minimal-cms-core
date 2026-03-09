from slugify import slugify
from typing import List
from sqlalchemy import select, and_
from sqlalchemy.exc import SQLAlchemyError
import uuid

from .soft_delete_repository import SoftDeleteRepository, ModelType
from .exceptions import DatabaseError
from ..observability import log

class PublishableRepository(SoftDeleteRepository[ModelType]):
    
    def _build_conditions(
        self, 
        published_only: bool = False,
        **kwargs
        ) -> list:
        conditions = super()._build_conditions(**kwargs)

        if published_only:
            conditions.append(self.model.is_published == True)
        
        return conditions

        