"""
Declarative Base for all SQLAlchemy models.

Every model in app/models/ imports Base from here and subclasses it. This is
what lets Base.metadata.create_all() (in init_db.py) discover every table
that's been defined, as long as the model module has been imported somewhere
before create_all() runs.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()
