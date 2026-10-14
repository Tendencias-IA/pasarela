"""PPA-1: perfil de registro después de las tablas compartidas de HU-08."""

import sqlalchemy as sa
from alembic import op

revision = "0003_users_registration"
down_revision = "0002_wallet_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("full_name", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("national_id", sa.String(20), nullable=True))
    op.add_column("users", sa.Column("email", sa.String(254), nullable=True))
    op.create_unique_constraint("uq_users_national_id", "users", ["national_id"])
    op.create_unique_constraint("uq_users_email", "users", ["email"])


def downgrade() -> None:
    op.drop_constraint("uq_users_email", "users", type_="unique")
    op.drop_constraint("uq_users_national_id", "users", type_="unique")
    op.drop_column("users", "email")
    op.drop_column("users", "national_id")
    op.drop_column("users", "full_name")
