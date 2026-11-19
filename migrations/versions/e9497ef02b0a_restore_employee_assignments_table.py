"""restore employee assignments table"""

from alembic import op
import sqlalchemy as sa

revision = "e9497ef02b0a"
down_revision = "95d6f6a48ce0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "employee_assignments" not in inspector.get_table_names():
        op.create_table(
            "employee_assignments",
            sa.Column("assignment_id", sa.String(10), nullable=False),
            sa.Column("employee_id", sa.String(10), nullable=False),
            sa.Column("effective_from", sa.Date(), nullable=False),
            sa.Column("effective_to", sa.Date(), nullable=True),
            sa.Column("department_id", sa.String(10), nullable=False),
            sa.Column("role_id", sa.String(10), nullable=False),
            sa.Column("job_level", sa.Integer(), nullable=False),
            sa.Column("manager_id", sa.String(10), nullable=True),
            sa.Column("change_reason", sa.String(300), nullable=True),
            sa.ForeignKeyConstraint(["department_id"], ["departments.department_id"]),
            sa.ForeignKeyConstraint(["employee_id"], ["employees.emp_id"]),
            sa.ForeignKeyConstraint(["manager_id"], ["employees.emp_id"]),
            sa.ForeignKeyConstraint(["role_id"], ["roles.role_id"]),
            sa.PrimaryKeyConstraint("assignment_id"),
        )

        op.create_index(
            "ix_employee_assignments_manager_id",
            "employee_assignments",
            ["manager_id"],
        )
        op.create_index(
            "ix_employee_assignments_employee_id",
            "employee_assignments",
            ["employee_id"],
        )
        op.create_index(
            "ix_employee_assignments_department_id",
            "employee_assignments",
            ["department_id"],
        )
        op.create_index(
            "ix_assignment_employee_dates",
            "employee_assignments",
            ["employee_id", "effective_from", "effective_to"],
        )


def downgrade() -> None:
    # Keep the table and its data intact.
    pass