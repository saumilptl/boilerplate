"""User manager with password security features."""

import datetime
import uuid
from typing import Any, ClassVar

from fastapi import HTTPException, Request, Response
from fastapi_users import BaseUserManager, UUIDIDMixin

from app.auth.models import User
from app.infra.monitoring.logging.logger import logger


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """User management with password security features."""

    def __init__(
        self,
        user_db,
        password_helper=None,
    ):
        super().__init__(user_db, password_helper)

    # Track failed login attempts
    _failed_login_attempts: ClassVar[dict[str, dict[str, Any]]] = {}

    async def validate_password(self, password: str, user: User | None = None) -> None:  # noqa: ARG002
        """Validate password strength."""
        if len(password) < 12:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 12 characters",
            )

        # Check for at least one uppercase, one lowercase, one digit and one special char
        if not any(c.isupper() for c in password):
            raise HTTPException(
                status_code=400,
                detail="Password must contain at least one uppercase letter",
            )

        if not any(c.islower() for c in password):
            raise HTTPException(
                status_code=400,
                detail="Password must contain at least one lowercase letter",
            )

        if not any(c.isdigit() for c in password):
            raise HTTPException(status_code=400, detail="Password must contain at least one number")

        if not any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?/`~" for c in password):
            raise HTTPException(
                status_code=400,
                detail="Password must contain at least one special character",
            )

    async def on_after_register(self, user: User, request: Request | None = None) -> None:  # noqa: ARG002
        logger.info(f"User {user.id} registered")

    async def on_after_forgot_password(self, user: User, token: str, request: Request | None = None) -> None:  # noqa: ARG002
        logger.info(f"User {user.id} forgot password. Reset token generated.")

    async def on_after_request_verify(self, user: User, token: str, request: Request | None = None) -> None:  # noqa: ARG002
        logger.info("Verification requested for user %s. Verification token generated.", user.id)

    async def on_after_login(
        self,
        user: User,
        request: Request | None = None,  # noqa: ARG002
        response: Response | None = None,  # noqa: ARG002
    ) -> None:
        # Clear failed login attempts on successful login
        if user.email in self._failed_login_attempts:
            del self._failed_login_attempts[user.email]

        # Get current UTC time and convert to naive datetime
        now_utc = datetime.datetime.now(datetime.UTC)
        naive_now = now_utc.replace(tzinfo=None)

        # Update last login time
        update_dict = {
            "last_login": naive_now,
            "failed_login_attempts": 0,
            "locked_until": None,
        }
        await self.user_db.update(user, update_dict)

        logger.info(f"User {user.id} logged in successfully")

    async def on_before_login(
        self,
        user: User | None,
        password: str | None,
        request: Request | None = None,  # noqa: ARG002
    ) -> None:
        """Check user status before login."""
        if not user:
            # For security, we still proceed but will fail verification later
            return

        # Check if account is temporarily locked
        if user.locked_until and datetime.datetime.now(datetime.UTC) < user.locked_until:
            remaining = (user.locked_until - datetime.datetime.now(datetime.UTC)).seconds / 60
            logger.warning(f"Locked account login attempt for {user.email}")
            raise HTTPException(
                status_code=403,
                detail=f"Account temporarily locked. Try again in {int(remaining)} minutes.",
            )

        # Track failed login attempts
        if password is not None:
            email = user.email
            current_time = datetime.datetime.now(datetime.UTC)

            # Initialize tracking for this user if not exists
            if email not in self._failed_login_attempts:
                self._failed_login_attempts[email] = {
                    "count": 0,
                    "first_attempt": current_time,
                    "last_attempt": current_time,
                }

            # Reset counter if it's been more than 30 minutes since first attempt
            time_diff = (current_time - self._failed_login_attempts[email]["first_attempt"]).total_seconds() / 60
            if time_diff > 30:
                self._failed_login_attempts[email] = {
                    "count": 0,
                    "first_attempt": current_time,
                    "last_attempt": current_time,
                }

            # Update last attempt time
            self._failed_login_attempts[email]["last_attempt"] = current_time
