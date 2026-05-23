from enum import StrEnum


class ServiceStatus(StrEnum):
    """Valid status values for any service output schema.

    Attributes:
        OK: The service completed successfully and data is populated.
        ERROR: The service encountered an exception and error_message is populated.
    """

    OK = "OK"
    ERROR = "ERROR"
