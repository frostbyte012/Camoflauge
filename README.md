<div align="center">

# 🎭 Camouflage

### Autonomous Red vs. Blue AI Cyber Arena

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Powered-FF6B6B)](https://github.com/langchain-ai/langgraph)
[![W&B](https://img.shields.io/badge/Weights_&_Biases-Telemetry-FFBE00?logo=weightsandbiases&logoColor=black)](https://wandb.ai/)

**Camouflage** is a fully autonomous, multi-agent cybersecurity simulation framework that pits an AI Red Team against an AI Blue Team inside an air-gapped Docker sandbox — with real tools, real logs, and real-time telemetry.

[Features](#-features) · [Architecture](#-architecture) · [Installation](#-installation) · [Deployment](#-deployment) · [Telemetry](#-telemetry) · [Roadmap](#-roadmap)

<img src="path/to/your/camouflage_dashboard.png" alt="Camouflage C2 Dashboard" width="850"/>

*Live Command & Control Terminal UI*

</div>

---

## ✨ Features

- **Fully Autonomous** — Zero human intervention required; agents plan, attack, detect, and patch on their own
- **Air-Gapped** — Local LLM inference via Ollama keeps all simulation data off the public internet
- **Live Tooling** — Executes real network tools (`nmap`, `iptables`) inside isolated Docker containers
- **Multi-Agent Orchestration** — LangGraph routes intelligence dynamically between five specialized agents
- **Observability** — Tracks MTTD, token efficiency, and hallucination rates via Weights & Biases

---

## 🏗 Architecture

Camouflage uses a director-agent pattern where a central orchestrator evaluates intelligence and dispatches tasks to specialized Red and Blue team agents.

```
┌─────────────────────────────────────────────────────────┐
│                    [ DIRECTOR ]                         │
│          Central brain — routes all intelligence        │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌──────────────────┐     ┌──────────────────┐
│   🔴  RED TEAM   │     │   🔵  BLUE TEAM   │
│                  │     │                  │
│  [ SCANNER ]     │     │  [ DEFENDER ]    │
│  Network recon   │     │  SOC log analyst │
│  via nmap        │     │  & anomaly det.  │
│                  │     │                  │
│  [ EXPLOITER ]   │     │  [ PATCHER ]     │
│  Payload craft   │     │  Firewall rule   │
│  & execution     │     │  generation &    │
│                  │     │  deployment      │
└──────────────────┘     └──────────────────┘
```

| Agent | Team | Role |
|---|---|---|
| `[DIRECTOR]` | Orchestrator | Evaluates intelligence, routes tasks between agents |
| `[SCANNER]` | 🔴 Red | Executes `nmap` reconnaissance against the target sandbox |
| `[EXPLOITER]` | 🔴 Red | Crafts and fires exploit payloads based on scanner output |
| `[DEFENDER]` | 🔵 Blue | Monitors server logs and detects anomalous activity |
| `[PATCHER]` | 🔵 Blue | Writes and deploys `iptables` firewall rules dynamically |

---

## ⚙ Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| OS | Ubuntu 22.04+ | Linux host required for Docker subprocess management |
| Python | 3.11+ | For the orchestrator and W&B client |
| Docker + Compose | Latest | `docker-compose-v2` recommended |
| Ollama | Latest | Local LLM inference engine |
| Weights & Biases | Latest | Free account required for telemetry |

---

## 🚀 Installation

### Step 1 — Docker

```bash
# Install Docker and Compose plugin
sudo apt update
sudo apt install -y docker.io docker-compose-v2

# Add your user to the docker group (avoids needing sudo)
sudo usermod -aG docker $USER

# Apply group change immediately (or log out and back in)
newgrp docker
```

### Step 2 — Local LLM Engine (Ollama)

Camouflage runs inference locally to preserve the air-gap and prevent sensitive simulation data from leaving your machine.

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull the primary routing model
ollama pull qwen2.5:7b

# Verify Ollama is running
systemctl status ollama
```

> **Note:** Ollama must be running in the background before launching the arena. If it stopped, restart it with `systemctl start ollama`.

### Step 3 — Weights & Biases (Telemetry)

```bash
pip install wandb

# Authenticate — paste your API key when prompted
wandb login
```

Your free W&B account will receive live metrics from every simulation run automatically.

---

## 🛠 Deployment

```bash
# Clone the repository
git clone https://github.com/frostbyte012/Camouflage.git
cd Camouflage/red-blue-llm-arena

# Build the sandbox and orchestrator containers
docker compose up -d --build
```

> **Note:** `Dockerfile.target` automatically handles repository and GPG key configuration for the legacy vulnerable web server used as the attack surface.

To verify all containers are healthy before proceeding:

```bash
docker compose ps
```

---

## 🎮 Running the Arena

Once containers are healthy, launch the Camouflage Terminal UI:

```bash
docker exec -it decepticon_orchestrator python /app/camouflage_ui.py
```

You will be dropped into the interactive C2 prompt:

```
camouflage >
```

### C2 Commands

| Command | Description |
|---|---|
| `run` | Initiates the full autonomous simulation cycle |
| `exit` | Safely shuts down the terminal UI |

#### What happens during `run`:

1. **Flush** — Previous `iptables` rules are cleared for a clean slate
2. **Recon** — `[SCANNER]` executes an `nmap` sweep against the sandbox
3. **Exploit** — `[EXPLOITER]` crafts and fires payloads at discovered surfaces
4. **Detect** — `[DEFENDER]` analyzes server logs for attack signatures
5. **Patch** — `[PATCHER]` generates and deploys firewall rules in response
6. **Log** — All metrics are streamed to your W&B project dashboard

---

## 🔬 Telemetry & Evaluation

Every simulation run emits structured telemetry to your **`red-blue-llm-arena`** W&B project. The following metrics are tracked:

| Metric | Description |
|---|---|
| **MTTD** | Mean Time to Detect — how fast the Blue Team catches the attack |
| **Mitigation Rate** | Percentage of exploits successfully blocked by the Patcher |
| **Token Efficiency** | LLM token usage per agent per run |
| **Hallucination Rate** | False-negative rate — threats the Defender missed |
| **Agent Routing Path** | The sequence of agents the Director activated per run |

Access your dashboard at [wandb.ai](https://wandb.ai) after your first `run`.

---

## 📁 Project Structure

```
Camouflage/
└── red-blue-llm-arena/
    ├── docker-compose.yml        # Sandbox + orchestrator service definitions
    ├── Dockerfile.target         # Vulnerable web server target image
    ├── Dockerfile.orchestrator   # Orchestrator agent image
    ├── camouflage_ui.py          # Interactive C2 terminal interface
    ├── agents/
    │   ├── director.py           # Central routing agent
    │   ├── scanner.py            # Red Team recon agent
    │   ├── exploiter.py          # Red Team exploit agent
    │   ├── defender.py           # Blue Team SOC agent
    │   └── patcher.py            # Blue Team firewall agent
    └── config/
        └── settings.py           # Model, W&B, and network config
```

---

## 🗺 Roadmap

- [ ] Support for Llama-3 and Mistral model swapping via config
- [ ] Automated 50-run batch execution loop for large-scale W&B dataset generation
- [ ] Web-based dashboard (replacing terminal UI)
- [ ] CVE-seeded exploit library for the `[EXPLOITER]` agent
- [ ] Multi-target sandbox support (simulate internal network segments)

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome. Please open an issue first to discuss what you'd like to change.

```bash
# Fork and clone your fork
git checkout -b feature/your-feature-name

# Make your changes, then open a PR against main
```

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

---

<div align="center">

Built for security research and AI agent experimentation. Use responsibly in isolated environments only.

⭐ Star this repo if Camouflage helped your research!

</div>