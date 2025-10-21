import os
import sys

# Add project root to Python path (so 'utils' can be imported)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from utils.database_manager import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ShareMarketService:
    """Service class for Share Market related database operations."""
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager   

    
    # -----------------------------------------------------------
    # 🔹 Get list of distinct trading codes
    # -----------------------------------------------------------
    def get_trading_list(self) -> Optional[List[str]]:
        session = self.db_manager.get_session()
        try:
            sql = text("SELECT DISTINCT trading_code FROM dbo.market_history ORDER BY trading_code ASC")
            result = session.execute(sql).fetchall()
            if not result:
                logger.warning("⚠️ No trading codes found in market_history.")
                return None
            trading_codes = [row[0] for row in result if row[0]]
            logger.info(f"✅ Retrieved {len(trading_codes)} trading codes.")
            return trading_codes
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error in get_trading_list: {e}")
            return None
        finally:
            session.close()

    # -----------------------------------------------------------
    # 🔹 Get history for a specific trading code
    # -----------------------------------------------------------
    def get_history_by_code(self, trading_code: str) -> Optional[List[Dict[str, Any]]]:
        session = self.db_manager.get_session()
        try:
            sql = text("""
                SELECT TOP 100 *
                FROM dbo.market_history
                WHERE trading_code = :trading_code
                ORDER BY date DESC
            """)
            result = session.execute(sql, {"trading_code": trading_code}).fetchall()
            if not result:
                logger.warning(f"⚠️ No data found for trading_code: {trading_code}")
                return None

            # Convert to list of dicts
            data = [dict(row._mapping) for row in result]
            logger.info(f"✅ Retrieved {len(data)} rows for {trading_code}")
            return data
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error in get_history_by_code: {e}")
            return None
        finally:
            session.close()
