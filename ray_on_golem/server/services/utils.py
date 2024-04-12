from datetime import datetime, timezone
from typing import List


class WarningMessagesMixin:
    def __init__(self) -> None:
        self._service_warnings = []

    def get_warning_messages(self) -> List[str]:
        return self._service_warnings

    def add_warning_message(self, warning: str, add_timestamp: bool = True) -> None:
        if add_timestamp:
            warning = f"{datetime.now(timezone.utc).isoformat()} {warning}"
        self._service_warnings.append(warning)

    def clear_warning_messages(self):
        self._service_warnings.clear()
