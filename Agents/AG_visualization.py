"""
Visualization Agent
Provides visualization capabilities for VRP instances and solutions.
"""

from agents import Agent, function_tool
from azure import model
from Agents.shared_context import get_context
import json
import base64
from io import BytesIO

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


@function_tool
def visualize_instance(instance_json: str = None) -> str:
    """
    Create a visualization of the VRP instance showing customer locations and depot.
    
    Args:
        instance_json: Optional JSON string of instance. If not provided, uses context.
    
    Returns:
        Base64 encoded PNG image or text description if matplotlib unavailable.
    """
    if not HAS_MATPLOTLIB:
        return "Matplotlib not available. Install with: pip install matplotlib"
    
    # Get instance from context if not provided
    if instance_json is None:
        ctx = get_context()
        if not ctx.has_instance():
            return "No instance available. Please generate or load an instance first."
        instance = ctx.get_instance()
    else:
        instance = json.loads(instance_json)
    
    coords = instance['coordinates']
    tw = instance['time_windows']
    demands = instance['demands']
    n = len(coords)
    
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    
    # Plot depot
    ax.scatter(coords[0][0], coords[0][1], c='red', s=200, marker='s', 
               label='Depot', zorder=5, edgecolors='black', linewidth=2)
    
    # Plot customers
    for i in range(1, n):
        ax.scatter(coords[i][0], coords[i][1], c='blue', s=100 + demands[i]*20, 
                   marker='o', zorder=4, edgecolors='black', alpha=0.7)
        ax.annotate(f'{i}\nTW:{tw[i][0]}-{tw[i][1]}\nD:{demands[i]}', 
                    (coords[i][0], coords[i][1]), 
                    textcoords="offset points", xytext=(5, 5), fontsize=8)
    
    ax.set_xlabel('X Coordinate')
    ax.set_ylabel('Y Coordinate')
    ax.set_title(f'VRP Instance: {n-1} customers, {instance["n_vehicles"]} vehicles')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Save to base64
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    
    return f"![VRP Instance](data:image/png;base64,{img_base64})"


@function_tool
def visualize_solution(solution_json: str = None, instance_json: str = None) -> str:
    """
    Create a visualization of the VRP solution showing routes.
    
    Args:
        solution_json: Optional JSON string of solution.
        instance_json: Optional JSON string of instance.
    
    Returns:
        Base64 encoded PNG image or text description.
    """
    if not HAS_MATPLOTLIB:
        return "Matplotlib not available. Install with: pip install matplotlib"
    
    ctx = get_context()
    
    # Get instance
    if instance_json is None:
        if not ctx.has_instance():
            return "No instance available."
        instance = ctx.get_instance()
    else:
        instance = json.loads(instance_json)
    
    # Get solution
    if solution_json is None:
        if not ctx.has_solution():
            return "No solution available. Please solve the instance first."
        solution = ctx.get_solution()
    else:
        solution = json.loads(solution_json)
    
    coords = instance['coordinates']
    routes = solution.get('routes', [])
    
    if not routes:
        return "No routes in solution."
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 9))
    
    # Color palette for routes
    colors = plt.cm.Set1(range(len(routes)))
    
    # Plot routes
    for idx, route in enumerate(routes):
        route_coords = [coords[v] for v in route]
        xs = [c[0] for c in route_coords]
        ys = [c[1] for c in route_coords]
        
        ax.plot(xs, ys, c=colors[idx], linewidth=2, alpha=0.7, 
                label=f'Route {idx+1}', marker='o', markersize=8)
        
        # Add arrows for direction
        for i in range(len(route) - 1):
            dx = coords[route[i+1]][0] - coords[route[i]][0]
            dy = coords[route[i+1]][1] - coords[route[i]][1]
            ax.annotate('', xy=(coords[route[i+1]][0], coords[route[i+1]][1]),
                        xytext=(coords[route[i]][0], coords[route[i]][1]),
                        arrowprops=dict(arrowstyle='->', color=colors[idx], lw=1.5))
    
    # Plot depot
    ax.scatter(coords[0][0], coords[0][1], c='red', s=300, marker='s', 
               zorder=10, edgecolors='black', linewidth=3, label='Depot')
    
    # Annotate customers
    for i in range(1, len(coords)):
        ax.annotate(str(i), (coords[i][0], coords[i][1]), 
                    textcoords="offset points", xytext=(5, 5), fontsize=10, fontweight='bold')
    
    ax.set_xlabel('X Coordinate')
    ax.set_ylabel('Y Coordinate')
    total_cost = solution.get('total_cost', 0)
    ax.set_title(f'VRP Solution: {len(routes)} routes, Total Cost: {total_cost:.2f}')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    # Save to base64
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    
    return f"![VRP Solution](data:image/png;base64,{img_base64})"


