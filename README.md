# 🚚 ORAgent — AI-Powered Operations Research Assistant

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-Agents%20SDK-412991.svg)
![Azure](https://img.shields.io/badge/Azure-OpenAI-0089D6.svg)
![PuLP](https://img.shields.io/badge/PuLP-Optimization-green.svg)
![Chainlit](https://img.shields.io/badge/Chainlit-Chat%20UI-FF6B6B.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**An intelligent multi-agent system for solving Vehicle Routing Problems with Time Windows (VRPTW) using conversational AI**

[Features](#-features) • [Architecture](#-architecture) • [Installation](#-installation) • [Usage](#-usage) • [Demo](#-demo) • [Contributing](#-contributing)

</div>

---

## 📖 Description

**ORAgent** is a cutting-edge conversational AI assistant that brings the power of Operations Research to your fingertips. Built on top of the **OpenAI Agents SDK**, it leverages a sophisticated multi-agent architecture to help users generate, solve, analyze, and visualize **Vehicle Routing Problems with Time Windows (VRPTW)**.

Whether you're a logistics professional, an OR researcher, or a student learning about optimization, ORAgent provides an intuitive natural language interface to tackle complex routing problems without writing a single line of code.

### 🎯 What is VRPTW?

The **Vehicle Routing Problem with Time Windows** is a classic combinatorial optimization problem where:
- A fleet of vehicles must serve a set of customers
- Each customer has a demand and a time window for service
- Vehicles have limited capacity
- The goal is to minimize total travel cost while satisfying all constraints

This problem is NP-hard and has countless real-world applications in logistics, delivery services, field service scheduling, and more.

---

## ✨ Features

### 🤖 Multi-Agent Architecture
- **Orchestrator Agent**: Coordinates the specialized agents and routes user requests
- **Instance Generator Agent**: Creates customizable VRP instances with configurable parameters
- **VRPTW Solver Agent**: Solves problems using the MTZ formulation with PuLP + CBC
- **Code Editor Agent**: Analyzes and modifies optimization code, generates templates
- **Visualization Agent**: Creates beautiful visualizations of instances and solutions

### 🛡️ Advanced Guardrails
- **Topic Guardrail**: Ensures conversations stay focused on Operations Research
- **Safety Guardrail**: Filters inappropriate or harmful content
- **Professional Output Guardrail**: Maintains response quality
- **Parameter Validation**: Validates instance parameters and solver settings
- **Code Safety**: Prevents execution of malicious code patterns

### 📊 Mathematical Optimization
- **MTZ Formulation**: Miller-Tucker-Zemlin subtour elimination constraints
- **Time Windows**: Hard constraints for customer service windows
- **Capacity Constraints**: Vehicle load tracking and enforcement
- **CBC Solver**: Industrial-strength COIN-OR branch-and-cut solver

### 🎨 Visualization Capabilities
- Instance visualization with customer locations and time windows
- Solution visualization with colored routes and direction arrows
- Statistical analysis and charts
- Exportable images in PNG format

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Chainlit UI                             │
│                    (Chat Interface + Auth)                      │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Input Guardrails                             │
│              (Topic + Safety Validation)                        │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   OR Orchestrator Agent                         │
│            (Azure OpenAI GPT-4 / GPT-4o)                        │
│                                                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────┐│
│  │   Instance   │ │    VRPTW     │ │     Code     │ │  Viz    ││
│  │  Generator   │ │    Solver    │ │    Editor    │ │  Agent  ││
│  └──────────────┘ └──────────────┘ └──────────────┘ └─────────┘│
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Output Guardrails                             │
│              (Professional Response Filter)                     │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Shared Context                              │
│         (Singleton State Manager + File I/O)                    │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Responsibilities

| Agent | Responsibility | Key Tools |
|-------|---------------|-----------|
| **Orchestrator** | Routes requests, coordinates workflow | Handoffs to specialized agents |
| **Instance Generator** | Creates VRP instances | `create_vrp_instance`, `save_vrp_instance`, `modify_instance_parameter` |
| **VRPTW Solver** | Solves routing problems | `solve_vrptw`, `load_vrp_instance`, `get_solution_summary` |
| **Code Editor** | Analyzes/modifies code | `analyze_optimization_code`, `add_model_constraint`, `generate_problem_template` |
| **Visualization** | Creates visual outputs | `visualize_instance`, `visualize_solution`, `create_comparison_chart` |

---

## 📁 Project Structure

```
ORAgent/
├── main.py                 # Application entry point & Chainlit handlers
├── azure.py                # Azure OpenAI configuration
├── chainlit.md             # Welcome screen markdown
├── Agents/
│   ├── __init__.py         # Package exports
│   ├── AG_instance_gen.py  # Instance Generator Agent
│   ├── AG_vrptw_solver.py  # VRPTW Solver Agent
│   ├── AG_code_editor.py   # Code Editor Agent
│   ├── AG_visualization.py # Visualization Agent
│   ├── instance_gen.py     # Core instance generation logic
│   ├── vrptw_solver.py     # Core solver implementation (MTZ)
│   ├── code_editor.py      # Code analysis utilities
│   ├── shared_context.py   # Singleton context manager
│   └── guardrails.py       # Input/output guardrails
├── public/
│   ├── custom.css          # UI customization
│   └── img/                # Static images
└── .files/                 # Workspace for generated files
```

---

## 🚀 Installation

### Prerequisites

- Python 3.10 or higher
- Azure OpenAI API access (or OpenAI API)
- pip or conda package manager

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/ORAgent.git
cd ORAgent
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install openai-agents-sdk chainlit pulp numpy matplotlib python-dotenv httpx
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# Chainlit Authentication (Optional)
CHAINLIT_USERNAME=admin
CHAINLIT_PASSWORD=your_secure_password
```

### Step 5: Run the Application

```bash
chainlit run main.py
```

The application will be available at `http://localhost:8000`

---

## 💬 Usage

### Example Conversations

#### Generate a VRP Instance

```
User: Create a VRP instance with 15 customers

ORAgent: I'll generate a VRP instance with 15 customers for you...
✅ Instance created with 15 customers, 3 vehicles, capacity 30
```

#### Solve the Problem

```
User: Solve this routing problem

ORAgent: Solving VRPTW with MTZ formulation...
✅ Optimal solution found!
- Total cost: 342.87
- Routes: 3
  - Route 1: Depot → 3 → 7 → 12 → Depot
  - Route 2: Depot → 1 → 5 → 9 → 15 → Depot
  - Route 3: Depot → 2 → 4 → 6 → 8 → 10 → 11 → 13 → 14 → Depot
```

#### Visualize Results

```
User: Show me a visualization of the solution

ORAgent: Here's the visualization of your VRPTW solution:
[Displays colored route map with arrows]
```

#### Get Code Templates

```
User: Generate a template for the Traveling Salesman Problem

ORAgent: Here's a PuLP template for TSP with MTZ formulation...
[Provides complete Python code]
```

---

## 🔧 Configuration

### Solver Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `time_limit` | 300s | Maximum solving time |
| `n_customers` | 9 | Number of customers (max 100) |
| `n_vehicles` | 3 | Fleet size |
| `vehicle_capacity` | 30 | Maximum load per vehicle |

### Guardrail Settings

The guardrails can be customized in `Agents/guardrails.py`:

- **Topic Keywords**: OR-related terms that keep conversations on track
- **Safety Patterns**: Regex patterns for content filtering
- **Parameter Limits**: Min/max values for instance generation

---

## 🧮 Mathematical Formulation

### MTZ Formulation for VRPTW

**Sets:**
- $V = \{0, 1, ..., n\}$ — vertices (0 is depot)
- $K$ — set of vehicles

**Decision Variables:**
- $x_{ij} \in \{0, 1\}$ — 1 if arc $(i,j)$ is used
- $t_i \geq 0$ — arrival time at vertex $i$
- $u_i \geq 0$ — position of vertex $i$ in route

**Objective:**
$$\min \sum_{i \in V} \sum_{j \in V, j \neq i} c_{ij} \cdot x_{ij}$$

**Constraints:**
1. Visit each customer exactly once
2. Flow conservation at depot
3. Time window constraints: $t_j \geq t_i + s_i + c_{ij} - M(1 - x_{ij})$
4. MTZ subtour elimination: $u_i - u_j + n \cdot x_{ij} \leq n - 1$
5. Capacity constraints

---

## 🛡️ Security Features

ORAgent implements multiple layers of security:

1. **Input Validation**: All user inputs are validated before processing
2. **Code Sandboxing**: Generated code is analyzed for dangerous patterns
3. **Authentication**: Optional Chainlit-based user authentication
4. **Rate Limiting**: Azure OpenAI built-in rate limiting
5. **Guardrails**: AI-powered content filtering for inputs and outputs

### Dangerous Pattern Detection

The Code Safety Guardrail blocks:
- `exec()`, `eval()` calls
- System command execution (`os.system`, `subprocess`)
- File system manipulation outside workspace
- Network operations
- Import of dangerous modules

---

## 📈 Performance

| Instance Size | Variables | Constraints | Typical Solve Time |
|--------------|-----------|-------------|-------------------|
| 10 customers | ~200 | ~300 | < 5 seconds |
| 20 customers | ~800 | ~1,200 | 10-30 seconds |
| 50 customers | ~5,000 | ~7,500 | 1-5 minutes |
| 100 customers | ~20,000 | ~30,000 | 5-15 minutes* |

*May require increased time limit

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

### Development Ideas

- [ ] Add support for other VRP variants (CVRP, PDPTW)
- [ ] Implement metaheuristics (Genetic Algorithm, Simulated Annealing)
- [ ] Add real-world map integration (OSM, Google Maps)
- [ ] Support for multiple solver backends (Gurobi, CPLEX)
- [ ] Benchmark suite with Solomon instances
- [ ] Multi-language support

---

## 📚 Resources

### Learn More About VRPTW

- [NEO Research Group - VRPTW](https://neo.lcc.uma.es/vrp/vrp-flavors/vrp-with-time-windows/)
- [Solomon Benchmark Instances](https://www.sintef.no/projectweb/top/vrptw/solomon-benchmark/)
- [VRPy - Python VRP Library](https://vrpy.readthedocs.io/)

### OpenAI Agents SDK

- [Official Documentation](https://openai.github.io/openai-agents-python/)
- [GitHub Repository](https://github.com/openai/openai-agents-python)

### PuLP Optimization

- [PuLP Documentation](https://coin-or.github.io/pulp/)
- [COIN-OR CBC Solver](https://github.com/coin-or/Cbc)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenAI** for the Agents SDK
- **COIN-OR** for the CBC solver
- **Chainlit** for the beautiful chat interface
- The Operations Research community for decades of research on VRP

---

<div align="center">

**Built with ❤️ for the Operations Research community**

⭐ Star this repo if you find it useful!

</div>