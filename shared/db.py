import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        logger.debug("Initializing DatabaseManager")
        db_url = os.getenv('DATABASE_URL', 
            'postgresql://kagentic:kagentic123@tool-registry:5432/tool_registry')
        logger.info(f"Connecting to database at: {db_url.split('@')[1]}")
        
        connect_args = {
            "connect_timeout": 5,
            "client_encoding": "utf8",
            "application_name": "ai-agent",
            # Try explicit auth settings
            "sslmode": "disable",
            "gssencmode": "disable"
        }
        logger.debug(f"Connection arguments: {connect_args}")
        
        try:
            logger.debug("Creating database engine")
            self.engine = create_engine(
                db_url,
                connect_args=connect_args,
                pool_pre_ping=True,
                echo=True,  # SQL logging
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
                echo_pool=True  # Add connection pool logging
            )
            logger.info("Database engine created successfully")
            self.Session = sessionmaker(bind=self.engine)
            logger.debug("Session maker created")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
            raise

    def register_tool(self, name, description, endpoint_url, capabilities):
        with self.Session() as session:
            query = text("""
                INSERT INTO tools (
                    name, description, endpoint_url, capabilities, 
                    status, last_heartbeat
                ) VALUES (
                    :name, :description, :endpoint_url, :capabilities,
                    'active', CURRENT_TIMESTAMP
                )
                ON CONFLICT (name) 
                DO UPDATE SET 
                    description = :description,
                    endpoint_url = :endpoint_url,
                    capabilities = :capabilities,
                    status = 'active',
                    last_heartbeat = CURRENT_TIMESTAMP
                RETURNING id
            """)
            result = session.execute(query, {
                'name': name,
                'description': description,
                'endpoint_url': endpoint_url,
                'capabilities': capabilities
            })
            session.commit()
            return result.scalar()

    def get_active_tools(self):
        with self.Session() as session:
            logger.info("Fetching active tools")
            query = text("""
                SELECT name, description, endpoint_url, capabilities 
                FROM tools 
                WHERE status = 'active' 
                AND (last_heartbeat > NOW() - INTERVAL '5 minutes' 
                     OR last_heartbeat IS NULL)
            """)
            try:
                result = [dict(row) for row in session.execute(query)]
                logger.info(f"Found {len(result)} active tools")
                for tool in result:
                    logger.info(f"Active tool: {tool['name']} at {tool['endpoint_url']}")
                return result
            except Exception as e:
                logger.error(f"Error fetching active tools: {str(e)}", exc_info=True)
                raise

    def create_session(self, session_id):
        with self.Session() as session:
            query = text("""
                INSERT INTO sessions (session_id)
                VALUES (:session_id)
                ON CONFLICT (session_id) 
                DO UPDATE SET last_active = CURRENT_TIMESTAMP
            """)
            session.execute(query, {'session_id': session_id})
            session.commit()

    def add_chat_message(self, session_id, message, role):
        with self.Session() as session:
            query = text("""
                INSERT INTO chat_history (session_id, message, role)
                VALUES (:session_id, :message, :role)
            """)
            session.execute(query, {
                'session_id': session_id,
                'message': message,
                'role': role
            })
            session.commit()

    def update_tool_heartbeat(self, name):
        with self.Session() as session:
            query = text("""
                UPDATE tools 
                SET last_heartbeat = CURRENT_TIMESTAMP 
                WHERE name = :name
            """)
            session.execute(query, {'name': name})
            session.commit() 