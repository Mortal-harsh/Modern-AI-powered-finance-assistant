"""
Database Connection Manager for Oracle Database.
Provides connection pooling, lifecycle management, safe query execution with bind variables,
and direct PL/SQL procedure and function execution via python-oracledb.
Supports both Thin mode and Thick mode with automatic client detection.
"""

import os
import sys
import logging
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager

try:
    import oracledb
except ImportError:
    oracledb = None

from config.settings import AppConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("DatabaseManager")


class DatabaseManager:
    """Manages Oracle database connections, queries, and PL/SQL calls."""

    _instance: Optional["DatabaseManager"] = None
    _client_initialized: bool = False

    def __new__(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._init_manager()
        return cls._instance

    def _init_manager(self):
        """Initialize connection manager and determine client mode."""
        self._ensure_client_init()

    def _ensure_client_init(self):
        """Initialize Oracle Client if directory provided or detected."""
        if DatabaseManager._client_initialized:
            return

        if oracledb is None:
            logger.error("python-oracledb package is not installed.")
            return

        client_dir = AppConfig.get_oracle_client_dir()
        if client_dir and os.path.exists(client_dir):
            try:
                oracledb.init_oracle_client(lib_dir=client_dir)
                DatabaseManager._client_initialized = True
                logger.info("Initialized Oracle Client in Thick mode from: %s", client_dir)
            except Exception as e:
                # If already initialized or not needed, log informative warning
                if "already been initialized" in str(e).lower():
                    DatabaseManager._client_initialized = True
                else:
                    logger.warning("Could not initialize Oracle Client: %s", e)
        else:
            logger.info("Operating in python-oracledb Thin Mode by default.")

    def test_connection(self) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Tests the Oracle database connection and returns diagnostic status.
        Returns:
            (is_connected: bool, message: str, details: dict)
        """
        if oracledb is None:
            return False, "Error: python-oracledb library is not installed in the Python environment.", {}

        self._ensure_client_init()

        user = AppConfig.get_oracle_user()
        password = AppConfig.get_oracle_password()
        dsn = AppConfig.get_oracle_dsn()

        details = {
            "user": user,
            "dsn": dsn,
            "client_mode": "Thick" if DatabaseManager._client_initialized else "Thin",
            "server_version": "Unknown"
        }

        try:
            conn = oracledb.connect(user=user, password=password, dsn=dsn)
            with conn.cursor() as cursor:
                cursor.execute("SELECT banner FROM v$version WHERE ROWNUM = 1")
                row = cursor.fetchone()
                if row:
                    details["server_version"] = row[0]
            conn.close()
            return True, f"Connected successfully to Oracle Database!\n{details['server_version']}", details
        except Exception as e:
            err_msg = str(e)
            logger.error("Oracle Connection Test Failed: %s", err_msg)
            return False, f"Failed to connect to Oracle: {err_msg}", details

    @contextmanager
    def get_connection(self):
        """Context manager for acquiring an active database connection."""
        if oracledb is None:
            raise RuntimeError("python-oracledb is not installed.")

        self._ensure_client_init()
        user = AppConfig.get_oracle_user()
        password = AppConfig.get_oracle_password()
        dsn = AppConfig.get_oracle_dsn()

        conn = None
        try:
            conn = oracledb.connect(user=user, password=password, dsn=dsn)
            yield conn
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception as e:
                    logger.warning("Error closing connection: %s", e)

    @contextmanager
    def get_cursor(self, commit: bool = False):
        """Context manager yielding a cursor with safe commit/rollback."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                if commit:
                    conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()

    def execute_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Executes a SELECT query using bind variables and returns rows as a list of dicts.
        """
        with self.get_cursor(commit=False) as cursor:
            cursor.execute(sql, params or {})
            if cursor.description is None:
                return []
            columns = [col[0].upper() for col in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]

    def execute_scalar(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Executes a query and returns the first column of the first row."""
        with self.get_cursor(commit=False) as cursor:
            cursor.execute(sql, params or {})
            row = cursor.fetchone()
            return row[0] if row else None

    def execute_non_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> int:
        """Executes an INSERT, UPDATE, or DELETE and returns affected row count."""
        with self.get_cursor(commit=True) as cursor:
            cursor.execute(sql, params or {})
            return cursor.rowcount

    def call_procedure(self, proc_name: str, parameters: List[Any]) -> List[Any]:
        """
        Calls a PL/SQL stored procedure using cursor.callproc().
        Supports IN and OUT parameters (including oracledb.CURSOR / SYS_REFCURSOR).
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                result = cursor.callproc(proc_name, parameters)
                conn.commit()
                return result

    def call_function(self, func_name: str, return_type: Any, parameters: List[Any]) -> Any:
        """
        Calls a PL/SQL stored function using cursor.callfunc().
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                result = cursor.callfunc(func_name, return_type, parameters)
                return result

    def fetch_refcursor(self, ref_cursor) -> List[Dict[str, Any]]:
        """Utility to exhaust and convert a SYS_REFCURSOR into list of dictionaries."""
        try:
            columns = [col[0].upper() for col in ref_cursor.description]
            rows = ref_cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        finally:
            ref_cursor.close()

    def run_sql_script(self, script_path: str) -> Tuple[bool, str]:
        """
        Executes an SQL script containing tables, views, triggers, and PL/SQL blocks.
        Splits statements intelligently on standard SQL terminators and PL/SQL slashes.
        """
        if not os.path.exists(script_path):
            return False, f"Script file not found: {script_path}"

        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()

        statements = []
        current = []
        in_plsql = False

        for raw_line in content.splitlines():
            # Remove trailing comments
            line_no_comment = raw_line
            if "--" in raw_line:
                # If not inside a quoted string
                parts = raw_line.split("--")
                # keep before comment
                line_no_comment = parts[0]

            line = line_no_comment.strip()
            if not line:
                continue

            upper = line.upper()
            if any(upper.startswith(k) for k in ["CREATE OR REPLACE", "CREATE TRIGGER", "DECLARE", "BEGIN"]):
                in_plsql = True

            if line == "/" and in_plsql:
                stmt = "\n".join(current).strip()
                if stmt:
                    statements.append(stmt)
                current = []
                in_plsql = False
            elif line.endswith(";") and not in_plsql:
                current.append(line_no_comment)
                stmt = "\n".join(current).strip()
                if stmt.endswith(";"):
                    stmt = stmt[:-1].strip()
                if stmt:
                    statements.append(stmt)
                current = []
            else:
                current.append(line_no_comment)

        if current:
            stmt = "\n".join(current).strip()
            if stmt.endswith(";"):
                stmt = stmt[:-1].strip()
            if stmt:
                statements.append(stmt)

        executed_count = 0
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                for stmt in statements:
                    stmt_clean = stmt.strip()
                    if not stmt_clean or stmt_clean.startswith("--"):
                        continue
                    try:
                        cursor.execute(stmt_clean)
                        executed_count += 1
                    except Exception as e:
                        logger.warning("Error running statement:\n%s\nError: %s", stmt_clean[:120], e)
                conn.commit()

        return True, f"Successfully executed {executed_count} statements from {os.path.basename(script_path)}."


def get_db() -> DatabaseManager:
    """Helper to retrieve the DatabaseManager singleton instance."""
    return DatabaseManager()
