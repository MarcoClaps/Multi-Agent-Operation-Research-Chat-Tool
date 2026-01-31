"""
Shared Context Manager for OR Agents
Provides a singleton context that agents can use to share state.
"""

from typing import Optional, Dict, Any
import json
from pathlib import Path


class ORContext:
    """
    Singleton context manager for sharing state between OR agents.
    Stores the current instance, solution, and other shared data.
    """
    _instance: Optional['ORContext'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._current_instance: Optional[Dict[str, Any]] = None
        self._current_solution: Optional[Dict[str, Any]] = None
        self._history: list = []
        self._workspace_path: Path = Path(".")
    
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
        status.append("OR Context Status")
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


# Singleton accessor
def get_context() -> ORContext:
    """Get the shared OR context instance."""
    return ORContext()
