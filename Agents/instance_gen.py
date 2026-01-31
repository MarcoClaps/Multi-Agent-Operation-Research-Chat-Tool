"""
VRP Instance Generator with Time Windows
Creates a simple instance with 10 vertices (1 depot + 9 customers)
"""

import json
import random
import numpy as np

def generate_vrp_instance(n_customers=9, seed=42):
    """
    Generate a VRP instance with time windows.
    
    Args:
        n_customers: Number of customers (excluding depot)
        seed: Random seed for reproducibility
    
    Returns:
        Dictionary containing the VRP instance data
    """
    random.seed(seed)
    np.random.seed(seed)
    
    n_vertices = n_customers + 1  # Including depot (index 0)
    
    # Generate random coordinates for vertices
    coordinates = [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(n_vertices)]
    
    # Depot at center
    coordinates[0] = (50, 50)
    
    # Calculate Euclidean distance matrix (costs)
    cost_matrix = np.zeros((n_vertices, n_vertices))
    for i in range(n_vertices):
        for j in range(n_vertices):
            if i != j:
                dx = coordinates[i][0] - coordinates[j][0]
                dy = coordinates[i][1] - coordinates[j][1]
                cost_matrix[i][j] = round(np.sqrt(dx**2 + dy**2), 2)
    
    # Generate time windows
    # Depot has wide time window
    time_windows = [(0, 1000)]  # Depot
    
    for i in range(1, n_vertices):
        # Random early time between 0 and 500
        early = random.randint(0, 500)
        # Late time is early + random window size (50-200)
        window_size = random.randint(50, 200)
        late = early + window_size
        time_windows.append((early, late))
    
    # Service times at each vertex
    service_times = [0]  # Depot has no service time
    for i in range(1, n_vertices):
        service_times.append(random.randint(5, 20))
    
    # Demands at each vertex
    demands = [0]  # Depot has no demand
    for i in range(1, n_vertices):
        demands.append(random.randint(1, 10))
    
    # Vehicle capacity
    vehicle_capacity = 30
    
    # Number of vehicles
    n_vehicles = 3
    
    instance = {
        "n_vertices": n_vertices,
        "n_customers": n_customers,
        "n_vehicles": n_vehicles,
        "vehicle_capacity": vehicle_capacity,
        "coordinates": coordinates,
        "cost_matrix": cost_matrix.tolist(),
        "time_windows": time_windows,
        "service_times": service_times,
        "demands": demands
    }
    
    return instance

def save_instance(instance, filename="vrp_instance.json"):
    """Save instance to JSON file."""
    with open(filename, 'w') as f:
        json.dump(instance, f, indent=2)
    print(f"Instance saved to {filename}")

def print_instance(instance):
    """Print instance summary."""
    print("=" * 50)
    print("VRP Instance with Time Windows")
    print("=" * 50)
    print(f"Number of vertices: {instance['n_vertices']}")
    print(f"Number of customers: {instance['n_customers']}")
    print(f"Number of vehicles: {instance['n_vehicles']}")
    print(f"Vehicle capacity: {instance['vehicle_capacity']}")
    print("\nVertices:")
    print("-" * 50)
    print(f"{'ID':<4} {'Coord':<20} {'TW':<15} {'Service':<8} {'Demand':<6}")
    print("-" * 50)
    for i in range(instance['n_vertices']):
        coord = f"({instance['coordinates'][i][0]:.1f}, {instance['coordinates'][i][1]:.1f})"
        tw = f"[{instance['time_windows'][i][0]}, {instance['time_windows'][i][1]}]"
        vertex_type = "Depot" if i == 0 else f"Cust {i}"
        print(f"{vertex_type:<4} {coord:<20} {tw:<15} {instance['service_times'][i]:<8} {instance['demands'][i]:<6}")
    
    print("\nCost Matrix (first 5x5):")
    print("-" * 50)
    for i in range(min(5, instance['n_vertices'])):
        row = [f"{instance['cost_matrix'][i][j]:.1f}" for j in range(min(5, instance['n_vertices']))]
        print("  ".join(f"{val:>6}" for val in row))

if __name__ == "__main__":
    # Generate instance
    instance = generate_vrp_instance(n_customers=9, seed=42)
    
    # Print summary
    print_instance(instance)
    
    # Save to file
    save_instance(instance, "vrp_instance.json")