#!/usr/bin/env python3
"""
Database connection and initialization module for the Emergency Management System.
"""

import os
import asyncpg
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection manager for PostgreSQL."""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.connection_params = {
            'user': os.getenv('DB_USER', 'zs_zzr'),
            'password': os.getenv('DB_PASSWORD', '373291Moon'),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'zs_data')
        }
    
    async def initialize(self):
        """Initialize database connection pool and create tables."""
        try:
            self.pool = await asyncpg.create_pool(**self.connection_params)
            logger.info("Database connection pool created successfully")
            await self._create_tables()
            logger.info("Database tables initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def _create_tables(self):
        """Create necessary database tables."""
        async with self.pool.acquire() as conn:
            # Users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) UNIQUE NOT NULL,
                    username VARCHAR(255),
                    email VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Sessions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) UNIQUE NOT NULL,
                    user_id VARCHAR(255) REFERENCES users(user_id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(50) DEFAULT 'active',
                    metadata JSONB
                )
            """)
            
            # Workflow executions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS workflow_executions (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) REFERENCES sessions(session_id),
                    user_id VARCHAR(255) REFERENCES users(user_id),
                    workflow_name VARCHAR(255) NOT NULL,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    status VARCHAR(50) DEFAULT 'running',
                    input_data JSONB,
                    output_data JSONB,
                    processing_log TEXT[],
                    mcp_calls JSONB,
                    langfuse_trace_id VARCHAR(255)
                )
            """)
            
            # MCP calls table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS mcp_calls (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) REFERENCES sessions(session_id),
                    workflow_execution_id INTEGER REFERENCES workflow_executions(id),
                    mcp_server VARCHAR(255) NOT NULL,
                    tool_name VARCHAR(255) NOT NULL,
                    called_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    duration_ms INTEGER,
                    success BOOLEAN,
                    input_params JSONB,
                    output_result JSONB,
                    error_message TEXT
                )
            """)
            
            # Create indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_workflow_executions_session_id ON workflow_executions(session_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_mcp_calls_session_id ON mcp_calls(session_id)")
    
    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

# Global database manager instance
db_manager = DatabaseManager()

async def init_database():
    """Initialize database connection."""
    await db_manager.initialize()

async def close_database():
    """Close database connection."""
    await db_manager.close()