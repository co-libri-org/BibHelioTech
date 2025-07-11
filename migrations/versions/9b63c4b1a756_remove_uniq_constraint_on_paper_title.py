"""Remove uniq constraint on Paper.title

Revision ID: 9b63c4b1a756
Revises: ddb85671ad8b
Create Date: 2025-07-10 17:27:52.035238

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9b63c4b1a756'
down_revision = 'ddb85671ad8b'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        CREATE TABLE paper_new (
            id INTEGER NOT NULL PRIMARY KEY,
            title VARCHAR NOT NULL,
            doi VARCHAR,
            ark VARCHAR,
            istex_id VARCHAR,
            publication_date VARCHAR,
            pdf_path VARCHAR UNIQUE,
            txt_path VARCHAR UNIQUE,
            cat_path VARCHAR UNIQUE,
            cat_in_db BOOLEAN,
            task_id VARCHAR UNIQUE,
            task_status VARCHAR,
            task_started DATETIME,
            task_stopped DATETIME,
            UNIQUE (pdf_path),
            UNIQUE (txt_path),
            UNIQUE (istex_id),
            UNIQUE (ark),
            UNIQUE (doi),
            UNIQUE (cat_path),
            UNIQUE (task_id)
        );
    ''')

    # copier données
    op.execute('''
        INSERT INTO paper_new (id, title, doi, ark, istex_id, publication_date, pdf_path, txt_path, cat_path, cat_in_db, task_id, task_status, task_started, task_stopped)
        SELECT id, title, doi, ark, istex_id, publication_date, pdf_path, txt_path, cat_path, cat_in_db, task_id, task_status, task_started, task_stopped FROM paper;
    ''')

    # drop ancienne table
    op.execute('DROP TABLE paper;')

    # renommer table temporaire
    op.execute('ALTER TABLE paper_new RENAME TO paper;')

def downgrade():
    pass
