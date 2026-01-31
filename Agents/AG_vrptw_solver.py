"""
VRPTW Solver Agent
Wraps the VRPTW solver functions as an OpenAI Agents SDK agent.
"""

from agents import Agent, function_tool
from Agents.vrptw_solver import load_instance, solve_vrptw_mtz, extract_solution
from Agents.shared_context import get_context
from Agents.guardrails import (
    InstanceParameterGuardrail, 
    SolverGuardrail, 
    format_validation_result
)
from azure import model
from pulp import LpStatus, value
import json


@function_tool
def load_vrp_instance(filename: str = "vrp_instance.json") -> str:
    """
    Load a VRP instance from a JSON file into the shared context.
    
    Args:
        filename: Path to the JSON file containing the instance. Default is 'vrp_instance.json'.
    
    Returns:
        JSON string of the loaded instance or error message.
    """
    ctx = get_context()
    result = ctx.load_instance(filename)
    
    if "Error" in result:
        return result
    
    # Validate loaded instance
    instance = ctx.get_instance()
    validation = InstanceParameterGuardrail.validate_instance_data(instance)
    
    if not validation.is_valid:
        return f"❌ Loaded instance is invalid:\n{format_validation_result(validation)}"
    
    response = ctx.get_instance_json()
    
    if validation.warnings:
        warnings = "\n".join(f"⚠️ {w}" for w in validation.warnings)
        response = f"{warnings}\n\n{response}"
    
    return response


@function_tool
def get_current_instance() -> str:
    """
    Get the currently loaded VRP instance from the shared context.
    
    Returns:
        JSON string of the current instance or error message.
    """
    ctx = get_context()
    return ctx.get_instance_json()


@function_tool
def solve_vrptw(instance_json: str = None, time_limit: int = 300) -> str:
    """
    Solve a VRPTW instance using the MTZ formulation with PuLP + CBC.
    
    Args:
        instance_json: The VRP instance data as JSON. If not provided, uses context.
        time_limit: Maximum solving time in seconds. Default is 300, max is 600.
    
    Returns:
        Solution summary including routes, costs, and schedules.
    """
    ctx = get_context()
    
    # Get instance from context if not provided
    if instance_json is None:
        if not ctx.has_instance():
            return "Error: No instance available. Please generate or load an instance first."
        instance = ctx.get_instance()
    else:
        instance = json.loads(instance_json)
        ctx.set_instance(instance)  # Store in context
    
    # Validate instance structure
    instance_validation = InstanceParameterGuardrail.validate_instance_data(instance)
    if not instance_validation.is_valid:
        return f"❌ Invalid instance:\n{format_validation_result(instance_validation)}"
    
    # Validate solve request
    solve_validation = SolverGuardrail.validate_solve_request(instance, time_limit)
    if not solve_validation.is_valid:
        return f"❌ Cannot solve:\n{format_validation_result(solve_validation)}"
    
    # Apply corrections if any
    if solve_validation.corrected_values:
        time_limit = solve_validation.corrected_values.get('time_limit', time_limit)
    
    # Build warnings header
    warnings_header = ""
    all_warnings = instance_validation.warnings + solve_validation.warnings
    if all_warnings:
        warnings_header = "\n".join(f"⚠️ {w}" for w in all_warnings) + "\n\n"
    
    # Solve the problem
    lp_model, x, t, u, status = solve_vrptw_mtz(instance)
    
    # Build solution report
    n = instance['n_vertices']
    result = []
    
    status_str = LpStatus[status]
    result.append(f"Optimization Status: {status_str}")
    
    if status_str not in ["Optimal", "Feasible"]:
        result.append("No feasible solution found!")
        return "\n".join(result)
    
    total_cost = value(lp_model.objective)
    result.append(f"Total Cost: {total_cost:.2f}")
    
    # Extract routes
    routes = []
    schedules = []
    visited = set()
    
    for j in range(1, n):
        if value(x[0, j]) > 0.5 and j not in visited:
            route = [0, j]
            schedule = [0, value(t[j]) if value(t[j]) else 0]
            visited.add(j)
            current = j
            
            while current != 0:
                for next_v in range(n):
                    if current != next_v and value(x[current, next_v]) > 0.5:
                        if next_v == 0:
                            route.append(0)
                            schedule.append(0)
                            current = 0
                        elif next_v not in visited:
                            route.append(next_v)
                            schedule.append(value(t[next_v]) if value(t[next_v]) else 0)
                            visited.add(next_v)
                            current = next_v
                        break
            
            routes.append(route)
            schedules.append(schedule)
    
    # Store solution in context
    solution = {
        "status": status_str,
        "total_cost": total_cost,
        "routes": routes,
        "schedules": schedules
    }
    ctx.set_solution(solution)
    
    result.append(f"\nNumber of routes: {len(routes)}")
    
    for idx, route in enumerate(routes):
        route_cost = sum(instance['cost_matrix'][route[i]][route[i+1]] for i in range(len(route)-1))
        route_demand = sum(instance['demands'][v] for v in route[1:-1])
        
        result.append(f"\nRoute {idx + 1}: {' -> '.join(map(str, route))}")
        result.append(f"  Cost: {route_cost:.2f}")
        result.append(f"  Total demand: {route_demand}")
        result.append(f"  Stops: {len(route) - 2}")
        
        result.append("  Schedule:")
        for i, v in enumerate(route):
            if v == 0:
                result.append(f"    Depot")
            else:
                arrival = schedules[idx][i]
                tw = instance['time_windows'][v]
                result.append(f"    Customer {v}: arrival={arrival:.1f}, TW=[{tw[0]}, {tw[1]}]")
    
    return "\n".join(result)


