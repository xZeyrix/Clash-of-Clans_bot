from .admin import router as admin_router
from .user import router as user_router
from .beta import router as beta_router

__all__ = ["admin_router", "user_router", "beta_router"]