# from sqlalchemy import create_engine
# from sqlalchemy.orm import scoped_session, sessionmaker
# from sqlalchemy.ext.declarative import declarative_base
# from flask import current_app as app
#
# engine = create_engine(app.config.get('SQLALCHEMY_DATABASE_URI'), convert_unicode=True)
# db_session = scoped_session(sessionmaker(autocommit=False,
#                                          autoflush=False,
#                                          bind=engine))
# Base = declarative_base()
# Base.query = db_session.query_property()
#
# def init_db():
#     # import all modules here that might define models so that
#     # they will be registered properly on the metadata.  Otherwise
#     # you will have to import them first before calling init_db()
#     # import yourapplication.models
#     import image, audio
#     Base.metadata.create_all(bind=engine)

from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()