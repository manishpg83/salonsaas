"""Provider interface for outbound messages (CLAUDE.md §7 Phase 8.1).

`ConsoleProvider` is the only implementation for now — it logs/prints
instead of calling a real API, so the whole module is testable without a
WhatsApp Business account. Swapping to the real WhatsApp Cloud API provider
later is a `MESSAGING_PROVIDER` setting change, not a change at any call
site (they all go through `get_provider()` / `apps.messaging.services`).
"""
import logging
from abc import ABC, abstractmethod

from django.conf import settings

logger = logging.getLogger("apps.messaging")


class BaseProvider(ABC):
    @abstractmethod
    def send(self, to: str, body: str) -> bool:
        """Send `body` to `to`. Returns True on success, False on failure —
        never raises for an ordinary send failure, so callers can log a
        FAILED Message instead of crashing the request."""


class ConsoleProvider(BaseProvider):
    def send(self, to: str, body: str) -> bool:
        logger.info("[ConsoleProvider] WhatsApp -> %s: %s", to, body)
        print(f"[WhatsApp:Console] To {to}: {body}")
        return True


PROVIDERS = {
    "console": ConsoleProvider,
}


def get_provider() -> BaseProvider:
    name = getattr(settings, "MESSAGING_PROVIDER", "console")
    provider_cls = PROVIDERS.get(name, ConsoleProvider)
    return provider_cls()
