"""Tests for OSLW Cron Scheduler."""

import asyncio
import pytest
from oslw.cron.scheduler import CronJob, CronScheduler


class TestCronJob:
    """Test CronJob class."""

    @pytest.mark.asyncio
    async def test_cron_job_execute_success(self):
        """Test successful job execution."""
        async def dummy_job():
            return {"status": "ok"}

        job = CronJob("test_job", dummy_job, interval=60)
        result = await job.execute()

        assert result["status"] == "success"
        assert result["name"] == "test_job"
        assert result["run_count"] >= 1
        assert result["last_run"] is not None
        assert result["last_error"] is None

    @pytest.mark.asyncio
    async def test_cron_job_execute_failure(self):
        """Test job execution with error."""
        async def failing_job():
            raise ValueError("Test error")

        job = CronJob("failing_job", failing_job, interval=60)
        result = await job.execute()

        assert result["status"] == "error"
        assert result["run_count"] >= 1
        assert result["last_error"] == "Test error"

    @pytest.mark.asyncio
    async def test_cron_job_disabled(self):
        """Test disabled job."""
        async def dummy_job():
            return {"status": "ok"}

        job = CronJob("disabled_job", dummy_job, interval=60, enabled=False)
        result = await job.execute()

        assert result["status"] == "disabled"

    @pytest.mark.asyncio
    async def test_cron_job_multiple_runs(self):
        """Test job execution multiple times."""
        async def dummy_job():
            return {"status": "ok"}

        job = CronJob("multi_job", dummy_job, interval=60)
        await job.execute()
        await job.execute()
        await job.execute()

        assert job.run_count == 3
        assert job.last_run is not None


class TestCronScheduler:
    """Test CronScheduler class."""

    def test_scheduler_create(self):
        """Test scheduler creation."""
        scheduler = CronScheduler()
        assert scheduler.jobs == {}
        assert scheduler.running is False

    @pytest.mark.asyncio
    async def test_scheduler_register_and_list(self):
        """Test job registration and listing."""
        async def dummy_job():
            return {"status": "ok"}

        scheduler = CronScheduler()
        job = scheduler.register("test_job", dummy_job, interval=120)

        assert job.name == "test_job"
        assert job.interval == 120

        jobs_list = scheduler.list_jobs()
        assert len(jobs_list) == 1
        assert jobs_list[0]["name"] == "test_job"
        assert jobs_list[0]["interval"] == 120

    @pytest.mark.asyncio
    async def test_scheduler_unregister(self):
        """Test job unregistration."""
        async def dummy_job():
            return {"status": "ok"}

        scheduler = CronScheduler()
        scheduler.register("test_job", dummy_job, interval=60)
        assert len(scheduler.jobs) == 1

        result = scheduler.unregister("test_job")
        assert result is True
        assert len(scheduler.jobs) == 0

        result = scheduler.unregister("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_scheduler_get_job(self):
        """Test getting a job by name."""
        async def dummy_job():
            return {"status": "ok"}

        scheduler = CronScheduler()
        job = scheduler.register("test_job", dummy_job, interval=60)

        retrieved = scheduler.get_job("test_job")
        assert retrieved is job

        none_job = scheduler.get_job("nonexistent")
        assert none_job is None

    @pytest.mark.asyncio
    async def test_scheduler_run_specific_job(self):
        """Test running a specific job."""
        async def dummy_job():
            return {"data": "test"}

        scheduler = CronScheduler()
        scheduler.register("test_job", dummy_job, interval=60)

        result = await scheduler.run_job("test_job")
        assert result["status"] == "success"
        assert result["result"]["data"] == "test"

    @pytest.mark.asyncio
    async def test_scheduler_run_nonexistent_job(self):
        """Test running nonexistent job."""
        scheduler = CronScheduler()
        result = await scheduler.run_job("nonexistent")
        assert result["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_scheduler_run_all(self):
        """Test running all jobs."""
        async def job1():
            return {"job": 1}

        async def job2():
            return {"job": 2}

        scheduler = CronScheduler()
        scheduler.register("job1", job1, interval=60)
        scheduler.register("job2", job2, interval=120)
        scheduler.register("disabled_job", job1, interval=60, enabled=False)

        results = await scheduler.run_all()
        assert len(results) == 2  # Only enabled jobs

        statuses = [r["status"] for r in results]
        assert all(s == "success" for s in statuses)

    @pytest.mark.asyncio
    async def test_scheduler_start_stop(self):
        """Test scheduler start and stop."""
        async def dummy_job():
            await asyncio.sleep(0.1)
            return {"status": "ok"}

        scheduler = CronScheduler()
        scheduler.register("test_job", dummy_job, interval=1)

        await scheduler.start()
        assert scheduler.running is True

        await asyncio.sleep(0.3)  # Let loop run at least once

        await scheduler.stop()
        assert scheduler.running is False
