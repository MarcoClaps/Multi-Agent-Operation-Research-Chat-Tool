"""
VRP with Time Windows Solver using MTZ Formulation
Two-index formulation with Miller-Tucker-Zemlin subtour elimination constraints
Using PuLP with COIN-OR CBC solver
"""

import json
from pulp import (
    LpProblem, LpMinimize, LpVariable, LpBinary, LpContinuous,
    lpSum, LpStatus, value, PULP_CBC_CMD
)

def load_instance(filename="vrp_instance.json"):
    """Load VRP instance from JSON file."""
    with open(filename, 'r') as f:
        return json.load(f)

def solve_vrptw_mtz(instance):
    """
    Solve VRPTW using two-index MTZ formulation with PuLP + CBC.
    
    Decision variables:
    - x[i][j]: 1 if arc (i,j) is used, 0 otherwise
    - t[i]: arrival time at vertex i
    - u[i]: position of vertex i in the route (for MTZ subtour elimination)
    """
    n = instance['n_vertices']
    K = instance['n_vehicles']
    Q = instance['vehicle_capacity']
    c = instance['cost_matrix']
    tw = instance['time_windows']
    s = instance['service_times']
    d = instance['demands']
    
    # Big-M for time constraints
    M = max(tw[i][1] for i in range(n)) + max(c[i][j] for i in range(n) for j in range(n)) + max(s)
    
    # Create model
    model = LpProblem("VRPTW_MTZ", LpMinimize)
    
    # Decision variables
    # x[i][j] = 1 if we travel from i to j
    x = {(i, j): LpVariable(f"x_{i}_{j}", cat=LpBinary)
         for i in range(n) for j in range(n) if i != j}
    
    # t[i] = arrival time at vertex i
    t = {i: LpVariable(f"t_{i}", lowBound=tw[i][0], upBound=tw[i][1], cat=LpContinuous)
         for i in range(n)}
    
    # u[i] = position in route (MTZ variable) for subtour elimination
    u = {i: LpVariable(f"u_{i}", lowBound=0, upBound=n, cat=LpContinuous)
         for i in range(n)}
    
    # load[i] = cumulative load when arriving at vertex i
    load = {i: LpVariable(f"load_{i}", lowBound=0, upBound=Q, cat=LpContinuous)
            for i in range(n)}
    
    # Objective: minimize total travel cost
    model += lpSum(c[i][j] * x[i, j] for i in range(n) for j in range(n) if i != j)
    
    # Constraints
    
    # 1. Each customer is visited exactly once
    for j in range(1, n):
        model += lpSum(x[i, j] for i in range(n) if i != j) == 1, f"visit_in_{j}"
    
    # 2. Each customer is left exactly once
    for i in range(1, n):
        model += lpSum(x[i, j] for j in range(n) if i != j) == 1, f"visit_out_{i}"
    
    # 3. Flow conservation at depot
    model += lpSum(x[0, j] for j in range(1, n)) <= K, "depot_out"
    model += lpSum(x[i, 0] for i in range(1, n)) <= K, "depot_in"
    model += lpSum(x[0, j] for j in range(1, n)) == lpSum(x[i, 0] for i in range(1, n)), "depot_balance"
    
    # 4. Time window constraints with travel time
    for i in range(n):
        for j in range(1, n):
            if i != j:
                model += t[j] >= t[i] + s[i] + c[i][j] - M * (1 - x[i, j]), f"time_{i}_{j}"
    
    # 5. MTZ subtour elimination constraints
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                model += u[i] - u[j] + n * x[i, j] <= n - 1, f"mtz_{i}_{j}"
    
    # 6. Capacity constraints
    model += load[0] == 0, "load_depot"
    
    for i in range(n):
        for j in range(1, n):
            if i != j:
                model += load[j] >= load[i] + d[j] - Q * (1 - x[i, j]), f"load_{i}_{j}"
    
    # Solve with CBC
    print("Solving VRPTW with MTZ formulation using PuLP + CBC...")
    print(f"Variables: {len(model.variables())}, Constraints: {len(model.constraints)}")
    
    solver = PULP_CBC_CMD(msg=1, timeLimit=300)
    status = model.solve(solver)
    
    return model, x, t, u, status

def extract_solution(model, x, t, instance, status):
    """Extract and print the solution."""
    n = instance['n_vertices']
    
    print("\n" + "=" * 50)
    print("Solution")
    print("=" * 50)
    
    status_str = LpStatus[status]
    print(f"Status: {status_str}")
    
    if status_str not in ["Optimal", "Feasible"]:
        print("No feasible solution found!")
        return None
    
    print(f"Total Cost: {value(model.objective):.2f}")
    
    # Extract routes
    routes = []
    visited = set()
    
    for j in range(1, n):
        if value(x[0, j]) > 0.5 and j not in visited:
            route = [0, j]
            visited.add(j)
            current = j
            
            while current != 0:
                for next_v in range(n):
                    if current != next_v and value(x[current, next_v]) > 0.5:
                        if next_v == 0:
                            route.append(0)
                            current = 0
                        elif next_v not in visited:
                            route.append(next_v)
                            visited.add(next_v)
                            current = next_v
                        break
            
            routes.append(route)
    
    # Print routes
    print(f"\nNumber of routes: {len(routes)}")
    for idx, route in enumerate(routes):
        route_cost = sum(instance['cost_matrix'][route[i]][route[i+1]] for i in range(len(route)-1))
        route_demand = sum(instance['demands'][v] for v in route[1:-1])
        
        print(f"\nRoute {idx + 1}: {' -> '.join(map(str, route))}")
        print(f"  Cost: {route_cost:.2f}")
        print(f"  Total demand: {route_demand}")
        print(f"  Stops: {len(route) - 2}")
        
        print("  Schedule:")
        for v in route:
            if v == 0:
                print(f"    Depot")
            else:
                arrival = value(t[v]) if value(t[v]) is not None else 0
                tw = instance['time_windows'][v]
                print(f"    Customer {v}: arrival={arrival:.1f}, TW=[{tw[0]}, {tw[1]}]")
    
    return routes

def main():
    try:
        instance = load_instance("vrp_instance.json")
        print("Instance loaded successfully!")
    except FileNotFoundError:
        print("Instance file not found. Please run vrp_instance_generator.py first.")
        return
    
    model, x, t, u, status = solve_vrptw_mtz(instance)
    routes = extract_solution(model, x, t, instance, status)
    
    return routes

if __name__ == "__main__":
    main()