@function_tool
def solve_vrptw_from_file(filename: str = "vrp_instance.json", time_limit: int = 300) -> str:
    """
    Load and solve a VRPTW instance from a file.
    
    Args:
        filename: Path to the JSON file containing the instance. Default is 'vrp_instance.json'.
        time_limit: Maximum solving time in seconds. Default is 300.
    
    Returns:
        Solution summary or error message.
    """
    ctx = get_context()
    result = ctx.load_instance(filename)
    
    if "Error" in result:
        return result
    
    return solve_vrptw(time_limit=time_limit)


@function_tool
def get_model_statistics(instance_json: str = None) -> str:
    """
    Get statistics about the optimization model without solving.
    
    Args:
        instance_json: The VRP instance data as JSON. If not provided, uses context.
    
    Returns:
        Model statistics including variable and constraint counts.
    """
    ctx = get_context()
    
    if instance_json is None:
        if not ctx.has_instance():
            return "Error: No instance available."
        instance = ctx.get_instance()
    else:
        instance = json.loads(instance_json)
    
    n = instance['n_vertices']
    
    # Calculate approximate numbers
    n_binary_vars = n * (n - 1)  # x variables
    n_continuous_vars = 3 * n  # t, u, load variables
    n_total_vars = n_binary_vars + n_continuous_vars
    
    # Constraints count (approximate)
    n_visit_constraints = 2 * (n - 1)  # in and out for each customer
    n_depot_constraints = 3  # depot in, out, balance
    n_time_constraints = n * (n - 1)
    n_mtz_constraints = (n - 1) * (n - 2)
    n_load_constraints = n * (n - 1) + 1
    n_total_constraints = n_visit_constraints + n_depot_constraints + n_time_constraints + n_mtz_constraints + n_load_constraints
    
    stats = [
        "=" * 50,
        "VRPTW Model Statistics (MTZ Formulation)",
        "=" * 50,
        f"Instance size: {n} vertices ({n-1} customers + 1 depot)",
        f"Vehicles available: {instance['n_vehicles']}",
        f"Vehicle capacity: {instance['vehicle_capacity']}",
        "",
        "Decision Variables:",
        f"  - Binary (arc) variables: {n_binary_vars}",
        f"  - Continuous (time, position, load): {n_continuous_vars}",
        f"  - Total variables: {n_total_vars}",
        "",
        "Constraints:",
        f"  - Visit constraints: {n_visit_constraints}",
        f"  - Depot constraints: {n_depot_constraints}",
        f"  - Time window constraints: {n_time_constraints}",
        f"  - MTZ subtour elimination: {n_mtz_constraints}",
        f"  - Capacity constraints: {n_load_constraints}",
        f"  - Total constraints: ~{n_total_constraints}",
        "",
        "Formulation: Two-index MTZ with time windows",
        "Solver: COIN-OR CBC (via PuLP)"
    ]
    
    return "\n".join(stats)


# Create the VRPTW Solver Agent
vrptw_solver_agent = Agent(
    name="VRPTW Solver Agent",
    instructions="""You are an expert in solving Vehicle Routing Problems with Time Windows (VRPTW).

Your capabilities:
1. Load VRP instances from JSON files
2. Solve VRPTW using the MTZ (Miller-Tucker-Zemlin) formulation
3. Extract and present solutions with routes, costs, and schedules
4. Provide model statistics and complexity analysis

The solver uses:
- PuLP library with COIN-OR CBC solver
- Two-index formulation with binary arc variables
- MTZ constraints for subtour elimination
- Big-M constraints for time windows

When solving problems:
- First load or receive the instance data
- Use get_model_statistics to show problem size
- Use solve_vrptw or solve_vrptw_from_file to find optimal routes
- Explain the solution in terms of routes, timing, and costs

Always interpret results clearly for the user, explaining what each route means and whether time windows are satisfied.""",
    tools=[
        load_vrp_instance,
        solve_vrptw,
        solve_vrptw_from_file,
        get_model_statistics
    ],
    model=model
)
