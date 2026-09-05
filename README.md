# J.A.R.V.I.S. — Personal AI, Computer Agent & Coding Assistant

> **Just A Rather Very Intelligent System**  
> An offline-first, extensible, and free personal AI and computer agent.

---

## 🌟 Overview & Philosophy

J.A.R.V.I.S. is being evolved from a simple script into a fully autonomous, offline-first personal AI computer and coding agent.

* **Offline-First & Free**: No mandatory subscriptions or paid cloud APIs.
* **Pluggable Local LLMs**: Direct support for [Ollama](https://ollama.com) (Llama 3, Qwen 2.5 Coder, Mistral, Phi-3, DeepSeek), [LM Studio](https://lmstudio.ai), and a built-in zero-dependency deterministic fallback engine.
* **Extensible Tool System**: Safe PowerShell command runner, workspace filesystem manager, system specs inspector, and diagnostic debugger.
* **3-Tier Permission Boundary**: Classifies all actions (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) with confirmation prompts for destructive operations.
* **System Diagnostics**: Automatically investigates and diagnoses missing CLI tools (e.g. `winget`, `python`, `git`) and PATH misconfigurations.

---

## 🚀 Quick Start

### 1. Launch J.A.R.V.I.S. (Interactive CLI)
```bash
python main.py
```

### 2. Run Diagnostics / Health Check
```bash
python main.py --doctor
```

### 3. Run a Single Non-Interactive Query
```bash
python main.py --query "What are my system specs?"
python main.py --query "diagnose winget"
python main.py --query "list files in workspace"
```

---

## 🧠 Connecting Local LLMs

You can switch the cognitive provider in `config.json` or pass `--provider`:

### Option A: Local Ollama (Recommended)
1. Install Ollama from [ollama.com](https://ollama.com)
2. Pull a model:
   ```bash
   ollama pull llama3.2
   # or for coding:
   ollama pull qwen2.5-coder:7b
   ```
3. Update `config.json`:
   ```json
   {
     "llm": {
       "provider": "ollama",
       "model": "llama3.2"
     }
   }
   ```

### Option B: LM Studio / LocalAI (OpenAI-Compatible)
1. Launch LM Studio and start the local inference server (default port `1234`).
2. Update `config.json`:
   ```json
   {
     "llm": {
       "provider": "openai_compatible",
       "openai_compat_url": "http://localhost:1234/v1"
     }
   }
   ```

### Option C: Standalone Rule Engine (Zero Setup)
Default out of the box. No model download needed.

---

## 🛠️ Built-in Tools

| Tool | Risk Level | Description |
| :--- | :--- | :--- |
| `run_shell_command` | `HIGH` (Dynamic) | Executes PowerShell commands with output capture and timeout handling. |
| `get_system_info` | `LOW` | Inspects CPU, RAM, OS, disk space, and runtime metrics. |
| `diagnose_command` | `LOW` | Diagnoses missing tools, PATH issues, and Windows AppExecutionAliases (`winget`, etc.). |
| `read_file` | `LOW` | Reads text files safely with line truncation limits. |
| `write_file` | `MEDIUM` | Creates or writes files within the workspace. |
| `list_directory` | `LOW` | Lists directory trees and file metadata. |
| `take_screenshot` | `LOW` | Captures and saves desktop screenshots to `~/Pictures`. |
| `open_browser` | `LOW` | Opens URLs and web apps in the default browser. |
| `tell_joke` | `LOW` | Returns tech and programming jokes. |

---

## ⌨️ CLI Meta Commands

When running in interactive mode (`python main.py`), you can use the following commands:
* `:help` — Show interaction guide and query examples.
* `:doctor` — Run full system diagnostic health checks.
* `:tools` — List all registered tools and their schemas.
* `:status` — Check active LLM engine, memory context, and runtime state.
* `:voice` — Toggle offline voice speech output (pyttsx3).
* `:config` — Display active configuration settings.
* `:clear` — Clear terminal screen and reset conversation history.
* `:exit` — Exit J.A.R.V.I.S.

---

## 🧪 Running Unit Tests

```bash
python -m unittest discover -s tests
```

---

## 🗺️ 9-Phase Roadmap

1. ✅ **Phase 1 — Foundation (Baby J.A.R.V.I.S.)**: Core engine, modular package, tool registry, safety gates, local LLM layer, and interactive CLI.
2. ⬜ **Phase 2 — Voice**: Local offline STT (Whisper/Vosk), wake-word detection, continuous listening.
3. ⬜ **Phase 3 — Memory**: Vector store (Chromadb/sqlite-vss), long-term user preferences, project memory.
4. ⬜ **Phase 4 — Computer Control**: UI automation, window management, desktop perception.
5. ⬜ **Phase 5 — Coding Agent**: Multi-file refactoring, autonomous debugging, test-driven repair loop.
6. ⬜ **Phase 6 — System Agent**: Windows service management, registry fixes, environment doctor.
7. ⬜ **Phase 7 — Agentic Intelligence**: Goal-oriented planning, multi-step subtask decomposition.
8. ⬜ **Phase 8 — Safety & Reliability**: Sandbox execution, rollback strategies, dry-run previews.
9. ⬜ **Phase 9 — Mature J.A.R.V.I.S.**: Fully autonomous, multimodal personal AI assistant.
