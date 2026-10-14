"""ppa-8: wallets, transactions e idempotency_keys

Revision ID: 0002_wallet_tables
Revises: 0001_create_users_and_sessions
Create Date: 2026-10-14
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_wallet_tables"  # <= 32 caracteres (límite de alembic_version.version_num)
down_revision = "0001_create_users_and_sessions"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "wallets",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("balance", sa.Numeric(15, 2), server_default="0.00", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("balance >= 0", name="ck_wallets_balance_non_negative"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_wallets_user_id"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_wallets_user_id"),
    )
    op.create_table(
        "transactions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "type", sa.Enum("transferencia", "recarga", name="transaction_type"), nullable=False
        ),
        sa.Column(
            "status", sa.Enum("exitosa", "rechazada", name="transaction_status"), nullable=False
        ),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("sender_wallet_id", sa.BigInteger(), nullable=True),
        sa.Column("receiver_wallet_id", sa.BigInteger(), nullable=False),
        sa.Column("rejection_reason", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
        sa.ForeignKeyConstraint(
            ["sender_wallet_id"], ["wallets.id"], name="fk_transactions_sender_wallet"
        ),
        sa.ForeignKeyConstraint(
            ["receiver_wallet_id"], ["wallets.id"], name="fk_transactions_receiver_wallet"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_transactions_receiver_created", "transactions", ["receiver_wallet_id", "created_at"]
    )
    op.create_index(
        "ix_transactions_sender_created", "transactions", ["sender_wallet_id", "created_at"]
    )
    op.create_table(
        "idempotency_keys",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("key", sa.String(36), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("status_code", sa.SmallInteger(), nullable=False),
        sa.Column("response_body", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "key"),
    )


def downgrade():
    op.drop_table("idempotency_keys")
    op.drop_index("ix_transactions_sender_created", table_name="transactions")
    op.drop_index("ix_transactions_receiver_created", table_name="transactions")
    op.drop_table("transactions")
    op.drop_table("wallets")
