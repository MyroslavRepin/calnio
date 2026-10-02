import httpx


class HealthcheckRepo:
    """Pings an external dead man's switch, such as healthchecks.io.

    The one failure this process cannot report is the machine going down. The
    switch expects a ping every tick and raises the alarm when they stop.
    """

    def __init__(self, url: str) -> None:
        self.url = url.rstrip("/")
        self.client = httpx.Client(timeout=10.0)

    def ping(self, failed: bool) -> None:
        """Report one tick. /fail alerts at once instead of waiting."""
        url = self.url
        if failed:
            url = f"{self.url}/fail"
        self.client.get(url).raise_for_status()
