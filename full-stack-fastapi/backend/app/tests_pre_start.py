import logging

from sqlmodel import Session, select

logger = logging.getLogger(__name__)


def init(engine: object) -> None:
    with Session(engine) as session:
        session.exec(select(1))
    logger.info("Database connection successful.")
