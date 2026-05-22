# Ultra Vibe - Ultrawork Mode for Mistral Vibe

Bring the **Ultrawork Mode** capability from [oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent) to [Mistral Vibe](https://github.com/mistralai/mistral-vibe).

Ultrawork Mode transforms Vibe from a simple chat assistant into a **multi-agent orchestrator** that manages background tasks, specialized experts, and iterative loops for autonomous task completion.

---

## Features

### Core Ultrawork Capabilities
- **Multi-Agent Orchestration**: Sisyphus coordinates specialist agents (Hephaestus, Oracle, Librarian, Explore)
- **Parallel Task Execution**: Delegates work to multiple agents simultaneously
- **Mandatory Planning**: Forces structured planning for complex tasks
- **Model Auto-Escalation**: Automatically upgrades to high-precision models
- **ULW Loop**: Persistent iteration with verification enforcement
- **Task Continuity**: Maintains state across session resumes via task_id

### Protocol Rules (from oh-my-openagent)
1. **Mandatory Certainty**: 100% certainty before implementation
2. **Mandatory Planning**: Use plan agent for 2+ step tasks
3. **Aggressive Delegation**: Orchestrator delegates, doesn't implement
4. **Model Optimization**: Auto-upgrade to max/high precision variants

---

## Quick Start

### Prerequisites
- Python 3.10+
- Mistral Vibe 2.10.1+
- pip

### Installation

#### Development Setup
```bash
# Clone the repository
git clone https://github.com/your-username/ultra-vibe.git
cd ultra-vibe

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .
```

#### As a Vibe Plugin (Future)
```bash
pip install ultra-vibe
```

### Configuration

Add to your `~/.vibe/config.toml`:

```toml
[ultrawork]
enabled = true
keyword_detection = true
model_auto_upgrade = true
default_agent = "sisyphus"

# Per-agent ultrawork settings
[agents.sisyphus.ultrawork]
enabled = true
model = "anthropic/claude-3-5-sonnet"
variant = "max"

[agents.hephaestus.ultrawork]
enabled = true
model = "mistral-large-2407"
variant = "max"
```

---

## Usage

### Trigger Ultrawork Mode

```bash
# Explicit command
vibe --ultrawork "Refactor the entire codebase"

# Short form
vibe --ulw "Create a microservice architecture"

# Natural language (requires keyword detection)
vibe "Please use ultrawork mode to optimize the database queries"

# Combo mode with hyperplan
vibe "hpp ulw: Design and implement a caching layer"
```

### Use Specific Specialist Agent

```bash
vibe --agent sisyphus "Orchestrate a complex migration"
vibe --agent hephaestus "Implement a high-performance algorithm"
vibe --agent oracle "Review this architecture for security issues"
vibe --agent librarian "Find documentation for this API"
vibe --agent explore "Analyze this codebase structure"
```

---

## Project Structure

```
ultra-vibe/
├── vibe/
│   └── core/
│       ├── hooks/                  # Hook system for mode detection & injection
│       │   ├── __init__.py
│       │   ├── base.py            # Base hook classes
│       │   ├── keyword_detector.py
│       │   ├── model_override.py
│       │   └── ultrawork.py
│       ├── delegation/            # Task delegation system
│       │   ├── __init__.py
│       │   ├── task_manager.py
│       │   ├── subagent.py
│       │   └── result_aggregator.py
│       ├── background/             # Background task execution
│       │   ├── __init__.py
│       │   ├── task_queue.py
│       │   └── worker.py
│       └── ultrawork/              # Ultrawork-specific components
│           ├── __init__.py
│           ├── loop.py            # ULW Loop implementation
│           ├── protocol.py        # Ultrawork protocol
│           └── agents.py          # Agent definitions
├── agents/                        # Specialist agent configurations
│   ├── sisyphus.toml
│   ├── hephaestus.toml
│   ├── oracle.toml
│   ├── librarian.toml
│   └── explore.toml
├── tests/
│   └── test_ultrawork/
│       ├── __init__.py
│       ├── test_keyword_detection.py
│       ├── test_model_override.py
│       ├── test_delegation.py
│       └── test_loop.py
├── docs/
│   └── ultrawork/
│       ├── overview.md
│       ├── quick-start.md
│       ├── agents.md
│       ├── configuration.md
│       └── workflows.md
├── examples/
│   └── ultrawork/
│       ├── basic.md
│       ├── refactoring.md
│       ├── debugging.md
│       ├── documentation.md
│       └── research.md
├── pyproject.toml
├── README.md
└── LICENSE
```

---

## Specialist Agents

| Agent | Role | Specialization | Default Model |
|-------|------|---------------|---------------|
| **Sisyphus** | Main Orchestrator | Task decomposition, delegation, result aggregation | claude-3-5-sonnet |
| **Hephaestus** | Deep Implementation | Complex coding, refactoring, optimization | mistral-large-2407 |
| **Oracle** | Architectural Review | Design, code review, security, best practices | mistral-large-2407 |
| **Librarian** | Documentation | Doc generation, research, knowledge lookup | mistral-medium-3.5 |
| **Explore** | Codebase Exploration | Repository analysis, context gathering | mistral-medium-3.5 |

---

## Architecture

### Hook System
The hook system allows intercepting and modifying Vibe's behavior at key points:
- **Pre-prompt hooks**: Modify system prompt before LLM call
- **Post-response hooks**: Process LLM response
- **Tool execution hooks**: Intercept and modify tool calls
- **Model selection hooks**: Override model/variant selection

### Task Delegation Flow
```
User Request → Keyword Detection → Ultrawork Enabled
    ↓
Sisyphus (Orchestrator) → Task Analysis
    ↓
    ├─> Plan Agent → Generate task graph (if multi-step)
    │
    ├─> Hephaestus → Deep implementation
    ├─> Oracle → Architecture review
    ├─> Librarian → Documentation/research
    └─> Explore → Codebase context
    ↓
Result Aggregation → Verification (if ULW Loop) → Final Response
```

---

## Configuration Reference

### Global Ultrawork Settings

```toml
[ultrawork]
enabled = true              # Enable ultrawork mode globally
keyword_detection = true    # Detect /ultrawork, /ulw, etc.
model_auto_upgrade = true   # Auto-upgrade models in ultrawork mode
default_agent = "sisyphus"   # Default agent for ultrawork
hyperplan_integration = true # Enable hpp ulw combo mode
max_concurrent_tasks = 5    # Maximum parallel sub-agents
background_tasks = true     # Enable background task execution
```

### Per-Agent Ultrawork Settings

```toml
[agents.<name>.ultrawork]
enabled = true              # Enable ultrawork for this agent
model = "mistral-large-2407" # Model override for ultrawork
variant = "max"             # Reasoning variant override
```

---

## Development

### Running Tests
```bash
# All tests
pytest

# Specific test file
pytest tests/test_ultrawork/test_keyword_detection.py

# With coverage
pytest --cov=vibe --cov-report=html
```

### Code Style
- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints
- Include docstrings
- Keep lines under 100 characters

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Inspired by [oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent) by code-yeongyu
- Built for [Mistral Vibe](https://github.com/mistralai/mistral-vibe)
- DeepWiki documentation: [Ultrawork Mode](https://deepwiki.com/code-yeongyu/oh-my-openagent/9.1-ultrawork-mode)

---

## Resources

- [Project Plan](/.vibe/plans/1779477120-proud-rustic-creek.md)
- [oh-my-openagent GitHub](https://github.com/code-yeongyu/oh-my-openagent)
- [Mistral Vibe GitHub](https://github.com/mistralai/mistral-vibe)
- [Vibe Documentation](https://docs.vibe.sh)
