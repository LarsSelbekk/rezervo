"""cal token

Revision ID: 13376b9e08a8
Revises: 9936e1c8eab5
Create Date: 2023-06-10 11:04:37.357533

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session

from sit_rezervo.models import User
from sit_rezervo.utils.ical_utils import generate_calendar_token

# revision identifiers, used by Alembic.
revision = '13376b9e08a8'
down_revision = '9936e1c8eab5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('cal_token', sa.String(), nullable=True))
    session = Session(bind=op.get_bind())
    for user in session.query(User):
        user.cal_token = generate_calendar_token()
    session.commit()
    op.alter_column('users', 'cal_token', nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'cal_token')
    # ### end Alembic commands ###
