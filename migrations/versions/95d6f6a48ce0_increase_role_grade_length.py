"""increase role grade length"""

from alembic import op
import sqlalchemy as sa

revision = "95d6f6a48ce0"
down_revision = "e6b50935a899"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("roles") as batch_op:
        batch_op.alter_column(
            "grade",
            existing_type=sa.String(length=20),
            type_=sa.String(length=100),
            existing_nullable=False,
        )


def downgrade():
    with op.batch_alter_table("roles") as batch_op:
        batch_op.alter_column(
            "grade",
            existing_type=sa.String(length=100),
            type_=sa.String(length=20),
            existing_nullable=False,
        )