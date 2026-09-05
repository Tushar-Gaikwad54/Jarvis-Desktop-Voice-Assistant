"""
Visual Presentation and Styling for J.A.R.V.I.S.
"""

from jarvis.core.logger import Colors, safe_print

BANNER_TEXT = rf"""{Colors.CYAN}{Colors.BOLD}
      ___       ___           ___           ___           ___           ___     
     /\  \     /\  \         /\  \         /\__\         /\  \         /\  \    
    _\:\  \   /::\  \       /::\  \       /:/ _/_        \:\  \       /::\  \   
   /\ \:\  \ /:/\:\  \     /:/\:\  \     /:/ /\  \        \:\  \     /:/\ \  \  
  _\:\ \:\  /::\~\:\  \   /::\~\:\  \   /:/ /::\  \   _____\:\  \   _\:\~\ \  \ 
 /\ \:\ \:\/:/\:\ \:\__\ /:/\:\ \:\__\ /:/_/:/\:\__\ /::::::::\__\ /\ \:\ \ \__\
 \:\ \:\ \/__/\:\ \/__/ \/_|::\/:/  / \:\/:/ /:/  / \:\~~\~~\/__/ \:\ \:\ \/__/
  \:\ \:\__\   \:\__\      |:|::/  /   \::/ /:/  /   \:\  \        \:\ \:\__\  
   \:\/:/  /    \/__/      |:|\/__/     \/_/:/  /     \:\  \        \:\/:/  /  
    \::/  /                |:|  |         /:/  /       \:\__\        \::/  /   
     \/__/                  \|__|         \/__/         \/__/         \/__/    
{Colors.RESET}{Colors.GRAY}              Just A Rather Very Intelligent System - v1.0.0 (Foundation Core)
{Colors.RESET}"""


def print_banner() -> None:
    safe_print(BANNER_TEXT)


def print_status_box(provider_name: str, model: str, tools_count: int, workspace: str) -> None:
    border = f"{Colors.BLUE}{'=' * 65}{Colors.RESET}"
    safe_print(border)
    safe_print(f"  {Colors.BOLD}[STATUS]{Colors.RESET} ONLINE (Phase 1: Foundation)")
    safe_print(f"  {Colors.BOLD}[COGNITIVE CORE]{Colors.RESET} {provider_name} (Model: {model})")
    safe_print(f"  {Colors.BOLD}[TOOLS]{Colors.RESET} {tools_count} tools registered")
    safe_print(f"  {Colors.BOLD}[WORKSPACE]{Colors.RESET} {workspace}")
    safe_print(f"  {Colors.BOLD}[HELP]{Colors.RESET} Type {Colors.CYAN}:help{Colors.RESET} for commands or enter any query directly.")
    safe_print(border)
    safe_print("")
