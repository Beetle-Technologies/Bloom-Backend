from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import SQLModel, col, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.constants import DEFAULT_PAGE_SIZE
from src.core.database.transaction import in_transaction
from src.core.exceptions import errors
from src.core.helpers.misc import call
from src.core.types import IDType
from src.libs.query_engine import (
    BaseQueryEngineParams,
    EntityNotFoundError,
    GeneralPaginationRequest,
    GeneralPaginationResponse,
    QueryEngineError,
    QueryEngineService,
)

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base repository providing CRUD operations for SQLModel models.\n
    It allows for flexible querying capabilities, standard database operations,
    and general pagination support (keyset by default).

    Automatically detects if operations are running within a transaction context
    and adjusts commit behavior accordingly.
    """

    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
        self.query_engine = QueryEngineService(model, session)

    async def _save_changes(self, refresh_obj=None):
        """
        Save changes to the database, respecting transaction context.

        If running within a transaction, just flush changes.
        If not in a transaction, commit changes.

        Args:
            refresh_obj: Object to refresh after saving changes
        """
        if in_transaction():
            await self.session.flush()
        else:
            await self.session.commit()

        if refresh_obj is not None:
            await self.session.refresh(refresh_obj)

    async def find(
        self,
        *,
        pagination: GeneralPaginationRequest | None = None,
    ) -> GeneralPaginationResponse[ModelType]:
        """
        Find records using general pagination (keyset by default).

        Args:
            pagination (GeneralPaginationRequest): General pagination request (if None, creates one with defaults)

        Returns:
            GeneralPaginationResponse (keyset or offset based on type)
        """

        if pagination is None:
            pagination = GeneralPaginationRequest(
                limit=DEFAULT_PAGE_SIZE,
                order_by=["created_datetime"],
            )

        return await self.query_engine.paginate(pagination=pagination)

    async def find_one_by_and_none(self, **kwargs: Any) -> ModelType | None:
        """
        Find a single record by field values (use AND condition).

        Args:
            **kwargs: Field names and values to filter by

        Returns:
            The found record or None
        """
        query = select(self.model)
        for field, value in kwargs.items():
            if hasattr(self.model, field):
                query = query.where(col(getattr(self.model, field)) == value)
        result = await self.session.exec(query)
        return result.one_or_none()

    async def find_one_by_or_none(self, **kwargs: Any) -> ModelType | None:
        """
        Find a single record by field values (use OR condition).

        Args:
            **kwargs: Field names and values to filter by

        Returns:
            The found record or None
        """
        query = select(self.model)
        conditions = [
            col(getattr(self.model, field)) == value for field, value in kwargs.items() if hasattr(self.model, field)
        ]

        if not conditions:
            return None

        query = query.filter(or_(*conditions))
        result = await self.session.exec(query)
        return result.one_or_none()

    async def find_one_by(self, id: IDType, params: BaseQueryEngineParams | None = None) -> ModelType | None:
        """
        Get a single record by ID.

        Args:
            id (IDType): The id of the record to retrieve

        Returns:
            ModelType | None: The found record or None
        """

        result: ModelType | None = None

        if id and not params:
            query = select(self.model).where(col(self.model.id) == id)  # type: ignore
            result = (await self.session.exec(query)).one_or_none()
        elif id and params:
            params.filters = params.filters or {}
            params.filters["id"] = id

            result = await self.query(params=params)

        return result

    async def get_or_404(self, id: IDType, params: BaseQueryEngineParams | None = None) -> ModelType:
        """
        Get a record by ID or raise a 404 error.

        Args:
            id: The UUID of the record to retrieve

        Returns:
            The found record

        Raises:
            DBError: If the record is not found
        """
        try:
            obj = await self.find_one_by(id, params)
            if not obj:
                raise EntityNotFoundError(metadata={"id": id})
            return obj
        except EntityNotFoundError as enf:
            raise errors.DatabaseError(
                detail=enf.detail,
                metadata=call(enf, "metadata") or {"id": id},
            )

    async def create(self, schema: CreateSchemaType) -> ModelType:
        """
        Create a new record.

        Args:
            schema: The data to create the record with

        Returns:
            The created record
        """
        db_obj = self.model(**schema.model_dump())

        if hasattr(db_obj, "save_friendly_fields"):
            call(db_obj, "save_friendly_fields")

        if hasattr(db_obj, "save_order_tag"):
            call(db_obj, "save_order_tag")

        if hasattr(db_obj, "save_invoice_tag"):
            call(db_obj, "save_invoice_tag")

        self.session.add(db_obj)
        await self._save_changes(refresh_obj=db_obj)
        return db_obj

    async def update(self, id: IDType, schema: UpdateSchemaType | dict[str, Any]) -> ModelType | None:
        """
        Update a record by ID.

        Args:
            id: The id of the record to update
            schema: The data to update the record with

        Returns:
            The updated record or None if not found
        """
        existing_entity = await self.find_one_by(id)

        if not existing_entity:
            return None

        if isinstance(schema, BaseModel):
            schema = schema.model_dump(exclude_unset=True)

        updated_fields = schema
        if not updated_fields:
            return existing_entity

        existing_entity.sqlmodel_update(updated_fields)
        self.session.add(existing_entity)
        await self._save_changes(refresh_obj=existing_entity)
        return existing_entity

    async def delete(self, id: IDType) -> bool:
        """
        Delete a record by ID.

        Args:
            id: The id of the record to delete

        Returns:
            True if the record was deleted, False if not found
        """
        query = select(self.model).where(col(self.model.id) == id)  # type: ignore
        result = (await self.session.exec(query)).one_or_none()

        if not result:
            return False

        await self.session.delete(result)
        await self._save_changes()
        return True

    async def exists(self, id: IDType) -> bool:
        """
        Check if a record exists by ID.

        Args:
            id: The id of the record to check

        Returns:
            bool: True if the record exists, False otherwise
        """
        query = select(self.model).where(col(self.model.id) == id)  # type: ignore
        result = await self.session.exec(query)
        return result.one_or_none() is not None

    async def exists_one(self) -> ModelType | None:
        """
        Check if at least one record exists.

        Returns:
            bool: True if at least one record exists, False otherwise
        """
        query = select(self.model)
        result = await self.session.exec(query)
        return result.first()

    async def query(self, *, params: BaseQueryEngineParams) -> ModelType:
        """
        Query for a single entity.

        Args:
            filters (dict[str, Any] | None): Dictionary of filter conditions
            fields (str | None): Comma-separated string of fields to select or "*" for all fields
            include (list[str] | None): List of relationships to include
            order_by (list[str] | None): List of fields to order by

        Returns:
            ModelType: Single entity or None if not found
        """

        try:
            return await self.query_engine.query(
                filters=params.filters, fields=params.fields, include=params.include, order_by=params.order_by
            )
        except QueryEngineError as qe:
            raise errors.DatabaseError(
                message="Failed to execute query",
                detail="An error occurred while executing the query.",
            ) from qe
        except SQLAlchemyError as e:
            raise errors.DatabaseError(
                message="Failed to execute query",
                detail="An error occurred while executing the query.",
            ) from e

    async def query_all(self, *, params: BaseQueryEngineParams) -> list[ModelType]:
        """
        Query for multiple entities.

        Args:
            filters (dict[str, Any] | None): Dictionary of filter conditions
            fields (str | None): Comma-separated string of fields to select or "*" for all fields
            include (list[str] | None): List of relationships to include
            order_by (list[str] | None): List of fields to order by

        Returns:
            list[ModelType]: List of entities matching the query
        """

        try:
            return await self.query_engine.query_all(
                filters=params.filters, fields=params.fields, include=params.include, order_by=params.order_by
            )
        except QueryEngineError as qe:
            raise errors.DatabaseError(
                message="Failed to execute query",
                detail="An error occurred while executing the query.",
            ) from qe
        except SQLAlchemyError as e:
            raise errors.DatabaseError(
                message="Failed to execute query",
                detail="An error occurred while executing the query.",
            ) from e

    async def execute_raw(self, query: str, params: dict[str, Any] | None = None) -> Any:
        """
        Execute a raw SQL query.

        Args:
            query (str): The raw SQL query to execute

        Returns:
            Any: The result of the query execution
        """

        try:
            result = await self.session.exec(query, params=params or {})  # type: ignore
            return result
        except SQLAlchemyError as e:
            raise errors.DatabaseError(
                message="Failed to execute raw query",
                detail="An error occurred while executing the raw query.",
                metadata={"query": query, "params": params},
            ) from e
