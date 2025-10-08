"""Test data factories using Polyfactory.

Example usage:
    from tests.helpers.factories import UserFactory

    # Create a user instance
    user = UserFactory.build()

    # Create with custom fields
    user = UserFactory.build(email="custom@example.com")

    # Create multiple instances
    users = UserFactory.batch(5)
"""
