"""
Interactive Terminal CLI Interface for J.A.R.V.I.S.
Supports dual-mode: Interactive Text REPL and Continuous Voice Listening Loop with Pause/Resume.
"""

import os
import sys
from jarvis.config import get_config, reload_config
from jarvis.core.engine import JarvisEngine
from jarvis.core.logger import Colors, logger, safe_print
from jarvis.interface.banner import print_banner, print_status_box
from jarvis.interface.voice import voice_bridge
from jarvis.llm.factory import LLMFactory
from jarvis.tools.registry import tool_registry


class JarvisCLI:
    def __init__(self, start_in_voice_mode: bool = False):
        self.config = get_config()
        self.engine = JarvisEngine()
        self.voice_mode = start_in_voice_mode or (self.config.voice.input_mode == "voice")
        self.is_paused = False

    def run(self) -> None:
        """Starts the interactive CLI REPL."""
        os.system("cls" if os.name == "nt" else "clear")
        print_banner()

        provider_name = self.engine.provider.__class__.__name__.replace("Provider", "")
        model_name = getattr(self.engine.provider, "model", "Deterministic Rules")
        tools_count = len(tool_registry.list_tools())
        
        print_status_box(
            provider_name=provider_name,
            model=model_name,
            tools_count=tools_count,
            workspace=self.config.workspace_dir,
        )

        mode_desc = "VOICE (Microphone)" if self.voice_mode else "TEXT (Keyboard)"
        safe_print(f"  {Colors.BOLD}[INPUT MODE]{Colors.RESET} {Colors.GREEN}{mode_desc}{Colors.RESET}")
        safe_print(f"  {Colors.GRAY}(Say 'stop listening' to pause, or type :listen to switch modes){Colors.RESET}\n")

        greeting = f"Welcome back, {self.config.user_name}. J.A.R.V.I.S. Foundation Core is online."
        logger.agent(greeting)
        if self.config.voice.enabled or self.voice_mode:
            voice_bridge.speak(greeting)

        while True:
            try:
                user_input = ""

                # Paused / Standby State
                if self.is_paused:
                    safe_print(f"\n{Colors.YELLOW}[PAUSED]{Colors.RESET} Voice listening is on standby.")
                    prompt_str = f"   {Colors.CYAN}Press [1] + Enter to resume listening, or type a command: {Colors.RESET}"
                    user_input = input(prompt_str).strip()

                    if not user_input:
                        continue

                    if user_input == "1" or user_input.lower() in ["resume", "start listening", ":listen", "listen"]:
                        self.is_paused = False
                        self.voice_mode = True
                        resume_msg = f"Resuming listening mode. I am at your service, {self.config.user_name}."
                        logger.agent(resume_msg)
                        voice_bridge.speak(resume_msg)
                        continue

                # Voice Mode Active
                elif self.voice_mode:
                    safe_print(f"\n{Colors.GREEN}{Colors.BOLD}{self.config.user_name} [Voice Mode] > {Colors.RESET}")
                    user_input = voice_bridge.listen(timeout=6, phrase_time_limit=8)
                    if not user_input:
                        continue

                # Text Mode Active
                else:
                    user_input = input(f"\n{Colors.GREEN}{Colors.BOLD}{self.config.user_name} > {Colors.RESET}").strip()
                    if not user_input:
                        continue

                # Check for "stop listening" voice/text commands
                input_lower = user_input.lower().strip()
                if any(stop_phrase in input_lower for stop_phrase in ["stop listening", "pause listening", "mute mic", "go to sleep", "sleep mode"]):
                    self.is_paused = True
                    pause_msg = f"Paused listening mode. Press 1 and Enter whenever you need me, {self.config.user_name}."
                    logger.agent(pause_msg)
                    voice_bridge.speak(pause_msg)
                    continue

                # Check for meta commands
                if user_input.startswith(":"):
                    handled = self._handle_meta_command(user_input)
                    if handled == "exit":
                        break
                    continue

                # Check for exit commands
                if input_lower in ["exit", "quit", "offline", "shutdown jarvis", "go offline"]:
                    farewell = f"Going offline. Have a productive day, {self.config.user_name}!"
                    logger.agent(farewell)
                    voice_bridge.speak(farewell)
                    break

                # Process query through engine
                response_text = self.engine.process_query(user_input)
                safe_print("")
                logger.agent(response_text)
                
                # Speak response out loud in voice mode or if TTS enabled
                if self.config.voice.enabled or self.voice_mode:
                    voice_bridge.speak(response_text)

            except (KeyboardInterrupt, EOFError):
                safe_print(f"\n{Colors.YELLOW}Session interrupted. Goodbye!{Colors.RESET}")
                break
            except Exception as e:
                logger.error(f"Unexpected error in CLI loop: {e}")

    def _handle_meta_command(self, cmd_str: str) -> str:
        cmd = cmd_str.lower().strip()
        
        if cmd in [":exit", ":quit", ":q"]:
            return "exit"

        elif cmd in [":help", ":h", ":?"]:
            self._print_help()

        elif cmd in [":listen", ":mode"]:
            self.voice_mode = not self.voice_mode
            self.is_paused = False
            self.config.voice.enabled = self.voice_mode or self.config.voice.enabled
            self.config.voice.input_mode = "voice" if self.voice_mode else "text"
            self.config.save()
            mode_name = "VOICE (Microphone)" if self.voice_mode else "TEXT (Keyboard)"
            safe_print(f"{Colors.GREEN}[MODE SWITCH]{Colors.RESET} Input mode is now: {Colors.BOLD}{mode_name}{Colors.RESET}")
            voice_bridge.speak(f"Switched to {mode_name} mode.")

        elif cmd == ":tools":
            self._print_tools()

        elif cmd == ":status":
            self._print_status()

        elif cmd == ":doctor":
            self._run_doctor()

        elif cmd == ":config":
            self._print_config()

        elif cmd in [":voice"]:
            self.config.voice.enabled = not self.config.voice.enabled
            self.config.save()
            status = "ENABLED" if self.config.voice.enabled else "DISABLED"
            logger.info(f"Voice TTS speech output is now {status}.")
            if self.config.voice.enabled:
                voice_bridge.speak("Voice output is now enabled.")

        elif cmd.startswith(":gender") or cmd.startswith(":persona"):
            parts = cmd.split()
            if len(parts) > 1:
                target_gender = parts[1].strip()
                new_gender = voice_bridge.set_gender(target_gender)
            else:
                current = voice_bridge.gender
                new_gender = voice_bridge.set_gender("female" if current == "male" else "male")
            self.config.save()
            persona = "J.A.R.V.I.S. (Male)" if new_gender == "male" else "F.R.I.D.A.Y. (Female)"
            safe_print(f"{Colors.GREEN}[PERSONA]{Colors.RESET} Voice persona set to: {Colors.BOLD}{persona}{Colors.RESET}")
            if self.config.voice.enabled:
                voice_bridge.speak(f"Voice persona set to {persona}.")

        elif cmd == ":clear":
            os.system("cls" if os.name == "nt" else "clear")
            print_banner()
            self.engine.context.clear()
            logger.info("Terminal screen cleared and conversation context reset.")

        else:
            logger.warn(f"Unknown command '{cmd_str}'. Type {Colors.CYAN}:help{Colors.RESET} to see available commands.")

        return "continue"

    def _print_help(self) -> None:
        safe_print(f"\n{Colors.BOLD}{Colors.CYAN}--- J.A.R.V.I.S. Command & Interaction Guide ---{Colors.RESET}")
        safe_print(f"  {Colors.BOLD}Meta Commands:{Colors.RESET}")
        safe_print(f"    {Colors.CYAN}:listen{Colors.RESET}  - Toggle Voice Mode (Microphone vs Keyboard)")
        safe_print(f"    {Colors.CYAN}:voice{Colors.RESET}   - Toggle Spoken Audio Speech Output (TTS)")
        safe_print(f"    {Colors.CYAN}:gender{Colors.RESET}  - Toggle Voice Persona (Male J.A.R.V.I.S. / Female F.R.I.D.A.Y.)")
        safe_print(f"    {Colors.CYAN}:doctor{Colors.RESET}  - Run comprehensive system health checks")
        safe_print(f"    {Colors.CYAN}:tools{Colors.RESET}   - List all available tools & risk levels")
        safe_print(f"    {Colors.CYAN}:status{Colors.RESET}  - View active LLM provider and memory state")
        safe_print(f"    {Colors.CYAN}:config{Colors.RESET}  - Display current configuration settings")
        safe_print(f"    {Colors.CYAN}:clear{Colors.RESET}   - Clear screen and reset context")
        safe_print(f"    {Colors.CYAN}:exit{Colors.RESET}    - Exit J.A.R.V.I.S.")
        safe_print(f"\n  {Colors.BOLD}Voice Commands to Speak:{Colors.RESET}")
        safe_print(f"    • \"Open YouTube\" -> Speaks back and opens YouTube in browser")
        safe_print(f"    • \"Stop listening\" -> Pauses microphone (press 1 to resume)")
        safe_print(f"    • \"What are my system specs?\" -> Inspects hardware and reads specs")
        safe_print(f"    • \"Take a screenshot\" -> Captures desktop screen")
        safe_print(f"    • \"Diagnose winget\" -> Checks Windows AppExecutionAliases")
        safe_print(f"    • \"Tell me a joke\" -> Tells a joke out loud")

    def _print_tools(self) -> None:
        safe_print(f"\n{Colors.BOLD}{Colors.MAGENTA}--- Registered J.A.R.V.I.S. Tools ({len(tool_registry.list_tools())}) ---{Colors.RESET}")
        for t in tool_registry.list_tools():
            risk_color = Colors.GREEN if t.risk_level.value == "LOW" else (Colors.YELLOW if t.risk_level.value == "MEDIUM" else Colors.RED)
            safe_print(f"  ⚡ {Colors.BOLD}{t.name:<22}{Colors.RESET} [{risk_color}{t.risk_level.value:<8}{Colors.RESET}] - {t.description}")

    def _print_status(self) -> None:
        provider_name = self.engine.provider.__class__.__name__
        is_avail = self.engine.provider.is_available()
        avail_str = f"{Colors.GREEN}ONLINE{Colors.RESET}" if is_avail else f"{Colors.RED}OFFLINE{Colors.RESET}"
        
        safe_print(f"\n{Colors.BOLD}{Colors.BLUE}--- J.A.R.V.I.S. System Diagnostics ---{Colors.RESET}")
        safe_print(f"  Cognitive Core Provider: {provider_name} [{avail_str}]")
        safe_print(f"  Active Model:            {getattr(self.engine.provider, 'model', 'Rule-Based Fallback')}")
        safe_print(f"  Input Mode:              {'VOICE (Microphone)' if self.voice_mode else 'TEXT (Keyboard)'}")
        safe_print(f"  Listening State:         {'PAUSED' if self.is_paused else 'ACTIVE'}")
        safe_print(f"  Voice Audio Output:      {'ENABLED' if self.config.voice.enabled else 'DISABLED'}")
        safe_print(f"  Context Messages:        {len(self.engine.context.messages)}")
        safe_print(f"  Workspace:               {self.config.workspace_dir}")

    def _run_doctor(self) -> None:
        safe_print(f"\n{Colors.BOLD}{Colors.CYAN}--- Running J.A.R.V.I.S. Doctor Health Checks ---{Colors.RESET}")
        diag_tool = tool_registry.get_tool("diagnose_command")
        
        for tool_name in ["winget", "python", "git", "powershell"]:
            res = diag_tool.execute(tool_name)
            status = "PASS" if res.get("is_available") else "CHECK"
            safe_print(f"  [{status:<5}] {tool_name}")
            for f in res.get("findings", []):
                safe_print(f"           {f}")

    def _print_config(self) -> None:
        safe_print(f"\n{Colors.BOLD}{Colors.YELLOW}--- Current Configuration (config.json) ---{Colors.RESET}")
        import json
        from dataclasses import asdict
        safe_print(json.dumps(asdict(self.config), indent=2))
