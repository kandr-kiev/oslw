"""Tests for cron job functions.

Tests that each job function returns correct structure
and handles errors gracefully.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestDoctorJob:
    """Test doctor_job function."""

    @patch('oslw.cron.jobs.QualityService')
    def test_doctor_job_success(self, mock_quality_svc):
        """Test successful doctor job execution."""
        from oslw.cron.jobs import doctor_job

        mock_service = MagicMock()
        mock_result = MagicMock()
        mock_result.issues = []
        mock_service.diagnose.return_value = mock_result
        mock_quality_svc.return_value = mock_service

        result = doctor_job(wiki_root="/tmp/fake_wiki")

        assert result["status"] == "success"
        assert result["total_issues"] == 0
        mock_service.diagnose.assert_called_once_with(layer="all")

    @patch('oslw.cron.jobs.QualityService')
    def test_doctor_job_with_issues(self, mock_quality_svc):
        """Test doctor job with issues found."""
        from oslw.cron.jobs import doctor_job

        mock_service = MagicMock()
        mock_result = MagicMock()

        class Issue:
            severity = "critical"

        mock_result.issues = [Issue(), Issue()]
        mock_service.diagnose.return_value = mock_result
        mock_quality_svc.return_value = mock_service

        result = doctor_job(wiki_root="/tmp/fake_wiki")

        assert result["status"] == "success"
        assert result["total_issues"] == 2
        assert result["critical"] == 2

    @patch('oslw.cron.jobs.QualityService')
    def test_doctor_job_error(self, mock_quality_svc):
        """Test doctor job handles errors gracefully."""
        from oslw.cron.jobs import doctor_job

        mock_quality_svc.side_effect = Exception("DB not found")

        result = doctor_job(wiki_root="/tmp/fake_wiki")

        assert result["status"] == "error"
        assert "DB not found" in result["error"]


class TestGraphJob:
    """Test graph_job function."""

    @patch('oslw.cron.jobs.GraphService')
    def test_graph_job_success(self, mock_graph_svc):
        """Test successful graph job execution."""
        from oslw.cron.jobs import graph_job

        mock_service = MagicMock()
        mock_service.generate_graph.return_value = {
            "total_nodes": 42,
            "total_edges": 120,
            "status": "success",
        }
        mock_graph_svc.return_value = mock_service

        result = graph_job(wiki_root="/tmp/fake_wiki")

        assert result["total_nodes"] == 42
        assert result["total_edges"] == 120
        assert result["status"] == "success"

    @patch('oslw.cron.jobs.GraphService')
    def test_graph_job_error(self, mock_graph_svc):
        """Test graph job handles errors gracefully."""
        from oslw.cron.jobs import graph_job

        mock_graph_svc.side_effect = Exception("Graph failed")

        result = graph_job(wiki_root="/tmp/fake_wiki")

        assert result["status"] == "error"
        assert "Graph failed" in result["error"]


class TestDigestJob:
    """Test digest_job function."""

    @patch('oslw.cron.jobs.DigestService')
    def test_digest_job_success(self, mock_digest_svc):
        """Test successful digest job execution."""
        from oslw.cron.jobs import digest_job

        mock_service = MagicMock()
        mock_service.generate_digest.return_value = []
        mock_svc_instance = MagicMock()
        mock_svc_instance.generate_digest.return_value = []
        mock_svc_instance.get_digest_summary.return_value = MagicMock(
            total_entries=5, by_type={"article": 3, "comparison": 2}
        )
        mock_digest_svc.return_value = mock_svc_instance

        result = digest_job(wiki_root="/tmp/fake_wiki", hours=12, format="markdown")

        assert result["status"] == "success"
        assert result["entries"] == 0

    @patch('oslw.cron.jobs.DigestService')
    def test_digest_job_error(self, mock_digest_svc):
        """Test digest job handles errors gracefully."""
        from oslw.cron.jobs import digest_job

        mock_digest_svc.side_effect = Exception("Digest failed")

        result = digest_job(wiki_root="/tmp/fake_wiki")

        assert result["status"] == "error"
        assert "Digest failed" in result["error"]


class TestSourcesJob:
    """Test sources_job function."""

    @patch('oslw.cron.jobs.SourceService')
    def test_sources_job_success(self, mock_source_svc):
        """Test successful sources job execution."""
        from oslw.cron.jobs import sources_job

        mock_service = MagicMock()
        mock_service.monitor_sources.return_value = {
            "rss1": {"status": "ok", "updated": 3},
        }
        mock_source_svc.return_value = mock_service

        result = sources_job(wiki_root="/tmp/fake_wiki")

        assert result["status"] == "success"
        assert len(result["results"]) == 1
        mock_service.monitor_sources.assert_called_once()

    @patch('oslw.cron.jobs.SourceService')
    def test_sources_job_with_source_name(self, mock_source_svc):
        """Test sources job with specific source."""
        from oslw.cron.jobs import sources_job

        mock_service = MagicMock()
        mock_service.monitor_sources.return_value = {}
        mock_source_svc.return_value = mock_service

        sources_job(wiki_root="/tmp/fake_wiki", source_name="github")

        mock_service.monitor_sources.assert_called_once()

    @patch('oslw.cron.jobs.SourceService')
    def test_sources_job_error(self, mock_source_svc):
        """Test sources job handles errors gracefully."""
        from oslw.cron.jobs import sources_job

        mock_source_svc.side_effect = Exception("Network error")

        result = sources_job(wiki_root="/tmp/fake_wiki")

        assert result["status"] == "error"
        assert "Network error" in result["error"]


class TestQualityJob:
    """Test quality_job function."""

    @patch('oslw.cron.jobs.QualityService')
    def test_quality_job_success(self, mock_quality_svc):
        """Test successful quality job execution."""
        from oslw.cron.jobs import quality_job

        mock_service = MagicMock()
        mock_service.run_full_audit.return_value = {
            "diagnosis": {"issues": [{"severity": "critical"}] * 5},
            "status": "success",
        }
        mock_quality_svc.return_value = mock_service

        result = quality_job(wiki_root="/tmp/fake_wiki")

        assert result["status"] == "success"
        assert len(result.get("diagnosis", {}).get("issues", [])) == 5

    @patch('oslw.cron.jobs.QualityService')
    def test_quality_job_error(self, mock_quality_svc):
        """Test quality job handles errors gracefully."""
        from oslw.cron.jobs import quality_job

        mock_quality_svc.side_effect = Exception("Lint failed")

        result = quality_job(wiki_root="/tmp/fake_wiki")

        assert result["status"] == "error"
        assert "Lint failed" in result["error"]


class TestIndexJob:
    """Test index_job function."""

    @patch('oslw.cron.jobs.IndexService')
    def test_index_job_success(self, mock_index_svc):
        """Test successful index job execution."""
        from oslw.cron.jobs import index_job

        mock_service = MagicMock()
        mock_service.rebuild_index.return_value = 150
        mock_index_svc.return_value = mock_service

        result = index_job(wiki_root="/tmp/fake_wiki")

        assert result["status"] == "success"
        assert result["total_pages"] == 150

    @patch('oslw.cron.jobs.IndexService')
    def test_index_job_error(self, mock_index_svc):
        """Test index job handles errors gracefully."""
        from oslw.cron.jobs import index_job

        mock_index_svc.side_effect = Exception("Index failed")

        result = index_job(wiki_root="/tmp/fake_wiki")

        assert result["status"] == "error"
        assert "Index failed" in result["error"]
