"""PPA-1 extend users and create wallets.

Revision ID: 0002_users_wallets
Revises: 0001_create_users_and_sessions
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_users_wallets"
down_revision = "0001_create_users_and_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable at storage level so users created by the earlier login work remain
    # migratable. HU-01's request schema requires all three values for new accounts.
    op.add_column("users", sa.Column("full_name", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("national_id", sa.String(length=20), nullable=True))
    op.add_column("users", sa.Column("email", sa.String(length=254), nullable=True))
    op.create_unique_constraint("uq_users_national_id", "users", ["national_id"])
    op.create_unique_constraint("uq_users_email", "users", ["email"])
    op.create_table(
        "wallets",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("balance", sa.Numeric(15, 2), server_default="0.00", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("UTC_TIMESTAMP()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("UTC_TIMESTAMP()"), nullable=False
        ),
        sa.CheckConstraint("balance >= 0", name="ck_wallets_balance_nonnegative"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_wallets_user_id_users", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_wallets"),
        sa.UniqueConstraint("user_id", name="uq_wallets_user_id"),
    )


def downgrade() -> None:
    op.drop_table("wallets")
    op.drop_constraint("uq_users_email", "users", type_="unique")
    op.drop_constraint("uq_users_national_id", "users", type_="unique")
    op.drop_column("users", "email")
    op.drop_column("users", "national_id")
    op.drop_column("users", "full_name")
