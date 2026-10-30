"""
Database Initializer Utility.
Executes schema DDL, compiles PL/SQL procedures, and loads demonstration seed data.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
from database.connection import get_db

logger = logging.getLogger("DatabaseInitializer")
BASE_DIR = Path(__file__).resolve().parent


def initialize_database(load_seed: bool = True) -> Tuple[bool, str]:
    """
    Runs schema creation, compiles PL/SQL procedures, and optionally seeds demonstration data.
    """
    db = get_db()
    
    # 1. Test connectivity first
    connected, msg, _ = db.test_connection()
    if not connected:
        return False, f"Cannot initialize: Database connection test failed.\n{msg}"

    schema_file = BASE_DIR / "schema.sql"
    proc_file = BASE_DIR / "procedures.sql"
    seed_file = BASE_DIR / "seed_data.sql"

    try:
        # Step 1: Run Schema
        logger.info("Executing schema DDL...")
        s_ok, s_msg = db.run_sql_script(str(schema_file))
        if not s_ok:
            return False, f"Schema execution failed: {s_msg}"

        # Step 2: Compile PL/SQL Procedures
        logger.info("Compiling PL/SQL stored procedures & functions...")
        p_ok, p_msg = db.run_sql_script(str(proc_file))
        if not p_ok:
            return False, f"PL/SQL procedure compilation failed: {p_msg}"

        # Step 3: Load Seed Data if requested
        if load_seed:
            logger.info("Loading demonstration seed data...")
            d_ok, d_msg = db.run_sql_script(str(seed_file))
            if not d_ok:
                return False, f"Seed data execution failed: {d_msg}"

        return True, "Database initialized successfully! Schema, PL/SQL procedures, and demo data are active."
    except Exception as e:
        logger.error("Initialization exception: %s", e)
        return False, f"Unexpected error during initialization: {e}"


if __name__ == "__main__":
    ok, message = initialize_database(load_seed=True)
    print("Result:", ok)
    print("Message:", message)
