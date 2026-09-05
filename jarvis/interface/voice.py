"""
Modular Voice Interface Bridge for J.A.R.V.I.S.
Provides Windows-native Text-to-Speech (with Male/Female Persona toggle and instant interruptibility)
and Speech-to-Text microphone input.
"""

from typing import Optional
import base64
import os
import re
import subprocess
import threading

from jarvis.config import get_config
from jarvis.core.logger import Colors, logger, safe_print


def clean_text_for_speech(text: str) -> str:
    """
    Cleans raw LLM responses for natural, human-friendly Text-to-Speech.
    Strips code blocks, markdown syntax, literal escape sequences (\\n, \\t),
    URLs, file path slashes, emojis, and noisy symbols so speech engine reads
    only clean spoken sentences without reading out technical symbols.
    """
    if not text:
        return ""

    s = str(text)

    # 1. Strip horizontal rule lines (---, ===, ___, ***)
    s = re.sub(r'^\s*[-=_*]{3,}\s*$', ' ', s, flags=re.MULTILINE)
    s = re.sub(r'[-=_*]{3,}', ' ', s)

    # 2. Replace multi-line markdown code blocks (```lang ... ```)
    s = re.sub(r'```[\w\-]*\n[\s\S]*?```', '. I have displayed the code on your screen. ', s)
    s = re.sub(r'```[\s\S]*?```', '. I have displayed the code on your screen. ', s)

    # 3. Replace markdown links [Title](URL) with just Title
    s = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', s)

    # 4. Remove raw URLs
    s = re.sub(r'https?://\S+|www\.\S+', 'a web link', s)

    # 5. Remove markdown tables (lines starting and ending with | or separator rows |---|)
    s = re.sub(r'\|[^\n]+\|', ' ', s)

    # 6. Unescape explicit literal escape sequences (like \n, \r)
    s = re.sub(r'\\+n', '\n', s)
    s = re.sub(r'\\+r', '\r', s)

    # 7. Replace inline code `variable` -> variable (and replace underscores in identifiers with spaces)
    def clean_inline_code(match):
        code_txt = match.group(1)
        return ' ' + code_txt.replace('_', ' ') + ' '
    s = re.sub(r'`([^`]+)`', clean_inline_code, s)

    # 8. Remove markdown headers (#, ##, ###, ####)
    s = re.sub(r'^\s*#{1,6}\s+', '', s, flags=re.MULTILINE)

    # 9. Remove markdown bullet points and numbering (*, -, +, 1.) at line start
    s = re.sub(r'^\s*[\*\-\+]\s+', ' ', s, flags=re.MULTILINE)
    s = re.sub(r'^\s*\d+[\.\)]\s+', ' ', s, flags=re.MULTILINE)
    s = re.sub(r'^\s*>\s+', '', s, flags=re.MULTILINE)  # blockquotes

    # 10. Remove bold/italic markdown marks: **, __, *, _
    s = re.sub(r'\*\*([^*]+)\*\*', r'\1', s)
    s = re.sub(r'__([^_]+)__', r'\1', s)
    s = re.sub(r'\*([^*]+)\*', r'\1', s)
    s = re.sub(r'_([^_]+)_', r'\1', s)

    # 11. Replace Windows backslashes and slashes (avoid "backslash Users backslash...")
    s = re.sub(r'[\\\/]', ' ', s)

    # 12. Remove emojis and non-standard unicode symbols
    emoji_pattern = re.compile(
        r'[\U00010000-\U0010ffff]'  # High code points (Emojis, symbols)
        r'|[\u2600-\u27bf]'          # Misc symbols & Dingbats
        r'|[\u2300-\u23ff]'          # Misc technical
        r'|[\u2b50\u2b55\u200d\ufe0f]'
        r'|[\u2022\u2023\u25b6\u25c0\u25a0\u25aa\u25cb\u25cf]' # Bullet shapes
    )
    s = emoji_pattern.sub('', s)

    # 13. Remove noisy ASCII symbols that SAPI reads awkwardly
    s = re.sub(r'[\~`\^\@\#\$\%\&\*\=\+\<\>\|\{\}\[\]_\(\)]', ' ', s)

    # 14. Convert newlines to periods for natural speech pauses
    s = re.sub(r'[\r\n]+', '. ', s)

    # 15. Normalize punctuation spacing (avoid "..", ",.", " .", etc.)
    s = re.sub(r'\s*([,.:;!?])\s*', r'\1 ', s)
    s = re.sub(r'([,.:;!?])(?:\s*[,.:;!?])+', r'\1', s)
    s = re.sub(r'\s+', ' ', s).strip()

    return s


