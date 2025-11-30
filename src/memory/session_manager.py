"""
Session management for ScholarLens.

Manages paper analysis sessions, stores intermediate results,
and maintains conversation history.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
import json
from pathlib import Path


@dataclass
class SessionData:
    """Represents a paper analysis session."""
    session_id: str
    created_at: datetime
    last_accessed: datetime
    paper_path: str
    document: Optional[Dict[str, Any]] = None
    agent_outputs: Dict[str, Any] = field(default_factory=dict)
    final_report: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "initialized"  # initialized, processing, completed, failed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'paper_path': self.paper_path,
            'document': self.document,
            'agent_outputs': self.agent_outputs,
            'final_report': self.final_report,
            'metadata': self.metadata,
            'status': self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionData':
        """Create session from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_accessed'] = datetime.fromisoformat(data['last_accessed'])
        return cls(**data)


class SessionManager:
    """Manages paper analysis sessions with in-memory storage."""
    
    def __init__(
        self,
        max_sessions: int = 100,
        session_timeout_hours: int = 24,
        enable_persistence: bool = False,
        persistence_path: Optional[Path] = None
    ):
        """
        Initialize session manager.
        
        Args:
            max_sessions: Maximum number of sessions to keep in memory
            session_timeout_hours: Hours before a session expires
            enable_persistence: Whether to persist sessions to disk
            persistence_path: Path for session persistence
        """
        self.max_sessions = max_sessions
        self.session_timeout = timedelta(hours=session_timeout_hours)
        self.enable_persistence = enable_persistence
        self.persistence_path = persistence_path
        
        # In-memory session storage
        self.sessions: Dict[str, SessionData] = {}
        
        # Session access tracking for LRU eviction
        self.access_order: List[str] = []
        
        # Load persisted sessions if enabled
        if self.enable_persistence and self.persistence_path:
            self._load_sessions()
    
    def create_session(
        self,
        paper_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new analysis session.
        
        Args:
            paper_path: Path to the paper being analyzed
            metadata: Optional metadata for the session
            
        Returns:
            Session ID
        """
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Create session
        now = datetime.now()
        session = SessionData(
            session_id=session_id,
            created_at=now,
            last_accessed=now,
            paper_path=paper_path,
            metadata=metadata or {},
            status="initialized"
        )
        
        # Store session
        self.sessions[session_id] = session
        self.access_order.append(session_id)
        
        # Evict old sessions if needed
        self._evict_if_needed()
        
        # Persist if enabled
        if self.enable_persistence:
            self._persist_session(session_id)
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Get session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            SessionData or None if not found
        """
        session = self.sessions.get(session_id)
        
        if session:
            # Update last accessed time
            session.last_accessed = datetime.now()
            
            # Update access order
            if session_id in self.access_order:
                self.access_order.remove(session_id)
            self.access_order.append(session_id)
            
            # Check if session is expired
            if self._is_expired(session):
                self.delete_session(session_id)
                return None
        
        return session
    
    def update_session(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update session data.
        
        Args:
            session_id: Session ID
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Update fields
        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        session.last_accessed = datetime.now()
        
        # Persist if enabled
        if self.enable_persistence:
            self._persist_session(session_id)
        
        return True
    
    def store_document(
        self,
        session_id: str,
        document: Dict[str, Any]
    ) -> bool:
        """
        Store extracted document in session.
        
        Args:
            session_id: Session ID
            document: Document dictionary
            
        Returns:
            True if successful
        """
        return self.update_session(session_id, {'document': document})
    
    def store_agent_output(
        self,
        session_id: str,
        agent_name: str,
        output: Dict[str, Any]
    ) -> bool:
        """
        Store agent output in session.
        
        Args:
            session_id: Session ID
            agent_name: Name of the agent
            output: Agent output dictionary
            
        Returns:
            True if successful
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.agent_outputs[agent_name] = output
        session.last_accessed = datetime.now()
        
        # Persist if enabled
        if self.enable_persistence:
            self._persist_session(session_id)
        
        return True
    
    def get_agent_output(
        self,
        session_id: str,
        agent_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get agent output from session.
        
        Args:
            session_id: Session ID
            agent_name: Name of the agent
            
        Returns:
            Agent output dictionary or None
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        return session.agent_outputs.get(agent_name)
    
    def store_final_report(
        self,
        session_id: str,
        report: Dict[str, Any]
    ) -> bool:
        """
        Store final aggregated report in session.
        
        Args:
            session_id: Session ID
            report: Final report dictionary
            
        Returns:
            True if successful
        """
        return self.update_session(
            session_id,
            {'final_report': report, 'status': 'completed'}
        )
    
    def get_full_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete session context for agents.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dictionary with all session data
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        return {
            'session_id': session.session_id,
            'paper_path': session.paper_path,
            'document': session.document,
            'agent_outputs': session.agent_outputs,
            'metadata': session.metadata
        }
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if deleted, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            
            if session_id in self.access_order:
                self.access_order.remove(session_id)
            
            # Remove persisted file if enabled
            if self.enable_persistence and self.persistence_path:
                session_file = self.persistence_path / f"{session_id}.json"
                if session_file.exists():
                    session_file.unlink()
            
            return True
        
        return False
    
    def clear_all_sessions(self) -> int:
        """
        Clear all sessions.
        
        Returns:
            Number of sessions cleared
        """
        count = len(self.sessions)
        self.sessions.clear()
        self.access_order.clear()
        
        # Clear persisted files if enabled
        if self.enable_persistence and self.persistence_path:
            for session_file in self.persistence_path.glob("*.json"):
                session_file.unlink()
        
        return count
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all active sessions.
        
        Returns:
            List of session summaries
        """
        sessions = []
        for session_id in self.access_order:
            session = self.sessions.get(session_id)
            if session:
                sessions.append({
                    'session_id': session.session_id,
                    'paper_path': session.paper_path,
                    'status': session.status,
                    'created_at': session.created_at.isoformat(),
                    'last_accessed': session.last_accessed.isoformat()
                })
        
        return sessions
    
    def get_session_count(self) -> int:
        """
        Get number of active sessions.
        
        Returns:
            Session count
        """
        return len(self.sessions)
    
    def _is_expired(self, session: SessionData) -> bool:
        """Check if session is expired."""
        age = datetime.now() - session.last_accessed
        return age > self.session_timeout
    
    def _evict_if_needed(self) -> None:
        """Evict oldest sessions if max capacity reached."""
        while len(self.sessions) > self.max_sessions:
            if not self.access_order:
                break
            
            # Remove least recently accessed session
            oldest_id = self.access_order.pop(0)
            if oldest_id in self.sessions:
                del self.sessions[oldest_id]
    
    def _persist_session(self, session_id: str) -> None:
        """Persist session to disk."""
        if not self.persistence_path:
            return
        
        session = self.sessions.get(session_id)
        if not session:
            return
        
        self.persistence_path.mkdir(parents=True, exist_ok=True)
        
        session_file = self.persistence_path / f"{session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session.to_dict(), f, indent=2)
    
    def _load_sessions(self) -> None:
        """Load persisted sessions from disk."""
        if not self.persistence_path or not self.persistence_path.exists():
            return
        
        for session_file in self.persistence_path.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    session = SessionData.from_dict(data)
                    
                    # Only load non-expired sessions
                    if not self._is_expired(session):
                        self.sessions[session.session_id] = session
                        self.access_order.append(session.session_id)
            except Exception as e:
                print(f"Error loading session from {session_file}: {e}")
    
    def export_session(
        self,
        session_id: str,
        export_path: Path
    ) -> bool:
        """
        Export session to JSON file.
        
        Args:
            session_id: Session ID
            export_path: Path to export file
            
        Returns:
            True if successful
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        export_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(session.to_dict(), f, indent=2)
        
        return True
    
    def import_session(self, import_path: Path) -> Optional[str]:
        """
        Import session from JSON file.
        
        Args:
            import_path: Path to import file
            
        Returns:
            Session ID if successful, None otherwise
        """
        if not import_path.exists():
            return None
        
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                session = SessionData.from_dict(data)
                
                self.sessions[session.session_id] = session
                self.access_order.append(session.session_id)
                
                return session.session_id
        except Exception as e:
            print(f"Error importing session: {e}")
            return None


# Global session manager instance
_global_session_manager: Optional[SessionManager] = None


def get_session_manager(
    max_sessions: int = 100,
    session_timeout_hours: int = 24
) -> SessionManager:
    """
    Get or create global session manager.
    
    Args:
        max_sessions: Maximum sessions to keep
        session_timeout_hours: Session timeout in hours
        
    Returns:
        SessionManager instance
    """
    global _global_session_manager
    
    if _global_session_manager is None:
        _global_session_manager = SessionManager(
            max_sessions=max_sessions,
            session_timeout_hours=session_timeout_hours
        )
    
    return _global_session_manager
