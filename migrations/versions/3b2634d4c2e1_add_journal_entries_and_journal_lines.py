"""add journal entries and journal lines

Revision ID: 3b2634d4c2e1
Revises: cc5b6062a26e
"""

from alembic import op
import sqlalchemy as sa

revision = "3b2634d4c2e1"
down_revision = "cc5b6062a26e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "journal_entries",
        sa.Column("entry_id", sa.String(30), primary_key=True),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("source_type", sa.String(30), nullable=False),
        sa.Column("source_id", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("total_debit", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_credit", sa.Numeric(14, 2), nullable=False),
        sa.Column("created_by", sa.String(20), nullable=False),
    )

    op.create_index(
        "ix_journal_entries_source",
        "journal_entries",
        ["source_type", "source_id"],
        unique=True,
    )

    op.create_table(
        "journal_lines",
        sa.Column("line_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "entry_id",
            sa.String(30),
            sa.ForeignKey("journal_entries.entry_id"),
            nullable=False,
        ),
        sa.Column("line_no", sa.Integer(), nullable=False),
        sa.Column("account_code", sa.String(20), nullable=False),
        sa.Column("debit", sa.Numeric(14, 2), nullable=False),
        sa.Column("credit", sa.Numeric(14, 2), nullable=False),
        sa.Column("line_description", sa.String(300)),
    )

    op.create_index("ix_journal_lines_entry_id", "journal_lines", ["entry_id"])


def downgrade():
    op.drop_index("ix_journal_lines_entry_id", table_name="journal_lines")
    op.drop_table("journal_lines")
    op.drop_index("ix_journal_entries_source", table_name="journal_entries")
    op.drop_table("journal_entries")