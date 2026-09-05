"""
J.A.R.V.I.S. Foundation Core Entry Point
Usage:
  python main.py               # Launch Modern Iron Man HUD GUI (Default)
  python main.py --cli         # Interactive CLI / Terminal mode
  python main.py --voice       # Interactive Voice Mode in CLI
  python main.py --query "..."  # Single non-interactive query
  python main.py --doctor       # Run system diagnostic checks
"""

import argparse
import sys
from jarvis.config import get_config
from jarvis.core.engine import JarvisEngine
from jarvis.core.ollama_service import ollama_service
from jarvis.interface.cli import JarvisCLI
from jarvis.interface.gui import launch_gui


def main():
    parser = argparse.ArgumentParser(description="J.A.R.V.I.S. - Personal AI and Computer Agent")
    parser.add_argument("--cli", action="store_true", help="Launch in Classic Terminal CLI mode")
    parser.add_argument("--query", "-q", type=str, help="Run a single query and exit")
    parser.add_argument("--doctor", action="store_true", help="Run system diagnostics and exit")
    parser.add_argument("--provider", type=str, help="Override LLM provider (ollama, openai_compatible, fallback)")
    parser.add_argument("--voice", "-v", "--listen", action="store_true", help="Launch in Voice Listening Mode")

    args = parser.parse_args()
    config = get_config()

    if args.provider:
        config.llm.provider = args.provider

    if args.doctor:
        cli = JarvisCLI()
        cli._run_doctor()
        sys.exit(0)

    if args.query:
        # Automatically ensure Ollama is up if using Ollama provider
        if config.llm.provider == "ollama":
            ollama_service.ensure_running(timeout_seconds=5)
        engine = JarvisEngine()
        response = engine.process_query(args.query)
        print(response)
        sys.exit(0)

    if args.cli:
        # CLI Mode
        if config.llm.provider == "ollama":
            ollama_service.ensure_running(timeout_seconds=5)
        cli = JarvisCLI(start_in_voice_mode=args.voice)
        cli.run()
        sys.exit(0)

    # Default: Launch Iron Man / Age of Ultron HUD GUI
    try:
        launch_gui()
    except Exception as e:
        print(f"\n[ERROR] Could not start GUI interface: {e}")
        print("[FALLBACK] Launching Terminal CLI mode...\n")
        cli = JarvisCLI(start_in_voice_mode=args.voice)
        cli.run()


if __name__ == "__main__":
    main()
