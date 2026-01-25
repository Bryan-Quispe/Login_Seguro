"""Presentation routes module"""
from .auth_routes import router as auth_router
from .face_routes import router as face_router

__all__ = ["auth_router", "face_router"]
