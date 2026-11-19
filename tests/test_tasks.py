from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import app.tasks as tasks


def setup_mock_db(monkeypatch, runs):
    db = MagicMock()
    db.get.side_effect = runs
    monkeypatch.setattr(tasks, "SessionLocal", lambda: db)
    return db


def test_process_bulk_payroll_success(monkeypatch):
    run_ids = [f"RUN-{i}" for i in range(18)]
    runs = [SimpleNamespace(status="DRAFT") for _ in run_ids]
    db = setup_mock_db(monkeypatch, runs)

    process_mock = MagicMock()
    monkeypatch.setattr(tasks, "process_payroll_run", process_mock)

    progress_updates = []
    monkeypatch.setattr(
        tasks.process_bulk_payroll,
        "update_state",
        lambda **kwargs: progress_updates.append(kwargs),
    )

    result = tasks.process_bulk_payroll.run(run_ids)

    assert result == {
        "status": "completed",
        "processed": 18,
        "total": 18,
    }
    assert db.commit.call_count == 18
    assert process_mock.call_count == 18
    assert len(progress_updates) == 18
    assert progress_updates[-1]["meta"]["percent"] == 100.0
    db.close.assert_called_once()


def test_process_bulk_payroll_rejects_wrong_count(monkeypatch):
    db = setup_mock_db(monkeypatch, [])

    with pytest.raises(ValueError, match="Expected exactly 18"):
        tasks.process_bulk_payroll.run(["RUN-1"])

    db.rollback.assert_called_once()
    db.close.assert_called_once()


def test_process_bulk_payroll_rejects_missing_run(monkeypatch):
    run_ids = [f"RUN-{i}" for i in range(18)]
    db = setup_mock_db(monkeypatch, [None])

    with pytest.raises(ValueError, match="missing or not in DRAFT"):
        tasks.process_bulk_payroll.run(run_ids)

    db.rollback.assert_called_once()
    db.close.assert_called_once()


def test_process_bulk_payroll_rejects_non_draft_run(monkeypatch):
    run_ids = [f"RUN-{i}" for i in range(18)]
    runs = [SimpleNamespace(status="PROCESSED")]
    db = setup_mock_db(monkeypatch, runs)

    with pytest.raises(ValueError, match="missing or not in DRAFT"):
        tasks.process_bulk_payroll.run(run_ids)

    db.rollback.assert_called_once()
    db.close.assert_called_once()


def test_process_bulk_payroll_rolls_back_on_processing_error(monkeypatch):
    run_ids = [f"RUN-{i}" for i in range(18)]
    runs = [SimpleNamespace(status="DRAFT")]
    db = setup_mock_db(monkeypatch, runs)

    def raise_error(db_session, run_id):
        raise RuntimeError("Payroll processing failed")

    monkeypatch.setattr(tasks, "process_payroll_run", raise_error)

    with pytest.raises(RuntimeError, match="Payroll processing failed"):
        tasks.process_bulk_payroll.run(run_ids)

    db.rollback.assert_called_once()
    db.close.assert_called_once()
    db.commit.assert_not_called()
