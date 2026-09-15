class ManagementUserError(Exception):
    """Expected operational user-management failure."""


class BootstrapError(Exception):
    """Initial data cannot be applied safely."""
