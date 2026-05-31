"""SQLAlchemy repository for delivery assignments."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.assignment_repository import IAssignmentRepository
from src.domain.entities.assignment import AssignmentStatus, DeliveryAssignment
from src.domain.value_objects.location import Location
from src.infrastructure.database.models.assignment_model import DeliveryAssignmentModel


class SqlAlchemyAssignmentRepository(IAssignmentRepository):
    """Persist and query delivery assignments through SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, assignment: DeliveryAssignment) -> DeliveryAssignment:
        """Persist newly created assignment."""
        model = self._entity_to_model(assignment)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._model_to_entity(model)

    async def get_by_id(self, assignment_id: UUID) -> DeliveryAssignment | None:
        """Get assignment by id."""
        model = await self._session.get(DeliveryAssignmentModel, assignment_id)
        if model is None:
            return None
        return self._model_to_entity(model)

    async def get_by_order_id(self, order_id: UUID) -> DeliveryAssignment | None:
        """Get latest assignment by order id."""
        stmt = (
            select(DeliveryAssignmentModel)
            .where(DeliveryAssignmentModel.order_id == order_id)
            .order_by(DeliveryAssignmentModel.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_entity(model)

    async def update(self, assignment: DeliveryAssignment) -> DeliveryAssignment:
        """Persist updated assignment."""
        model = await self._session.get(DeliveryAssignmentModel, assignment.id)
        if model is None:
            raise ValueError(f"assignment '{assignment.id}' not found")

        model.status = assignment.status.value
        model.current_latitude = (
            assignment.current_location.latitude if assignment.current_location else None
        )
        model.current_longitude = (
            assignment.current_location.longitude if assignment.current_location else None
        )
        model.delivered_at = assignment.delivered_at
        model.updated_at = assignment.updated_at
        await self._session.commit()
        await self._session.refresh(model)
        return self._model_to_entity(model)

    @staticmethod
    def _entity_to_model(assignment: DeliveryAssignment) -> DeliveryAssignmentModel:
        """Convert entity to ORM model."""
        location = assignment.current_location
        return DeliveryAssignmentModel(
            id=assignment.id,
            order_id=assignment.order_id,
            restaurant_id=assignment.restaurant_id,
            courier_id=assignment.courier_id,
            status=assignment.status.value,
            current_latitude=location.latitude if location else None,
            current_longitude=location.longitude if location else None,
            delivered_at=assignment.delivered_at,
            created_at=assignment.created_at,
            updated_at=assignment.updated_at,
        )

    @staticmethod
    def _model_to_entity(model: DeliveryAssignmentModel) -> DeliveryAssignment:
        """Convert ORM model to entity."""
        location: Location | None = None
        if model.current_latitude is not None and model.current_longitude is not None:
            location = Location(
                latitude=model.current_latitude,
                longitude=model.current_longitude,
            )
        return DeliveryAssignment(
            id=model.id,
            order_id=model.order_id,
            restaurant_id=model.restaurant_id,
            courier_id=model.courier_id,
            status=AssignmentStatus(model.status),
            current_location=location,
            delivered_at=model.delivered_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
