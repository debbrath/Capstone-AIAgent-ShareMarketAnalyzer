import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from utils.database_manager import DatabaseManager


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmployeeService:
    """Service to fetch employee name"""
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_employee_name(self, id: str):
        session = self.db_manager.get_session()
        try:
            sql = text("SELECT * FROM employee_name WHERE id = :id")
            row = session.execute(sql, {"id": id}).fetchone()
            if not row:
                print("❌ No employee found.")
                return None
            sa = row._mapping if hasattr(row, "_mapping") else row
            print("✅ Employee found:", dict(sa))
            return sa
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
        finally:
            session.close()