class VoiceBridge:
    def __init__(self):
        self.config = get_config()
        self._current_process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._is_stopped = False
        self._gender: str = getattr(self.config.voice, "voice_gender", "male").lower()

    @property
    def gender(self) -> str:
        return self._gender

    @gender.setter
    def gender(self, value: str) -> None:
        self.set_gender(value)

    def set_gender(self, gender: str) -> str:
        """Set voice gender: 'male' (J.A.R.V.I.S.) or 'female' (F.R.I.D.A.Y.)."""
        normalized = "female" if str(gender).strip().lower() in ("female", "f", "friday", "zira", "hazel") else "male"
        self._gender = normalized
        self.config.voice.voice_gender = normalized
        return self._gender

    def stop(self) -> None:
        """Immediately interrupts and halts any active speech synthesis."""
        with self._lock:
            self._is_stopped = True
            if self._current_process is not None:
                try:
                    pid = self._current_process.pid
                    self._current_process.kill()
                    creationflags = 0x08000000 if os.name == "nt" else 0
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=creationflags,
                        check=False,
                    )
                except Exception:
                    pass
                self._current_process = None

    def is_speaking(self) -> bool:
        """Returns True if speech synthesis is currently active."""
        with self._lock:
            if self._current_process is not None:
                return self._current_process.poll() is None
            return False

    def speak(self, text: str, gender: Optional[str] = None) -> None:
        """
        Speak text using Windows native SAPI speech engine.
        Automatically sanitizes text to remove markdown, code blocks, literal \\n, and slashes.
        Can be interrupted at any time using self.stop().
        """
        if not text or not str(text).strip():
            return

        # Sanitize text so SAPI reads human conversational speech
        cleaned_text = clean_text_for_speech(text)
        if not cleaned_text or not cleaned_text.strip():
            return

        # Stop any active speaking before starting new audio
        self.stop()

        target_gender = (gender or self._gender or "male").lower()

        try:
            # Convert JARVIS's configured rate (175 = normal) into
            # Windows SAPI's -10..10 rate scale.
            sapi_rate = max(
                -10,
                min(10, round((self.config.voice.tts_rate - 175) / 10))
            )

            sapi_volume = max(
                0,
                min(100, round(self.config.voice.tts_volume * 100))
            )

            # repr() safely quotes the response for PowerShell.
            safe_text = repr(cleaned_text)

            ps_script = f"""
Add-Type -AssemblyName System.Speech

$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = {sapi_rate}
$synth.Volume = {sapi_volume}

$targetGender = "{target_gender}".ToLower()
if ($targetGender -eq "female") {{
    $voice = $synth.GetInstalledVoices() | Where-Object {{ $_.VoiceInfo.Gender -eq [System.Speech.Synthesis.VoiceGender]::Female -and $_.Enabled }} | Select-Object -First 1
    if ($voice) {{
        $synth.SelectVoice($voice.VoiceInfo.Name)
    }} else {{
        try {{ $synth.SelectVoiceByHints([System.Speech.Synthesis.VoiceGender]::Female) }} catch {{}}
    }}
}} else {{
    $voice = $synth.GetInstalledVoices() | Where-Object {{ $_.VoiceInfo.Gender -eq [System.Speech.Synthesis.VoiceGender]::Male -and $_.Enabled }} | Select-Object -First 1
    if ($voice) {{
        $synth.SelectVoice($voice.VoiceInfo.Name)
    }} else {{
        try {{ $synth.SelectVoiceByHints([System.Speech.Synthesis.VoiceGender]::Male) }} catch {{}}
    }}
}}

$synth.Speak({safe_text})
$synth.Dispose()
"""

            encoded_command = base64.b64encode(
                ps_script.encode("utf-16le")
            ).decode("ascii")

            with self._lock:
                self._is_stopped = False
                creationflags = 0x08000000 if os.name == "nt" else 0
                self._current_process = subprocess.Popen(
                    [
                        "powershell.exe",
                        "-NoProfile",
                        "-NonInteractive",
                        "-EncodedCommand",
                        encoded_command,
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    creationflags=creationflags,
                    text=True,
                )

            try:
                _, stderr = self._current_process.communicate(timeout=120)
                if self._current_process.returncode != 0 and not self._is_stopped:
                    error = stderr.strip() if stderr else ""
                    if error:
                        logger.error(f"Windows SAPI speech error: {error}")
            except subprocess.TimeoutExpired:
                self.stop()
                logger.error("Windows SAPI speech timed out.")
            except Exception as e:
                if not self._is_stopped:
                    logger.error(f"Speech output error: {e}")
            finally:
                with self._lock:
                    self._current_process = None

        except Exception as e:
            if not self._is_stopped:
                logger.error(f"Speech output initialization error: {e}")

    def listen(
        self,
        timeout: int = 6,
        phrase_time_limit: int = 8
    ) -> Optional[str]:
        """Listen to microphone input and convert speech to text."""
        # Stop speech before opening microphone
        self.stop()

        try:
            import speech_recognition as sr

            r = sr.Recognizer()
            r.energy_threshold = 300
            r.dynamic_energy_threshold = True
            r.pause_threshold = 0.8

            with sr.Microphone() as source:
                safe_print(
                    f"{Colors.MAGENTA}[MIC]{Colors.RESET} "
                    "Listening for your voice command... (Speak now)"
                )

                r.adjust_for_ambient_noise(
                    source,
                    duration=0.5
                )

                audio = r.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )

            safe_print(
                f"{Colors.CYAN}[VOICE]{Colors.RESET} "
                "Recognizing speech..."
            )

            query = r.recognize_google(audio)

            safe_print(
                f"{Colors.GREEN}[HEARD]{Colors.RESET} "
                f"\"{query}\""
            )

            return query

        except sr.WaitTimeoutError:
            safe_print(
                f"{Colors.GRAY}[MIC]{Colors.RESET} "
                "No speech detected (timeout)."
            )
            return None

        except sr.UnknownValueError:
            safe_print(
                f"{Colors.YELLOW}[VOICE]{Colors.RESET} "
                "Could not understand audio. Please try again."
            )
            self.speak(
                "Sorry, I could not understand that. Please try again."
            )
            return None

        except sr.RequestError as e:
            safe_print(
                f"{Colors.RED}[VOICE ERROR]{Colors.RESET} "
                f"Speech service unavailable: {e}"
            )
            return None

        except Exception as e:
            safe_print(
                f"{Colors.RED}[MIC ERROR]{Colors.RESET} "
                f"Microphone error: {e}"
            )
            return None


# Global voice bridge instance
voice_bridge = VoiceBridge()