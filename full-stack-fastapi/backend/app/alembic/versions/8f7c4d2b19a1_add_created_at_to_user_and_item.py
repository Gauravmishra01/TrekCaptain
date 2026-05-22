"""Add created_at to user and item

Revision ID: 8f7c4d2b19a1
Revises: 1a31ce608336
Create Date: 2026-05-22 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8f7c4d2b19a1"
down_revision = "1a31ce608336"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "item",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.execute('UPDATE "user" SET created_at = NOW() WHERE created_at IS NULL')
    op.execute('UPDATE item SET created_at = NOW() WHERE created_at IS NULL')

    op.alter_column("user", "created_at", nullable=False)
    op.alter_column("item", "created_at", nullable=False)


def downgrade():
    op.drop_column("item", "created_at")
    op.drop_column("user", "created_at")
