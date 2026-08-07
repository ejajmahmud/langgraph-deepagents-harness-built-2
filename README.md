# LANGGRAPH-DEEPAGENTS-HARNESS-BUILT-2 - High-Impact Autonomous Agentic Application

🤖 **Production-Grade Cognitive Agent Loop, Multi-Agent Swarms, and Intelligent Task Routing Platform.**

---

## 📋 Table of Contents
1. [Overview](#-overview)
2. [Cognitive Loop Architecture](#-cognitive-loop-architecture)
3. [Key Features](#-key-features)
4. [Technology Stack](#-technology-stack)
5. [Directory Layout](#-directory-layout)
6. [Environment Configurations](#-environment-configurations)
7. [Installation & Deployment](#-installation--deployment)
8. [Unified Runtime Controller](#-unified-runtime-controller)
9. [Authors & Maintainers](#-authors--maintainers)

---

## 🔍 Overview
This repository provides a state-of-the-art, high-impact implementation of an autonomous agent system. Leveraged for complex multi-agent swarms (using frameworks like LangGraph, CrewAI, or AutoGen), this application resolves high-cognitive load tasks via dynamic routing, state preservation, and custom tool orchestration.

---

## 🧠 Cognitive Loop Architecture
The system utilizes a structured reasoning loop to dynamically analyze input, select tools, and iterate on responses:

```
[User Goal Input]
       │
       ▼
┌──────────────┐
│  State Node  │◄─────────────────┐
└──────┬───────┘                  │
       │                          │
       ▼                          │
┌──────────────┐                  │ (State Update &
│  LLM Reason  ├─────────────────┐│  Re-evaluation)
└──────┬───────┘                 ││
       │ (Tool Selected)         ││
       ▼                         ▼│
┌──────────────┐           ┌──────────────┐
│  Tool Exec   │           │  Final Output│
└──────────────┘           └──────────────┘
```

---

## ✨ Key Features
- **Intelligent Graph/State Routing**: Native state graph tracking preventing conversational loops.
- **Autonomous Tool-Calling**: Integrated interfaces for web browsing, scraping, database queries, and custom APIs.
- **Standardized Runtime Controller**: Equipped with `agent_runtime.py` to launch and evaluate cycles instantly.
- **Docker-ready Configs**: Seamless container deployment models.

---

## 🛠 Technology Stack
| Component | Stack |
| :--- | :--- |
| **Language Runtime** | Python |
| **Frameworks** | LangGraph / CrewAI / AutoGen / LangChain |
| **Cognitive Loop Engine** | `agent_runtime.py` (Local State Emulator) |
| **Deploy Tooling** | python-dotenv, pip/poetry configs |

---

## 📂 Directory Layout
```
langgraph-deepagents-harness-built-2/
├── agent_runtime.py      # Standardized agent executor (Injected Improvement)
├── requirements.txt      # Core python dependencies
├── README.md             # Super detailed developer documentation
└── [Core Files]          # Modular codebase components
```

---

## ⚙ Environment Configurations
Configure the variables inside a `.env` file at the root:

```env
# LLM Endpoint Credentials
OPENAI_API_KEY=your_openai_api_key_here
MODEL_NAME=gpt-4o
```

---

## 🚀 Installation & Deployment

### Step 1: Clone the Repository
```bash
git clone https://github.com/ejajmahmud/langgraph-deepagents-harness-built-2.git
cd langgraph-deepagents-harness-built-2
```

### Step 2: Dependencies Installation
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Run the Autonomous Loop
```bash
python agent_runtime.py
```

---

## 🛠 Unified Runtime Controller
The script `agent_runtime.py` provides an out-of-the-box launcher to emulate agent execution cycles, verify API keys, check tool parameters, and trace states. This enables rapid debugging before committing resources.

---

## 📄 Original Repository Documentation

<div align="center">
  <a href="https://docs.langchain.com/oss/python/deepagents/overview#deep-agents-overview">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset=".github/images/logo-dark.svg">
      <source media="(prefers-color-scheme: light)" srcset=".github/images/logo-light.svg">
      <img alt="Deep Agents Logo" src=".github/images/logo-dark.svg" width="50%">
    </picture>
  </a>
</div>

<div align="center">
  <h3>The batteries-included agent harness.</h3>
</div>

<div align="center">
  <a href="https://opensource.org/licenses/MIT" target="_blank"><img src="https://img.shields.io/pypi/l/deepagents" alt="PyPI - License"></a>
  <a href="https://pypistats.org/packages/deepagents" target="_blank"><img src="https://img.shields.io/pepy/dt/deepagents" alt="PyPI - Downloads"></a>
  <a href="https://pypi.org/project/deepagents/#history" target="_blank"><img src="https://img.shields.io/pypi/v/deepagents?label=%20" alt="Version"></a>
  <a href="https://x.com/langchain" target="_blank"><img src="https://img.shields.io/twitter/url/https/twitter.com/langchain.svg?style=social&label=Follow%20%40LangChain" alt="Twitter / X"></a>
</div>

<br>

Deep Agents is an agent harness. An opinionated, ready-to-run agent out of the box. Instead of wiring up prompts, tools, and context management yourself, you get a working agent immediately and customize what you need.

**What's included:**

- **Planning** — `write_todos` for task breakdown and progress tracking
- **Filesystem** — `read_file`, `write_file`, `edit_file`, `ls`, `glob`, `grep` for reading and writing context
- **Shell access** — `execute` for running commands (with sandboxing)
- **Sub-agents** — `task` for delegating work with isolated context windows
- **Smart defaults** — Prompts that teach the model how to use these tools effectively
- **Context management** — Auto-summarization when conversations get long, large outputs saved to files

> [!NOTE]
> Looking for the JS/TS library? Check out [deepagents.js](https://github.com/langchain-ai/deepagentsjs).

## Quickstart

```bash
pip install deepagents
# or
uv add deepagents
```

```python
from deepagents import create_deep_agent

agent = create_deep_agent()
result = agent.invoke({"messages": [{"role": "user", "content": "Research LangGraph and write a summary"}]})
```

The agent can plan, read/write files, and manage its own context. Add tools, customize prompts, or swap models as needed.

> [!TIP]
> For developing, debugging, and deploying AI agents and LLM applications, see [LangSmith](https://docs.langchain.com/langsmith/home).

## Customization

Add your own tools, swap models, customize prompts, configure sub-agents, and more. See the [documentation](https://docs.langchain.com/oss/python/deepagents/overview) for full details.

```python
from langchain.chat_models import init_chat_model

agent = create_deep_agent(
    model=init_chat_model("openai:gpt-4o"),
    tools=[my_custom_tool],
    system_prompt="You are a research assistant.",
)
```

MCP is supported via [`langchain-mcp-adapters`](https://github.com/langchain-ai/langchain-mcp-adapters).

## Deep Agents CLI

A pre-built coding agent in your terminal — similar to Claude Code or Cursor — powered by any LLM. One install command and you're up and running.

<p align="center">
  <img src="libs/cli/images/cli.png" alt="Deep Agents CLI" width="600"/>
</p>

```bash
curl -LsSf https://raw.githubusercontent.com/langchain-ai/deepagents/main/libs/cli/scripts/install.sh | bash
```

**Highlights:**

- **Interactive TUI** — rich terminal interface with streaming responses
- **Web search** — ground responses in live information
- **Headless mode** — run non-interactively for scripting and CI
- Plus all SDK features out of the box — remote sandboxes, persistent memory, custom skills, and human-in-the-loop approval

See the [CLI documentation](https://docs.langchain.com/oss/python/deepagents/cli/overview) for the full feature set.

## LangGraph Native

`create_deep_agent` returns a compiled [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) graph. Use it with streaming, Studio, checkpointers, or any LangGraph feature.

## FAQ

### Why should I use this?

- **100% open source** — MIT licensed, fully extensible
- **Provider agnostic** — Works with any Large Language Model that supports tool calling, including both frontier and open models
- **Built on LangGraph** — Production-ready runtime with streaming, persistence, and checkpointing
- **Batteries included** — Planning, file access, sub-agents, and context management work out of the box
- **Get started in seconds** — `uv add deepagents` and you have a working agent
- **Customize in minutes** — Add tools, swap models, tune prompts when you need to

---

## Documentation

- [docs.langchain.com](https://docs.langchain.com/oss/python/deepagents/overview) – Comprehensive documentation, including conceptual overviews and guides
- [reference.langchain.com/python](https://reference.langchain.com/python/deepagents/) – API reference docs for Deep Agents packages
- [Chat LangChain](https://chat.langchain.com/) – Chat with the LangChain documentation and get answers to your questions

**Discussions**: Visit the [LangChain Forum](https://forum.langchain.com) to connect with the community and share all of your technical questions, ideas, and feedback.

## Additional resources

- **[Examples](examples/)** — Working agents and patterns
- [Contributing Guide](https://docs.langchain.com/oss/python/contributing/overview) – Learn how to contribute to LangChain projects and find good first issues.
- [Code of Conduct](https://github.com/langchain-ai/langchain/?tab=coc-ov-file) – Our community guidelines and standards for participation.

---

## Acknowledgements

This project was primarily inspired by Claude Code, and initially was largely an attempt to see what made Claude Code general purpose, and make it even more so.

## Security

Deep Agents follows a "trust the LLM" model. The agent can do anything its tools allow. Enforce boundaries at the tool/sandbox level, not by expecting the model to self-police. See the [security policy](https://github.com/langchain-ai/deepagents?tab=security-ov-file) for more information.


---

Maintainer: [Md Ejaj Mahmud](https://github.com/ejajmahmud).