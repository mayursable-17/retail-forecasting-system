"""
Database connection management and initialization.
"""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from src.config import DATABASE_URL
from src.database.models import Base, Shop

_engine = None
_SessionFactory = None


def get_engine(db_url: str = None):
    global _engine, _SessionFactory
    url = db_url or DATABASE_URL
    if _engine is None or str(_engine.url) != url:
        connect_args = {"check_same_thread": False} if "sqlite" in url else {}
        kwargs = {"connect_args": connect_args, "echo": False}
        if ":memory:" in url:
            kwargs["poolclass"] = StaticPool
        _engine = create_engine(url, **kwargs)
        _SessionFactory = sessionmaker(bind=_engine, expire_on_commit=False)
    return _engine


def get_session_factory(db_url: str = None):
    get_engine(db_url)
    return _SessionFactory


def get_session(db_url: str = None) -> Session:
    factory = get_session_factory(db_url)
    return factory()


@contextmanager
def get_db_context(db_url: str = None) -> Generator[Session, None, None]:
    session = get_session(db_url)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _ensure_schema_migrations(engine) -> None:
    """Safely apply schema enhancements to existing SQLite/SQL databases."""
    try:
        url_str = str(engine.url)
        if "sqlite" in url_str:
            with engine.connect() as conn:
                res = conn.execute(text("PRAGMA table_info(shops)")).fetchall()
                cols = [r[1] for r in res] if res else []
                if cols:
                    if "default_lead_time_days" not in cols:
                        conn.execute(text("ALTER TABLE shops ADD COLUMN default_lead_time_days INTEGER DEFAULT 7"))
                    if "default_review_period_days" not in cols:
                        conn.execute(text("ALTER TABLE shops ADD COLUMN default_review_period_days INTEGER DEFAULT 7"))
                    if "default_service_level" not in cols:
                        conn.execute(text("ALTER TABLE shops ADD COLUMN default_service_level FLOAT DEFAULT 0.95"))
                    if "default_safety_stock_method" not in cols:
                        conn.execute(text("ALTER TABLE shops ADD COLUMN default_safety_stock_method VARCHAR(50) DEFAULT 'variability'"))
                    if "default_replenishment_buffer_pct" not in cols:
                        conn.execute(text("ALTER TABLE shops ADD COLUMN default_replenishment_buffer_pct FLOAT DEFAULT 0.20"))
                    conn.commit()
    except Exception:
        pass


def init_db(engine=None) -> None:
    """Initialize database tables and create default shop if none exists."""
    eng = engine or get_engine()
    Base.metadata.create_all(bind=eng)
    _ensure_schema_migrations(eng)
    
    # Ensure default shop exists
    with get_db_context(db_url=str(eng.url)) as session:
        shop = session.query(Shop).filter_by(shop_id=1).first()
        if not shop:
            default_shop = Shop(
                shop_id=1,
                shop_name="Kirana & Retail Hub",
                shop_type="General Store / Supermarket",
                currency_symbol="₹",
                currency_code="INR",
                default_lead_time_days=7,
                default_review_period_days=7,
                default_service_level=0.95,
                default_safety_stock_method="variability",
                default_replenishment_buffer_pct=0.20
            )
            session.add(default_shop)
