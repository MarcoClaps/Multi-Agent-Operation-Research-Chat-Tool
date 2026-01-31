"""
Instance Generator Agent
Wraps the instance generation functions as an OpenAI Agents SDK agent.
"""

from agents import Agent, function_tool
from Agents.instance_gen import generate_vrp_instance, save_instance, print_instance
from Agents.shared_context import get_context
from Agents.guardrails import InstanceParameterGuardrail, format_validation_result
from azure import model
import json


@function_tool
def create_vrp_instance(n_customers: int = 9, seed: int = 42) -> str:
    """
    Generate a new VRP instance with time windows and store it in shared context.
    
    Args:
        n_customers: Number of customers (excluding depot). Default is 9. Max is 100.
        seed: Random seed for reproducibility. Default is 42.
    
    Returns:
        JSON string containing the generated instance data, or error if validation fails.
    """
    # Validate parameters
    validation = InstanceParameterGuardrail.validate_instance_params(
        n_customers=n_customers,
        seed=seed
    )
    
    if not validation.is_valid:
        # Use corrected values if available
        if validation.corrected_values:
            n_customers = validation.corrected_values.get('n_customers', n_customers)
            seed = validation.corrected_values.get('seed', seed)
        else:
            return f"❌ Invalid parameters:\n{format_validation_result(validation)}"
    
    # Generate instance
    instance = generate_vrp_instance(n_customers=n_customers, seed=seed)
    
    # Store in shared context
    ctx = get_context()
    ctx.set_instance(instance, name=f"vrp_{n_customers}c_seed{seed}")
    
    # Build response with any warnings
    response = json.dumps(instance, indent=2)
    
    if validation.warnings:
        warnings = "\n".join(f"⚠️ {w}" for w in validation.warnings)
        response = f"{warnings}\n\n{response}"
    
    return response


@function_tool
def save_vrp_instance(instance_json: str = None, filename: str = "vrp_instance.json") -> str:
    """
    Save a VRP instance to a JSON file.
    
    Args:
        instance_json: The instance data as a JSON string. If not provided, uses context.
        filename: The filename to save to. Default is 'vrp_instance.json'.
    
    Returns:
        Confirmation message.
    """
    ctx = get_context()
    
    if instance_json is None:
        # Use instance from context
        return ctx.save_instance(filename)
    else:
        instance = json.loads(instance_json)
        ctx.set_instance(instance)  # Also update context
        return ctx.save_instance(filename)


@function_tool
def get_instance_summary(instance_json: str) -> str:
    """
    Get a formatted summary of a VRP instance.
    
    Args:
        instance_json: The instance data as a JSON string.
    
    Returns:
        Formatted summary string.
    """
    instance = json.loads(instance_json)
    
    summary = []
    summary.append("=" * 50)
    summary.append("VRP Instance with Time Windows")
    summary.append("=" * 50)
    summary.append(f"Number of vertices: {instance['n_vertices']}")
    summary.append(f"Number of customers: {instance['n_customers']}")
    summary.append(f"Number of vehicles: {instance['n_vehicles']}")
    summary.append(f"Vehicle capacity: {instance['vehicle_capacity']}")
    summary.append("\nVertices:")
    summary.append("-" * 50)
    summary.append(f"{'ID':<8} {'Coord':<20} {'TW':<15} {'Service':<8} {'Demand':<6}")
    summary.append("-" * 50)
    
    for i in range(instance['n_vertices']):
        coord = f"({instance['coordinates'][i][0]:.1f}, {instance['coordinates'][i][1]:.1f})"
        tw = f"[{instance['time_windows'][i][0]}, {instance['time_windows'][i][1]}]"
        vertex_type = "Depot" if i == 0 else f"Cust {i}"
        summary.append(f"{vertex_type:<8} {coord:<20} {tw:<15} {instance['service_times'][i]:<8} {instance['demands'][i]:<6}")
    
    return "\n".join(summary)


@function_tool
def modify_instance_parameter(instance_json: str, parameter: str, value: str) -> str:
    """
    Modify a parameter in an existing VRP instance.
    
    Args:
        instance_json: The instance data as a JSON string.
        parameter: The parameter to modify (e.g., 'n_vehicles', 'vehicle_capacity').
        value: The new value for the parameter.
    
    Returns:
        Modified instance as JSON string.
    """
    instance = json.loads(instance_json)
    
    if parameter in instance:
        # Try to convert to appropriate type
        try:
            if isinstance(instance[parameter], int):
                instance[parameter] = int(value)
            elif isinstance(instance[parameter], float):
                instance[parameter] = float(value)
            else:
                instance[parameter] = value
        except ValueError:
            instance[parameter] = value
        
        return json.dumps(instance, indent=2)
    else:
        return f"Error: Parameter '{parameter}' not found in instance. Available: {list(instance.keys())}"


# Create the Instance Generator Agent
instance_generator_agent = Agent(
    name="Instance Generator Agent",
    instructions="""You are an expert in generating Vehicle Routing Problem (VRP) instances.
    
Your capabilities:
1. Generate new VRP instances with customizable parameters (number of customers, random seed)
2. Save instances to JSON files
3. Provide summaries of instance data
4. Modify instance parameters

When a user asks to create or modify a VRP instance:
- Use create_vrp_instance to generate new instances
- Use get_instance_summary to show instance details
- Use save_vrp_instance to persist instances to disk
- Use modify_instance_parameter to change specific values

Always provide clear explanations of the generated data and its meaning for optimization.""",
    tools=[
        create_vrp_instance,
        save_vrp_instance,
        get_instance_summary,
        modify_instance_parameter
    ],
    model=model
)
