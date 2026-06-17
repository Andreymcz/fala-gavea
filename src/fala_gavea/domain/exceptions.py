class DomainError(Exception):
    """Base class for domain errors."""


class ReportNotFoundError(DomainError):
    def __init__(self, id: str) -> None:
        super().__init__(f"Report not found: {id}")
        self.id = id


class InvalidInputError(DomainError):
    pass
