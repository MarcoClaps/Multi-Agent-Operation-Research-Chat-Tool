"""
Agents package for OR optimization.
"""

from Agents.AG_instance_gen import instance_generator_agent
from Agents.AG_vrptw_solver import vrptw_solver_agent
from Agents.AG_code_editor import code_editor_agent
from Agents.AG_visualization import visualization_agent
from Agents.shared_context import (
    get_context, 
    ORContext,
    ORContextManager,
    set_current_user,
    get_current_user,
)
from Agents.guardrails import (
    topic_guardrail,
    safety_guardrail,
    professional_output_guardrail,
    InstanceParameterGuardrail,
    SolverGuardrail,
    CodeSafetyGuardrail,
)

__all__ = [
    # Agents
    "instance_generator_agent",
    "vrptw_solver_agent", 
    "code_editor_agent",
    "visualization_agent",
    # Context
    "get_context",
    "ORContext",
    "ORContextManager",
    "set_current_user",
    "get_current_user",
    # Guardrails
    "topic_guardrail",
    "safety_guardrail",
    "professional_output_guardrail",
    "InstanceParameterGuardrail",
    "SolverGuardrail",
    "CodeSafetyGuardrail",
]
