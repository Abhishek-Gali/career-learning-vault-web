"""Integration tests for curriculum snapshots and database storage."""

import pytest
from qf_app.curriculum.snapshot import CurriculumSnapshotManager


@pytest.mark.asyncio
async def test_curriculum_snapshot_refresh(db_session):
    mgr = CurriculumSnapshotManager(db_session)
    snapshot = await mgr.refresh_curriculum(force=True)

    assert snapshot.id is not None
    assert snapshot.exam_code == "CLF-C02"
    assert len(snapshot.domains) == 4

    # Verify domain weightings
    weights = {d.domain_number: d.weighting for d in snapshot.domains}
    assert weights[1] == 0.24
    assert weights[2] == 0.30
    assert weights[3] == 0.34
    assert weights[4] == 0.12
