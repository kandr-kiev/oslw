"""OSLW Cron Scheduler — manages scheduled jobs.

Cron scheduler with:
- Job registration
- Interval-based scheduling
- Manual execution
- Logging
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class CronJob:
    """Represents a single cron job."""

    def __init__(
        self,
        name: str,
        func: Callable,
        interval: int = 3600,  # seconds
        enabled: bool = True,
        **kwargs: Any,
    ):
        self.name = name
        self.func = func
        self.interval = interval
        self.enabled = enabled
        self.kwargs = kwargs
        self.last_run: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self.run_count: int = 0

    async def execute(self) -> dict:
        """Execute the job and return status."""
        if not self.enabled:
            return {"status": "disabled", "name": self.name}

        try:
            self.last_run = datetime.now()
            self.run_count += 1
            result = await self.func(**self.kwargs) if asyncio.iscoroutinefunction(self.func) else self.func(**self.kwargs)
            self.last_error = None
            return {
                "status": "success",
                "name": self.name,
                "last_run": self.last_run.isoformat(),
                "last_error": None,
                "run_count": self.run_count,
                "result": result,
            }
        except Exception as e:
            self.last_error = str(e)
            self.last_run = datetime.now()
            self.run_count += 1
            logger.error(f"Cron job '{self.name}' failed: {e}")
            return {
                "status": "error",
                "name": self.name,
                "last_run": self.last_run.isoformat(),
                "last_error": str(e),
                "run_count": self.run_count,
                "error": str(e),
            }


class CronScheduler:
    """Manages scheduled cron jobs."""

    def __init__(self):
        self.jobs: dict[str, CronJob] = {}
        self.running = False
        self._task: Optional[asyncio.Task] = None

    def register(
        self,
        name: str,
        func: Callable,
        interval: int = 3600,
        enabled: bool = True,
        **kwargs: Any,
    ) -> CronJob:
        """Register a new cron job."""
        job = CronJob(name, func, interval, enabled, **kwargs)
        self.jobs[name] = job
        logger.info(f"Registered cron job: {name} (every {interval}s)")
        return job

    def unregister(self, name: str) -> bool:
        """Unregister a cron job."""
        if name in self.jobs:
            del self.jobs[name]
            logger.info(f"Unregistered cron job: {name}")
            return True
        return False

    def get_job(self, name: str) -> Optional[CronJob]:
        """Get a cron job by name."""
        return self.jobs.get(name)

    def list_jobs(self) -> list[dict]:
        """List all registered jobs."""
        return [
            {
                "name": job.name,
                "enabled": job.enabled,
                "interval": job.interval,
                "last_run": job.last_run.isoformat() if job.last_run else None,
                "run_count": job.run_count,
                "last_error": job.last_error,
            }
            for job in self.jobs.values()
        ]

    async def run_job(self, name: str) -> dict:
        """Run a specific job."""
        job = self.jobs.get(name)
        if not job:
            return {"status": "not_found", "name": name}
        return await job.execute()

    async def run_all(self) -> list[dict]:
        """Run all enabled jobs."""
        results = []
        for name, job in self.jobs.items():
            if job.enabled:
                result = await job.execute()
                results.append(result)
        return results

    async def _loop(self):
        """Main scheduling loop."""
        logger.info("Cron scheduler started")
        while self.running:
            now = datetime.now()
            for name, job in self.jobs.items():
                if (
                    job.enabled
                    and job.last_run is None
                    or (now - job.last_run) >= timedelta(seconds=job.interval)
                ):
                    await job.execute()
            await asyncio.sleep(1)  # Check every second

    async def start(self):
        """Start the scheduler."""
        if self.running:
            return
        self.running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("Cron scheduler started")

    async def stop(self):
        """Stop the scheduler."""
        if not self.running:
            return
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Cron scheduler stopped")
