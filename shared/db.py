import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        db_url = os.getenv('DATABASE_URL', 
            'postgresql://kagentic:kagentic123@tool-registry:5432/tool_registry')
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def register_tool(self, name, description, endpoint_url, capabilities):
        with self.Session() as session:
            query = text("""
                INSERT INTO tools (name, description, endpoint_url, capabilities)
                VALUES (:name, :description, :endpoint_url, :capabilities)
                ON CONFLICT (name) 
                DO UPDATE SET 
                    description = :description,
                    endpoint_url = :endpoint_url,
                    capabilities = :capabilities,
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
            query = text("""
                SELECT name, description, endpoint_url, capabilities 
                FROM tools 
                WHERE status = 'active' 
                AND (last_heartbeat > NOW() - INTERVAL '5 minutes' 
                     OR last_heartbeat IS NULL)
            """)
            return [dict(row) for row in session.execute(query)]

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