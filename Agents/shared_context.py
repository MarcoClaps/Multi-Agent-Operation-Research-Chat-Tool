"""
Shared Context Manager for OR Agents
Provides per-user context isolation for multi-tenant deployments.
"""

from typing import Optional, Dict, Any
import json
from pathlib import Path
import threading


class ORContext:
    """
    Per-user context for sharing state between OR agents.
    Stores the current instance, solution, and other shared data.
    Each user gets their own isolated context.
    """
    
    def __init__(self, user_id: str, base_workspace: str = ".files"):
        """
        Initialize a user-specific context.
        
        Args:
            user_id: Unique identifier for the user
            base_workspace: Base directory for file storage
        """
        self.user_id = user_id
        self._current_instance: Optional[Dict[str, Any]] = None
        self._current_solution: Optional[Dict[str, Any]] = None
        self._history: list = []
        self._workspace_path: Path = Path(base_workspace) / user_id
        self._workspace_path.mkdir(parents=True, exist_ok=True)
    
    def set_workspace(self, path: str):
        """Set the workspace path for file operations."""
        self._workspace_path = Path(path)
        self._workspace_path.mkdir(parents=True, exist_ok=True)
    
    @property
    def workspace(self) -> Path:
        return self._workspace_path
    
    # Instance Management
    def set_instance(self, instance: Dict[str, Any], name: str = "default"):
        """Store the current VRP instance."""
        self._current_instance = instance
        self._history.append({
            "type": "instance_created",
            "name": name,
            "n_customers": instance.get("n_customers", 0)
        })
    
    def get_instance(self) -> Optional[Dict[str, Any]]:
        """Get the current VRP instance."""
        return self._current_instance
    
    def get_instance_json(self) -> str:
        """Get the current instance as JSON string."""
        if self._current_instance is None:
            return '{"error": "No instance loaded. Please generate or load an instance first."}'
        return json.dumps(self._current_instance, indent=2)
    
    def has_instance(self) -> bool:
        """Check if an instance is loaded."""
        return self._current_instance is not None
    
    # Solution Management
    def set_solution(self, solution: Dict[str, Any]):
        """Store the current solution."""
        self._current_solution = solution
        self._history.append({
            "type": "solution_found",
            "cost": solution.get("total_cost", 0),
            "routes": len(solution.get("routes", []))
        })
    
    def get_solution(self) -> Optional[Dict[str, Any]]:
        """Get the current solution."""
        return self._current_solution
    
    def has_solution(self) -> bool:
        """Check if a solution exists."""
        return self._current_solution is not None
    
    # File Operations
    def save_instance(self, filename: str = "vrp_instance.json") -> str:
        """Save current instance to file in workspace."""
        if not self.has_instance():
            return "Error: No instance to save."
        
        filepath = self._workspace_path / filename
        with open(filepath, 'w') as f:
            json.dump(self._current_instance, f, indent=2)
        return f"Instance saved to {filepath}"
    
    def load_instance(self, filename: str = "vrp_instance.json") -> str:
        """Load instance from file in workspace."""
        filepath = self._workspace_path / filename
        
        if not filepath.exists():
            return f"Error: File {filepath} not found."
        
        with open(filepath, 'r') as f:
            self._current_instance = json.load(f)
        return f"Instance loaded from {filepath}"
    
    # History and Status
    def get_status(self) -> str:
        """Get current context status."""
        status = []
        status.append("=" * 50)
        status.append(f"OR Context Status (User: {self.user_id})")
        status.append("=" * 50)
        status.append(f"Workspace: {self._workspace_path}")
        status.append(f"Instance loaded: {'Yes' if self.has_instance() else 'No'}")
        
        if self.has_instance():
            inst = self._current_instance
            status.append(f"  - Customers: {inst.get('n_customers', '?')}")
            status.append(f"  - Vehicles: {inst.get('n_vehicles', '?')}")
            status.append(f"  - Capacity: {inst.get('vehicle_capacity', '?')}")
        
        status.append(f"Solution found: {'Yes' if self.has_solution() else 'No'}")
        
        if self.has_solution():
            sol = self._current_solution
            status.append(f"  - Total cost: {sol.get('total_cost', '?')}")
            status.append(f"  - Routes: {len(sol.get('routes', []))}")
        
        status.append(f"\nHistory ({len(self._history)} events)")
        for event in self._history[-5:]:  # Last 5 events
            status.append(f"  - {event['type']}")
        
        return "\n".join(status)
    
    def clear(self):
        """Clear all context data."""
        self._current_instance = None
        self._current_solution = None
        self._history = []


class ORContextManager:
    """
    Thread-safe manager for per-user OR contexts.
    Handles creation, retrieval, and cleanup of user-specific contexts.
    """
    _contexts: Dict[str, ORContext] = {}
    _lock = threading.Lock()
    _base_workspace: str = ".files"
    
    @classmethod
    def set_base_workspace(cls, path: str):
        """Set the base workspace directory for all user contexts."""
        cls._base_workspace = path
        Path(path).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_context(cls, user_id: str) -> ORContext:
        """
        Get or create a context for a specific user.
        Thread-safe implementation.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            ORContext instance for the user
        """
        with cls._lock:
            if user_id not in cls._contexts:
                cls._contexts[user_id] = ORContext(user_id, cls._base_workspace)
            return cls._contexts[user_id]
    
    @classmethod
    def clear_context(cls, user_id: str):
        """
        Clear and remove a user's context.
        
        Args:
            user_id: Unique identifier for the user
        """
        with cls._lock:
            if user_id in cls._contexts:
                cls._contexts[user_id].clear()
                del cls._contexts[user_id]
    
    @classmethod
    def get_active_users(cls) -> list:
        """Get list of users with active contexts."""
        with cls._lock:
            return list(cls._contexts.keys())
    
    @classmethod
    def cleanup_all(cls):
        """Clear all user contexts (for shutdown)."""
        with cls._lock:
            for ctx in cls._contexts.values():
                ctx.clear()
            cls._contexts.clear()


# Thread-local storage for current user context
_current_user_id = threading.local()


def set_current_user(user_id: str):
    """
    Set the current user ID for the current thread.
    This should be called at the start of each request/message handling.
    
    Args:
        user_id: Unique identifier for the user
    """
    _current_user_id.value = user_id


def get_current_user() -> str:
    """
    Get the current user ID for the current thread.
    
    Returns:
        User ID or 'anonymous' if not set
    """
    return getattr(_current_user_id, 'value', 'anonymous')


def get_context(user_id: str = None) -> ORContext:
    """
    Get the OR context for a user.
    
    Args:
        user_id: Optional user ID. If not provided, uses current thread's user.
        
    Returns:
        ORContext instance for the user
    """
    if user_id is None:
        user_id = get_current_user()
    return ORContextManager.get_context(user_id)
