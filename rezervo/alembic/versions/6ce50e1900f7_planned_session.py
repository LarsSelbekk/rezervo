"""planned session

Revision ID: 6ce50e1900f7
Revises: 13376b9e08a8
Create Date: 2023-06-10 11:29:16.207400

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "6ce50e1900f7"
down_revision = "13376b9e08a8"
branch_labels = None
depends_on = None

original_session_status_enum = sa.Enum(
    "CONFIRMED", "BOOKED", "WAITLIST", "UNKNOWN", name="sessionstate"
)


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("ALTER TYPE sessionstate ADD VALUE 'PLANNED'")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("ALTER TYPE sessionstate RENAME TO sessionstate_old")
    original_session_status_enum.create(op.get_bind())
    op.execute(
        (
            "ALTER TABLE sessions ALTER COLUMN status \
            TYPE sessionstate USING \
            case WHEN status = 'PLANNED' THEN 'UNKNOWN'::sessionstate \
            ELSE status::text::sessionstate END"
        )
    )
    op.execute("DROP TYPE sessionstate_old")
    # ### end Alembic commands ###
