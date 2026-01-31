"""
Code Editor Agent
Wraps the code editing functions as an OpenAI Agents SDK agent.
"""

from agents import Agent, function_tool
from Agents.code_editor import CodeEditorAgent
from Agents.guardrails import CodeSafetyGuardrail
from azure import model
import json

# Initialize the code editor
_editor = CodeEditorAgent()


def _check_code_safety(code: str) -> tuple[bool, str]:
    """Helper to check code safety and return status + message."""
    result = CodeSafetyGuardrail.validate_code(code)
    if not result.is_safe:
        issues = "\n".join(f"  - {p}" for p in result.dangerous_patterns)
        return False, f"⚠️ **Code safety check failed:**\n{issues}"
    return True, ""


@function_tool
def analyze_optimization_code(code: str) -> str:
    """
    Analyze Python optimization code and extract model information.
    
    Args:
        code: Python source code as a string.
    
    Returns:
        JSON string with analysis results including variables, constraints, imports, etc.
    """
    # Check code safety first
    is_safe, safety_msg = _check_code_safety(code)
    if not is_safe:
        return safety_msg
    
    analysis = _editor.analyze_code(code)
    return json.dumps(analysis, indent=2)


@function_tool
def modify_code_parameter(code: str, param_name: str, new_value: str) -> str:
    """
    Modify a parameter value in Python code.
    
    Args:
        code: Original Python code.
        param_name: Name of the parameter to modify.
        new_value: New value for the parameter.
    
    Returns:
        Modified code as a string.
    """
    # Check input code safety
    is_safe, safety_msg = _check_code_safety(code)
    if not is_safe:
        return safety_msg
    
    modified = _editor.modify_parameters(code, param_name, new_value)
    
    # Check output code safety
    is_safe, safety_msg = _check_code_safety(modified)
    if not is_safe:
        return f"❌ Modification would create unsafe code:\n{safety_msg}"
    
    return modified


@function_tool
def add_model_constraint(code: str, constraint_expression: str, constraint_name: str) -> str:
    """
    Add a new constraint to an optimization model in the code.
    
    Args:
        code: Original Python code.
        constraint_expression: The constraint expression (e.g., "lpSum(x[i] for i in range(n)) <= 10").
        constraint_name: Name for the constraint.
    
    Returns:
        Modified code with the new constraint added.
    """
    # Check input code safety
    is_safe, safety_msg = _check_code_safety(code)
    if not is_safe:
        return safety_msg
    
    # Check constraint expression for dangerous patterns
    is_safe, safety_msg = _check_code_safety(constraint_expression)
    if not is_safe:
        return f"❌ Constraint expression contains unsafe code:\n{safety_msg}"
    
    modified = _editor.add_constraint(code, constraint_expression, constraint_name)
    return modified


@function_tool
def remove_model_constraint(code: str, constraint_name: str) -> str:
    """
    Remove a constraint from the optimization model by name.
    
    Args:
        code: Original Python code.
        constraint_name: Name of the constraint to remove.
    
    Returns:
        Modified code without the specified constraint.
    """
    return _editor.remove_constraint(code, constraint_name)


@function_tool
def change_optimization_sense(code: str, new_sense: str) -> str:
    """
    Change the optimization objective sense (minimize/maximize).
    
    Args:
        code: Original Python code.
        new_sense: Either "minimize" or "maximize".
    
    Returns:
        Modified code with the new optimization sense.
    """
    return _editor.change_objective(code, new_sense)


@function_tool
def extract_model_details(code: str) -> str:
    """
    Extract detailed information about an optimization model from code.
    
    Args:
        code: Python source code as a string.
    
    Returns:
        JSON string with model details (problem type, solver, features, etc.).
    """
    info = _editor.extract_model_info(code)
    return json.dumps(info, indent=2)


@function_tool
def generate_problem_template(problem_type: str) -> str:
    """
    Generate a code template for a specific optimization problem type.
    
    Args:
        problem_type: Type of problem - one of: TSP, VRP, VRPTW, KNAPSACK
    
    Returns:
        Python code template for the specified problem.
    """
    return _editor.generate_template(problem_type)


@function_tool
def list_available_templates() -> str:
    """
    List all available problem templates.
    
    Returns:
        Description of available templates.
    """
    templates = """Available Problem Templates:

1. TSP (Traveling Salesman Problem)
   - Classic single-vehicle routing problem
   - MTZ formulation for subtour elimination
   - Minimizes total travel distance

2. VRP (Vehicle Routing Problem)
   - Multiple vehicles, single depot
   - Basic capacity constraints
   - Flow conservation constraints

3. VRPTW (VRP with Time Windows)
   - Multiple vehicles with time windows
   - MTZ subtour elimination
   - Service time and capacity constraints

4. KNAPSACK (0-1 Knapsack Problem)
   - Classic combinatorial optimization
   - Binary selection variables
   - Single capacity constraint

Use generate_problem_template with any of these types to get starter code."""
    return templates


# Create the Code Editor Agent
code_editor_agent = Agent(
    name="Code Editor Agent",
    instructions="""You are an expert in analyzing and modifying Python code for Operations Research problems.

Your capabilities:
1. Analyze optimization code to extract variables, constraints, and model structure
2. Modify parameters in existing code
3. Add or remove constraints from optimization models
4. Change optimization objectives (minimize/maximize)
5. Generate code templates for common OR problems (TSP, VRP, VRPTW, Knapsack)

When working with code:
- Use analyze_optimization_code to understand existing code structure
- Use extract_model_details to identify problem type and solver
- Use modify_code_parameter to change specific values
- Use add_model_constraint/remove_model_constraint to modify constraints
- Use generate_problem_template to create new solver code

Supported problem types for templates:
- TSP: Traveling Salesman Problem
- VRP: Vehicle Routing Problem  
- VRPTW: VRP with Time Windows
- KNAPSACK: 0-1 Knapsack Problem

Always explain your code modifications and ensure the resulting code remains valid Python with correct PuLP/optimization syntax.""",
    tools=[
        analyze_optimization_code,
        modify_code_parameter,
        add_model_constraint,
        remove_model_constraint,
        change_optimization_sense,
        extract_model_details,
        generate_problem_template,
        list_available_templates
    ],
    model=model
)
