"""User repository for database operations."""

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import select

from app.auth.models import User
from app.infra.database.repository import Repository


class UserRepository(Repository[User]):
    """Repository for User operations."""

    model_class = User

    async def get_by_email(self, email: str) -> User | None:
        """
        Get a user by their email address.

        Args:
            email: The email address to lookup

        Returns:
            User if found, None otherwise
        """
        return await self.find_one_by_attributes(email=email)

    async def get_by_id(self, user_id: UUID) -> User | None:
        """
        Get a user by their ID.

        Args:
            user_id: The UUID of the user

        Returns:
            User if found, None otherwise
        """
        return await super().get_by_id(user_id)

    async def find_by_name(self, name_query: str) -> Sequence[User]:
        """
        Search for users by their name (partial match).

        Args:
            name_query: The name or part of name to search for

        Returns:
            Sequence of users matching the query
        """
        query = select(User).where(User.full_name.ilike(f"%{name_query}%"))
        result = await self.session.execute(query)
        return result.scalars().all()

    async def find_active_users(self) -> Sequence[User]:
        """
        Get all active users.

        Returns:
            Sequence of active users
        """
        return await self.find_by_attributes(is_active=True)

    async def find_verified_users(self) -> Sequence[User]:
        """
        Get all verified users.

        Returns:
            Sequence of verified users
        """
        return await self.find_by_attributes(is_verified=True)

    async def find_superusers(self) -> Sequence[User]:
        """
        Get all superusers.

        Returns:
            Sequence of superusers
        """
        return await self.find_by_attributes(is_superuser=True)

    async def find_locked_users(self) -> Sequence[User]:
        """
        Get all currently locked users.

        Returns:
            Sequence of users with accounts locked
        """
        query = select(User).where(User.locked_until.isnot(None))
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_login_status(self, user_id: UUID, login_successful: bool) -> User | None:
        """
        Update user login status, tracking successful logins or failed attempts.

        Args:
            user_id: User ID
            login_successful: Whether the login was successful

        Returns:
            Updated user or None if user not found
        """
        user = await self.get_by_id(user_id)
        if not user:
            return None

        # Update based on login success or failure
        if login_successful:
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login = datetime.now()
        else:
            user.failed_login_attempts += 1

        return await self.update(user)
