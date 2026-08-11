"""player_visible flags on shareable entities

Revision ID: 009
Revises: 008
Create Date: 2026-08-11
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "campaigns",
        sa.Column("player_visible", sa.Boolean(), server_default="0", nullable=False),
    )
    op.add_column(
        "npcs",
        sa.Column("player_visible", sa.Boolean(), server_default="0", nullable=False),
    )
    op.add_column(
        "locations",
        sa.Column("player_visible", sa.Boolean(), server_default="0", nullable=False),
    )
    op.add_column(
        "character_graphs",
        sa.Column("player_visible", sa.Boolean(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("character_graphs", "player_visible")
    op.drop_column("locations", "player_visible")
    op.drop_column("npcs", "player_visible")
    op.drop_column("campaigns", "player_visible")
