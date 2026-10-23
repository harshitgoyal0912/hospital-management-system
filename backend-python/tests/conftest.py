"""Shared pytest fixtures.

Integration tests need a real PostgreSQL because the models use the
postgresql UUID dialect. Set TEST_DATABASE_URL to enable them; without it
they skip cleanly rather than silently passing against a different engine.
"""
import os
import pytest

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@pytest.fixture(scope="session")
def database_url():
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL not set; integration tests skipped")
    return TEST_DATABASE_URL


@pytest.fixture(scope="session")
def engine(database_url):
    from sqlalchemy import create_engine
    eng = create_engine(database_url)
    yield eng
    eng.dispose()


@pytest.fixture
def db_session(engine):
    from sqlalchemy.orm import sessionmaker
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()
