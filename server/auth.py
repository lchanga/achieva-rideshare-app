def has_role(user_roles: set[str], required_role: str) -> bool:
    """
    Temporary authorization helper.

    Eventually, this should be replaced with real auth/SSO integration and
    a consistent representation of users/roles.
    """
    return required_role in user_roles

