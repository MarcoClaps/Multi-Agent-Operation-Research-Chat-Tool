"""
Code Editor Agent
An agent that can analyze, modify, and generate Python code for OR problems.
"""

import re
import ast
import json
from typing import Optional


class CodeEditorAgent:
    """Agent for editing and analyzing Python code related to OR problems."""
    
    def __init__(self):
        self.supported_operations = [
            "analyze_code",
            "modify_parameters",
            "add_constraint",
            "remove_constraint",
            "change_objective",
            "extract_model_info",
            "generate_template"
        ]
    
    def analyze_code(self, code: str) -> dict:
        """
        Analyze Python code and extract information about the optimization model.
        
        Args:
            code: Python source code as string
            
        Returns:
            Dictionary with analysis results
        """
        analysis = {
            "variables": [],
            "constraints": [],
            "objective": None,
            "imports": [],
            "functions": [],
            "syntax_valid": True,
            "errors": []
        }
        
        # Check syntax
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            analysis["syntax_valid"] = False
            analysis["errors"].append(f"Syntax error at line {e.lineno}: {e.msg}")
            return analysis
        
        # Extract imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    analysis["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                analysis["imports"].append(f"{node.module}")
            elif isinstance(node, ast.FunctionDef):
                analysis["functions"].append(node.name)
        
        # Pattern matching for PuLP/MIP variables
        var_patterns = [
            r'LpVariable\s*\(\s*["\'](\w+)["\']',  # PuLP
            r'model\.add_var\s*\([^)]*name\s*=\s*["\'](\w+)["\']',  # python-mip
        ]
        
        for pattern in var_patterns:
            matches = re.findall(pattern, code)
            analysis["variables"].extend(matches)
        
        # Pattern matching for constraints
        constraint_pattern = r'model\s*\+=.*,\s*["\'](\w+)["\']'
        analysis["constraints"] = re.findall(constraint_pattern, code)
        
        # Check for objective
        if "LpMinimize" in code or "minimize" in code.lower():
            analysis["objective"] = "minimize"
        elif "LpMaximize" in code or "maximize" in code.lower():
            analysis["objective"] = "maximize"
        
        return analysis
    
    def modify_parameters(self, code: str, param_name: str, new_value: str) -> str:
        """
        Modify a parameter value in the code.
        
        Args:
            code: Original code
            param_name: Name of the parameter to modify
            new_value: New value for the parameter
            
        Returns:
            Modified code
        """
        # Pattern to find parameter assignments
        pattern = rf'({param_name}\s*=\s*)([^\n]+)'
        
        def replacer(match):
            return f"{match.group(1)}{new_value}"
        
        modified_code = re.sub(pattern, replacer, code)
        return modified_code
    
    def add_constraint(self, code: str, constraint_code: str, constraint_name: str) -> str:
        """
        Add a new constraint to the optimization model.
        
        Args:
            code: Original code
            constraint_code: The constraint expression (e.g., "lpSum(x[i] for i in range(n)) <= 10")
            constraint_name: Name for the constraint
            
        Returns:
            Modified code with new constraint
        """
        # Find the last constraint or objective line
        lines = code.split('\n')
        insert_index = None
        
        for i, line in enumerate(lines):
            if 'model +=' in line or 'model.addConstr' in line:
                insert_index = i + 1
        
        if insert_index is None:
            # If no constraints found, find the solve line
            for i, line in enumerate(lines):
                if '.solve(' in line or '.optimize(' in line:
                    insert_index = i
                    break
        
        if insert_index:
            new_constraint = f'    model += {constraint_code}, "{constraint_name}"'
            lines.insert(insert_index, new_constraint)
        
        return '\n'.join(lines)
    
    def remove_constraint(self, code: str, constraint_name: str) -> str:
        """
        Remove a constraint from the code by name.
        
        Args:
            code: Original code
            constraint_name: Name of constraint to remove
            
        Returns:
            Modified code without the constraint
        """
        lines = code.split('\n')
        filtered_lines = []
        
        for line in lines:
            if f'"{constraint_name}"' not in line and f"'{constraint_name}'" not in line:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def change_objective(self, code: str, new_sense: str) -> str:
        """
        Change the optimization sense (minimize/maximize).
        
        Args:
            code: Original code
            new_sense: "minimize" or "maximize"
            
        Returns:
            Modified code
        """
        if new_sense.lower() == "minimize":
            code = code.replace("LpMaximize", "LpMinimize")
            code = code.replace("maximize", "minimize")
        else:
            code = code.replace("LpMinimize", "LpMaximize")
            code = code.replace("minimize", "maximize")
        
        return code
    
    def extract_model_info(self, code: str) -> dict:
        """
        Extract detailed model information from the code.
        
        Returns:
            Dictionary with model details
        """
        info = {
            "problem_type": "unknown",
            "solver": "unknown",
            "num_variables_approx": 0,
            "num_constraints_approx": 0,
            "has_time_limit": False,
            "has_capacity_constraints": False,
            "has_time_windows": False
        }
        
        # Detect problem type
        if "VRPTW" in code or "time_window" in code.lower():
            info["problem_type"] = "VRPTW"
            info["has_time_windows"] = True
        elif "VRP" in code:
            info["problem_type"] = "VRP"
        elif "TSP" in code:
            info["problem_type"] = "TSP"
        
        # Detect solver
        if "PULP_CBC_CMD" in code or "CBC" in code:
            info["solver"] = "CBC (COIN-OR)"
        elif "GUROBI" in code:
            info["solver"] = "Gurobi"
        elif "CPLEX" in code:
            info["solver"] = "CPLEX"
        elif "python-mip" in code or "from mip" in code:
            info["solver"] = "python-mip (CBC)"
        
        # Count variables and constraints
        info["num_variables_approx"] = len(re.findall(r'LpVariable|add_var', code))
        info["num_constraints_approx"] = len(re.findall(r'model\s*\+=', code))
        
        # Check for features
        if "timeLimit" in code or "max_seconds" in code:
            info["has_time_limit"] = True
        if "capacity" in code.lower() or "load" in code.lower():
            info["has_capacity_constraints"] = True
        
        return info
    
    def generate_template(self, problem_type: str) -> str:
        """
        Generate a code template for a given problem type.
        
        Args:
            problem_type: Type of problem (VRP, TSP, VRPTW, etc.)
            
        Returns:
            Code template as string
        """
        templates = {
            "TSP": self._tsp_template(),
            "VRP": self._vrp_template(),
            "VRPTW": self._vrptw_template(),
            "KNAPSACK": self._knapsack_template()
        }
        
        return templates.get(problem_type.upper(), "# Unknown problem type")
    
    def _tsp_template(self) -> str:
        return '''"""
Traveling Salesman Problem (TSP) - MTZ Formulation
"""
from pulp import LpProblem, LpMinimize, LpVariable, LpBinary, LpContinuous, lpSum, PULP_CBC_CMD

def solve_tsp(n, cost_matrix):
    model = LpProblem("TSP", LpMinimize)
    
    # Variables
    x = {(i, j): LpVariable(f"x_{i}_{j}", cat=LpBinary)
         for i in range(n) for j in range(n) if i != j}
    u = {i: LpVariable(f"u_{i}", lowBound=0, upBound=n-1, cat=LpContinuous)
         for i in range(1, n)}
    
    # Objective
    model += lpSum(cost_matrix[i][j] * x[i, j] for i in range(n) for j in range(n) if i != j)
    
    # Each city visited once
    for j in range(n):
        model += lpSum(x[i, j] for i in range(n) if i != j) == 1
    for i in range(n):
        model += lpSum(x[i, j] for j in range(n) if i != j) == 1
    
    # MTZ subtour elimination
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                model += u[i] - u[j] + n * x[i, j] <= n - 1
    
    model.solve(PULP_CBC_CMD(msg=0))
    return model
'''
    
    def _vrp_template(self) -> str:
        return '''"""
Vehicle Routing Problem (VRP) - Basic Formulation
"""
from pulp import LpProblem, LpMinimize, LpVariable, LpBinary, lpSum, PULP_CBC_CMD

def solve_vrp(n, K, cost_matrix, demands, capacity):
    model = LpProblem("VRP", LpMinimize)
    
    # Variables
    x = {(i, j): LpVariable(f"x_{i}_{j}", cat=LpBinary)
         for i in range(n) for j in range(n) if i != j}
    
    # Objective
    model += lpSum(cost_matrix[i][j] * x[i, j] for i in range(n) for j in range(n) if i != j)
    
    # Visit each customer once
    for j in range(1, n):
        model += lpSum(x[i, j] for i in range(n) if i != j) == 1
    for i in range(1, n):
        model += lpSum(x[i, j] for j in range(n) if i != j) == 1
    
    # Vehicle limit at depot
    model += lpSum(x[0, j] for j in range(1, n)) <= K
    
    model.solve(PULP_CBC_CMD(msg=0))
    return model
'''
    
    def _vrptw_template(self) -> str:
        return '''"""
VRP with Time Windows (VRPTW) - MTZ Formulation
"""
from pulp import LpProblem, LpMinimize, LpVariable, LpBinary, LpContinuous, lpSum, PULP_CBC_CMD

def solve_vrptw(n, K, cost_matrix, time_windows, service_times, demands, capacity):
    model = LpProblem("VRPTW", LpMinimize)
    M = 10000  # Big-M
    
    # Variables
    x = {(i, j): LpVariable(f"x_{i}_{j}", cat=LpBinary)
         for i in range(n) for j in range(n) if i != j}
    t = {i: LpVariable(f"t_{i}", lowBound=time_windows[i][0], upBound=time_windows[i][1])
         for i in range(n)}
    
    # Objective
    model += lpSum(cost_matrix[i][j] * x[i, j] for i in range(n) for j in range(n) if i != j)
    
    # Constraints (add your constraints here)
    # ...
    
    model.solve(PULP_CBC_CMD(msg=0))
    return model
'''
    
    def _knapsack_template(self) -> str:
        return '''"""
0-1 Knapsack Problem
"""
from pulp import LpProblem, LpMaximize, LpVariable, LpBinary, lpSum, PULP_CBC_CMD

def solve_knapsack(values, weights, capacity):
    n = len(values)
    model = LpProblem("Knapsack", LpMaximize)
    
    # Variables
    x = {i: LpVariable(f"x_{i}", cat=LpBinary) for i in range(n)}
    
    # Objective: maximize value
    model += lpSum(values[i] * x[i] for i in range(n))
    
    # Capacity constraint
    model += lpSum(weights[i] * x[i] for i in range(n)) <= capacity
    
    model.solve(PULP_CBC_CMD(msg=0))
    return model
'''
    
    def process_request(self, request: dict) -> dict:
        """
        Process an agent request.
        
        Args:
            request: Dictionary with 'operation' and 'params' keys
            
        Returns:
            Result dictionary
        """
        operation = request.get("operation")
        params = request.get("params", {})
        
        if operation not in self.supported_operations:
            return {"error": f"Unknown operation: {operation}", "supported": self.supported_operations}
        
        try:
            if operation == "analyze_code":
                result = self.analyze_code(params.get("code", ""))
            elif operation == "modify_parameters":
                result = self.modify_parameters(
                    params.get("code", ""),
                    params.get("param_name", ""),
                    params.get("new_value", "")
                )
            elif operation == "add_constraint":
                result = self.add_constraint(
                    params.get("code", ""),
                    params.get("constraint_code", ""),
                    params.get("constraint_name", "")
                )
            elif operation == "remove_constraint":
                result = self.remove_constraint(
                    params.get("code", ""),
                    params.get("constraint_name", "")
                )
            elif operation == "change_objective":
                result = self.change_objective(
                    params.get("code", ""),
                    params.get("new_sense", "minimize")
                )
            elif operation == "extract_model_info":
                result = self.extract_model_info(params.get("code", ""))
            elif operation == "generate_template":
                result = self.generate_template(params.get("problem_type", "TSP"))
            else:
                result = {"error": "Operation not implemented"}
            
            return {"success": True, "result": result}
        
        except Exception as e:
            return {"success": False, "error": str(e)}


# Example usage
if __name__ == "__main__":
    agent = CodeEditorAgent()
    
    # Test: Generate a template
    print("=== Generate VRPTW Template ===")
    template = agent.generate_template("VRPTW")
    print(template[:500] + "...")
    
    # Test: Analyze the template
    print("\n=== Analyze Code ===")
    analysis = agent.analyze_code(template)
    print(json.dumps(analysis, indent=2))
    
    # Test: Extract model info
    print("\n=== Extract Model Info ===")
    info = agent.extract_model_info(template)
    print(json.dumps(info, indent=2))
    
    # Test: Process a request
    print("\n=== Process Request ===")
    request = {
        "operation": "generate_template",
        "params": {"problem_type": "KNAPSACK"}
    }
    response = agent.process_request(request)
    print(f"Success: {response['success']}")
    print(response['result'][:300] + "...")
