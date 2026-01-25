"""Domain module - Contains entities and interfaces"""
from .entities import User
from .interfaces import IUserRepository, IFaceService

__all__ = ["User", "IUserRepository", "IFaceService"]
