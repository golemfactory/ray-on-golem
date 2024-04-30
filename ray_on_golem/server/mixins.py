from datetime import datetime, timezone
from typing import Sequence


class WarningMessagesMixin:
    """Mixin for collecting warning messages to display by `ray-on-golem status` command."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._warning_messages = []

    def get_warning_messages(self) -> Sequence[str]:
        """Get read-only collection of warnings."""

        return self._warning_messages

    def add_warning_message(self, message: str, *args, add_timestamp: bool = True) -> None:
        """Add warning to the collection.

        Positional arguments are used to format with %s-style the warning message."""

        message = message % args

        if add_timestamp:
            message = f"{datetime.now(timezone.utc).isoformat()} {message}"

        self._warning_messages.append(message)

    def clear_warning_messages(self) -> None:
        """Clear all collected warnings."""

        self._warning_messages.clear()
