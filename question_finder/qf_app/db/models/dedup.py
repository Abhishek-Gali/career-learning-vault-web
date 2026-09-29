"""Duplicate clusters and cluster members models."""

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from qf_app.db.models.base import Base, TimestampMixin


class DuplicateCluster(Base, TimestampMixin):
    """Cluster grouping multiple duplicate questions under one canonical record."""

    __tablename__ = "duplicate_clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    canonical_question_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("questions.id", ondelete="SET NULL"), nullable=True)
    cluster_size: Mapped[int] = mapped_column(Integer, default=1)
    selection_reason: Mapped[str] = mapped_column(String(255), default="HIGHEST_QUALITY_SCORE")

    members: Mapped[list["DuplicateMember"]] = relationship("DuplicateMember", back_populates="cluster", cascade="all, delete-orphan")


class DuplicateMember(Base, TimestampMixin):
    """Member question belonging to a duplicate cluster."""

    __tablename__ = "duplicate_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cluster_id: Mapped[int] = mapped_column(Integer, ForeignKey("duplicate_clusters.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    similarity_score: Mapped[float] = mapped_column(Float, default=1.0)
    comparison_method: Mapped[str] = mapped_column(String(50), default="EXACT_HASH")

    cluster: Mapped[DuplicateCluster] = relationship("DuplicateCluster", back_populates="members")
