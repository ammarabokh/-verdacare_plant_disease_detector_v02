import time
from collections import defaultdict

class ChatMemory:
    """
    Simple in-memory chat memory manager.
    Stores last N messages per session.
    """

    def __init__(self, max_history=10, expiry_minutes=30):
        """
        Args:
            max_history: Maximum number of messages to keep per session
            expiry_minutes: Session expiry time in minutes
        """
        self.sessions = defaultdict(list)
        self.last_activity = {}
        self.max_history = max_history
        self.expiry_minutes = expiry_minutes

    def add_message(self, session_id, role, content):
        """
        Add a message to the session history.

        Args:
            session_id: Unique session identifier
            role: 'user' or 'assistant'
            content: Message content
        """
        # Clean old sessions
        self._clean_expired_sessions()

        # Add message
        self.sessions[session_id].append({
            'role': role,
            'content': content,
            'timestamp': time.time()
        })

        # Update activity
        self.last_activity[session_id] = time.time()

        # Keep only last N messages
        if len(self.sessions[session_id]) > self.max_history:
            self.sessions[session_id] = self.sessions[session_id][-self.max_history:]

    def get_history(self, session_id):
        """
        Get chat history for a session.

        Returns:
            List of messages [{'role': 'user'/'assistant', 'content': '...'}]
        """
        self._clean_expired_sessions()

        if session_id not in self.sessions:
            return []

        # Return without timestamps
        return [
            {'role': msg['role'], 'content': msg['content']}
            for msg in self.sessions[session_id]
        ]

    def clear_history(self, session_id):
        """Clear chat history for a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.last_activity:
            del self.last_activity[session_id]

    def _clean_expired_sessions(self):
        """Remove expired sessions."""
        current_time = time.time()
        expired = [
            sid for sid, last in self.last_activity.items()
            if (current_time - last) > (self.expiry_minutes * 60)
        ]
        for sid in expired:
            self.clear_history(sid)

# Singleton instance
chat_memory = ChatMemory(max_history=10, expiry_minutes=30)
