class DomainError(Exception):
    """Base class for domain errors."""


class ReportNotFoundError(DomainError):
    def __init__(self, id: str) -> None:
        super().__init__(f"Report not found: {id}")
        self.id = id


class InvalidInputError(DomainError):
    pass


class UserNotFoundError(DomainError):
    def __init__(self, id: str) -> None:
        super().__init__(f"User not found: {id}")
        self.id = id


class UserAlreadyExistsError(DomainError):
    def __init__(self, email: str) -> None:
        super().__init__(f"User already exists: {email}")
        self.email = email


class ReportTypeNotFoundError(DomainError):
    def __init__(self, id: str) -> None:
        super().__init__(f"ReportType not found: {id}")
        self.id = id


class InvalidCredentialsError(DomainError):
    def __init__(self) -> None:
        super().__init__("Invalid credentials")


class PermissionDeniedError(DomainError):
    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(message)


class ForwardingNotFoundError(DomainError):
    def __init__(self, id: str) -> None:
        super().__init__(f"Forwarding not found: {id}")
        self.id = id


class OllamaUnavailableError(DomainError):
    def __init__(self) -> None:
        super().__init__("NL chat is unavailable in this deployment.")


class SavedFilterNotFoundError(DomainError):
    def __init__(self, id: str) -> None:
        super().__init__(f"SavedFilter not found: {id}")
        self.id = id


class SelfVoteError(DomainError):
    def __init__(self) -> None:
        super().__init__("Users cannot vote on their own content")
