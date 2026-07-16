# Import all the models, so that Base has them before being
# imported by Alembic or database initialization scripts
from app.database.base_class import Base  # noqa
from app.models.user import User  # noqa
from app.models.token import RefreshToken  # noqa
from app.models.shipment import Shipment  # noqa
from app.models.route import Route, RouteStop  # noqa
from app.models.status_history import StatusHistory  # noqa