@function_tool  
def visualize_gantt_schedule(solution_json: str = None, instance_json: str = None) -> str:
    """
    Create a Gantt chart showing the time schedule for each route.
    
    Args:
        solution_json: Optional JSON string of solution.
        instance_json: Optional JSON string of instance.
    
    Returns:
        Base64 encoded PNG image.
    """
    if not HAS_MATPLOTLIB:
        return "Matplotlib not available."
    
    ctx = get_context()
    
    if instance_json is None:
        if not ctx.has_instance():
            return "No instance available."
        instance = ctx.get_instance()
    else:
        instance = json.loads(instance_json)
    
    if solution_json is None:
        if not ctx.has_solution():
            return "No solution available."
        solution = ctx.get_solution()
    else:
        solution = json.loads(solution_json)
    
    routes = solution.get('routes', [])
    schedules = solution.get('schedules', [])
    tw = instance['time_windows']
    
    if not schedules:
        return "No schedule information in solution."
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 6))
    
    colors = plt.cm.Set2(range(len(routes)))
    
    for idx, (route, schedule) in enumerate(zip(routes, schedules)):
        y = idx
        
        for i, (vertex, arrival) in enumerate(zip(route[1:-1], schedule[1:-1])):
            # Draw time window
            ax.barh(y, tw[vertex][1] - tw[vertex][0], left=tw[vertex][0], 
                    height=0.3, color='lightgray', alpha=0.5)
            
            # Draw service
            service_time = instance['service_times'][vertex]
            ax.barh(y, service_time, left=arrival, height=0.6, 
                    color=colors[idx], edgecolor='black')
            
            ax.text(arrival + service_time/2, y, str(vertex), 
                    ha='center', va='center', fontsize=8)
    
    ax.set_yticks(range(len(routes)))
    ax.set_yticklabels([f'Route {i+1}' for i in range(len(routes))])
    ax.set_xlabel('Time')
    ax.set_title('Route Schedules (Gantt Chart)')
    ax.grid(True, axis='x', alpha=0.3)
    
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    
    return f"![Gantt Schedule](data:image/png;base64,{img_base64})"


@function_tool
def get_context_status() -> str:
    """
    Get the current status of the shared OR context.
    
    Returns:
        Status string showing loaded instance and solution info.
    """
    return get_context().get_status()


# Create the Visualization Agent
visualization_agent = Agent(
    name="Visualization Agent",
    instructions="""You are an expert in visualizing Operations Research problems and solutions.

Your capabilities:
1. Create visual maps of VRP instances showing customer locations, demands, and time windows
2. Visualize routing solutions with colored routes and direction arrows
3. Generate Gantt charts showing time schedules for each route
4. Show the current context status (loaded instance/solution)

When visualizing:
- Use visualize_instance to show the problem setup
- Use visualize_solution to show the routing plan
- Use visualize_gantt_schedule to show timing details
- Use get_context_status to check what data is available

The visualizations help users understand:
- Geographic distribution of customers
- How routes are organized
- Whether time windows are being respected
- Overall solution quality

Always explain what the visualization shows and highlight key insights.""",
    tools=[
        visualize_instance,
        visualize_solution,
        visualize_gantt_schedule,
        get_context_status
    ],
    model=model
)
