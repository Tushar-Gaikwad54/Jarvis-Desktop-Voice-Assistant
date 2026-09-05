/**
 * J.A.R.V.I.S. Frontend Application Controller
 * Manages PyWebView Native Bridge, AI Construction Boot Matrix, Real-time System Telemetry,
 * 60 FPS Particle Vortex, Capsule Waveform Visualizer, Speech Interrupt, & Male/Female Voice Personas.
 */

let vortex = null;
let isListening = false;
let isProcessing = false;
let voiceEnabled = true;
let currentVoiceGender = 'male';
let speechTimeout = null;
let waveformAnimId = null;

// =========================================================================
// INITIALIZATION
// =========================================================================
window.addEventListener('pywebviewready', () => {
  console.log('[JARVIS] PyWebView Bridge Connected.');
  startBootSequence();
});

document.addEventListener('DOMContentLoaded', () => {
  startClock();
  setupInputListeners();
  initWaveformVisualizer();

  // Fallback if opened directly in standard browser
  setTimeout(() => {
    const bootScreen = document.getElementById('boot-screen');
    if (bootScreen && !bootScreen.classList.contains('hidden')) {
      if (window.pywebview && window.pywebview.api) {
        startBootSequence();
      } else {
        simulateMockBoot();
      }
    }
  }, 900);
});

// Digital Clock Updater
function startClock() {
  const clockEl = document.getElementById('clock-display');
  function update() {
    const now = new Date();
    if (clockEl) {
      clockEl.innerText = now.toTimeString().split(' ')[0];
    }
  }
  update();
  setInterval(update, 1000);
}

// Input Event Listeners (Enter to Transmit, Esc to Interrupt, F11 to Fullscreen)
function setupInputListeners() {
  const input = document.getElementById('chat-input');
  if (input) {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendText();
      }
    });
  }

  // Global hotkeys
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      handleInterruptSpeech();
    } else if (e.key === 'F11') {
      e.preventDefault();
      handleToggleFullscreen();
    }
  });
}

// Fullscreen Mode Toggle
async function handleToggleFullscreen() {
  try {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.toggle_fullscreen) {
      await window.pywebview.api.toggle_fullscreen();
      return;
    }
  } catch (err) {
    console.warn('PyWebView fullscreen toggle notice:', err);
  }

  // Standard HTML5 browser fallback
  try {
    if (!document.fullscreenElement) {
      if (document.documentElement.requestFullscreen) {
        await document.documentElement.requestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        await document.exitFullscreen();
      }
    }
  } catch (err) {
    console.warn('Browser fullscreen error:', err);
  }
}

// =========================================================================
// SCREEN 1: BOOT SEQUENCE CONTROLLER
// =========================================================================
async function startBootSequence() {
  const logConsole = document.getElementById('boot-console');
  const statusLabel = document.getElementById('boot-status-label');
  const percentLabel = document.getElementById('boot-percent');
  const progressFill = document.getElementById('boot-progress-fill');

  function addLog(msg, colorClass = 'cyan') {
    if (!logConsole) return;
    const line = document.createElement('div');
    line.className = `boot-log-line ${colorClass}`;
    line.innerText = msg;
    logConsole.appendChild(line);
    logConsole.scrollTop = logConsole.scrollHeight;
  }

  function setProgress(percent, label) {
    if (percentLabel) percentLabel.innerText = `${percent}%`;
    if (progressFill) progressFill.style.width = `${percent}%`;
    if (statusLabel && label) statusLabel.innerText = label;
  }

  addLog('[BOOT] Establishing link with local hardware subsystems...', 'cyan');
  setProgress(15, 'SCANNING LOCAL OLLAMA DAEMON...');

  try {
    if (window.pywebview && window.pywebview.api) {
      const result = await window.pywebview.api.boot_sequence();

      // Process step logs returned from Python backend
      if (result.logs && Array.isArray(result.logs)) {
        for (const entry of result.logs) {
          addLog(entry.text, entry.type || 'cyan');
          setProgress(entry.percent || 50, entry.label || 'INITIALIZING...');
          await new Promise(r => setTimeout(r, 140));
        }
      }

      setProgress(100, 'SYSTEMS NOMINAL. ACCESS GRANTED.');
      addLog('[BOOT COMPLETE] Welcome back, Sir.', 'green');

      // Update model
      if (result.model) {
        const modelTag = document.getElementById('telemetry-model');
        if (modelTag) modelTag.innerText = result.model;
      }

      // Update persona
      if (result.voice_gender) {
        updateVoicePersonaUI(result.voice_gender);
      }

      // Update real hardware telemetry
      if (result.system_specs) {
        applyDiagnostics(result.system_specs);
      }

      if (result.live_telemetry) {
        applyLiveTelemetry(result.live_telemetry);
      }

      if (result.tool_count) {
        const toolBadge = document.getElementById('tool-count-badge');
        if (toolBadge) toolBadge.innerText = `${result.tool_count} TOOLS`;
      }
    } else {
      await simulateMockBoot();
    }
  } catch (err) {
    console.error('Boot sequence error:', err);
    addLog(`[WARNING] Boot sequence notice: ${err}`, 'amber');
    setProgress(100, 'INITIALIZED WITH FALLBACK MATRIX');
    fetchSystemSpecsDirectly();
  }

  // Smooth transition to main HUD
  setTimeout(() => {
    const bootScreen = document.getElementById('boot-screen');
    const mainScreen = document.getElementById('main-screen');
    if (bootScreen) bootScreen.classList.add('hidden');
    if (mainScreen) {
      mainScreen.classList.remove('hidden');
      if (!vortex) {
        vortex = new JarvisVortexCore('vortex-canvas');
      }
      startLiveTelemetryPolling();
    }
  }, 750);
}

// Fallback Mock Boot
async function simulateMockBoot() {
  const logConsole = document.getElementById('boot-console');
  const percentLabel = document.getElementById('boot-percent');
  const progressFill = document.getElementById('boot-progress-fill');
  const statusLabel = document.getElementById('boot-status-label');

  const steps = [
    { p: 25, label: 'SCANNING LOCAL OLLAMA DAEMON...', log: '[DAEMON] Detecting Ollama API on port 11434...', col: 'cyan' },
    { p: 55, label: 'CHECKING MODEL WEIGHTS (LLAMA-3.2)...', log: '[MODEL] LLM provider active: llama3.2 (Local Core)', col: 'green' },
    { p: 80, label: 'ENGAGING SAPI-5 AUDIO MATRIX...', log: '[AUDIO] Speech synthesis & microphone online.', col: 'cyan' },
    { p: 100, label: 'SYSTEMS ONLINE.', log: '[SYSTEM READY] All protocols initialized. Welcome, Sir.', col: 'green' }
  ];

  for (const step of steps) {
    if (percentLabel) percentLabel.innerText = `${step.p}%`;
    if (progressFill) progressFill.style.width = `${step.p}%`;
    if (statusLabel) statusLabel.innerText = step.label;
    if (logConsole) {
      const line = document.createElement('div');
      line.className = `boot-log-line ${step.col}`;
      line.innerText = step.log;
      logConsole.appendChild(line);
      logConsole.scrollTop = logConsole.scrollHeight;
    }
    await new Promise(r => setTimeout(r, 200));
  }

  fetchSystemSpecsDirectly();

  setTimeout(() => {
    const bootScreen = document.getElementById('boot-screen');
    const mainScreen = document.getElementById('main-screen');
    if (bootScreen) bootScreen.classList.add('hidden');
    if (mainScreen) {
      mainScreen.classList.remove('hidden');
      if (!vortex) {
        vortex = new JarvisVortexCore('vortex-canvas');
      }
      startLiveTelemetryPolling();
    }
  }, 600);
}

// =========================================================================
// SYSTEM DIAGNOSTICS & LIVE TELEMETRY
// =========================================================================
let telemetryTimer = null;

async function fetchSystemSpecsDirectly() {
  try {
    if (window.pywebview && window.pywebview.api) {
      const specs = await window.pywebview.api.get_system_specs();
      applyDiagnostics(specs);
    }
  } catch (e) {
    console.error('Direct specs query error:', e);
  }
}

function applyDiagnostics(specs) {
  if (!specs) return;
  const osEl = document.getElementById('diag-os');
  const cpuCoresEl = document.getElementById('diag-cpu-cores');
  const ramTotalEl = document.getElementById('diag-ram-total');
  const pathEl = document.getElementById('diag-path');

  if (osEl && specs.os) osEl.innerText = specs.os;
  if (cpuCoresEl && specs.cpu_cores) cpuCoresEl.innerText = specs.cpu_cores;
  if (ramTotalEl && specs.ram) ramTotalEl.innerText = specs.ram;
  if (pathEl && specs.path) {
    pathEl.innerText = specs.path;
    if (specs.full_path) {
      pathEl.title = specs.full_path;
    }
  }
}

function applyLiveTelemetry(t) {
  if (!t) return;

  // 1. CPU Live Meter
  const cpuVal = document.getElementById('diag-cpu-val');
  const cpuCores = document.getElementById('diag-cpu-cores');
  const cpuBar = document.getElementById('diag-cpu-bar');
  if (cpuVal && t.cpu_percent !== undefined) cpuVal.innerText = `${t.cpu_percent}%`;
  if (cpuCores && t.cpu_cores) cpuCores.innerText = t.cpu_cores;
  if (cpuBar && t.cpu_percent !== undefined) {
    cpuBar.style.width = `${Math.min(100, Math.max(0, t.cpu_percent))}%`;
    if (t.cpu_percent > 85) cpuBar.classList.add('warn'); else cpuBar.classList.remove('warn');
  }

  // 2. RAM Live Meter
  const ramTotal = document.getElementById('diag-ram-total');
  const ramUsed = document.getElementById('diag-ram-used');
  const ramSub = document.getElementById('diag-ram-sub');
  const ramBar = document.getElementById('diag-ram-bar');
  if (ramTotal && t.ram_total_disp) ramTotal.innerText = t.ram_total_disp;
  if (ramUsed && t.ram_used_gb !== undefined) ramUsed.innerText = `${t.ram_used_gb} GB`;
  if (ramSub && t.ram_avail_gb !== undefined && t.ram_percent !== undefined) {
    ramSub.innerText = `Avail: ${t.ram_avail_gb} GB (${t.ram_percent}%)`;
  }
  if (ramBar && t.ram_percent !== undefined) {
    ramBar.style.width = `${Math.min(100, Math.max(0, t.ram_percent))}%`;
    if (t.ram_percent > 85) ramBar.classList.add('warn'); else ramBar.classList.remove('warn');
  }

  // 3. GPU Live Meter
  const gpuLabel = document.getElementById('diag-gpu-label');
  const gpuVal = document.getElementById('diag-gpu-val');
  const gpuSub = document.getElementById('diag-gpu-sub');
  const gpuBar = document.getElementById('diag-gpu-bar');
  if (gpuLabel && t.gpu_name) {
    const shortName = t.gpu_name.replace('Laptop GPU', '').replace('GeForce ', '').trim();
    gpuLabel.innerText = `GPU (${shortName || 'RTX'})`;
  }
  if (gpuVal && t.gpu_percent !== undefined) gpuVal.innerText = `${t.gpu_percent}%`;
  if (gpuSub && t.gpu_vram_disp) {
    gpuSub.innerText = `VRAM: ${t.gpu_vram_disp}`;
  }
  if (gpuBar) {
    const barPct = t.gpu_vram_pct !== undefined && t.gpu_vram_pct > 0 ? t.gpu_vram_pct : t.gpu_percent;
    gpuBar.style.width = `${Math.min(100, Math.max(0, barPct || 0))}%`;
  }

  // 4. Disk Storage Live Meter
  const diskFree = document.getElementById('diag-disk-free');
  const diskSub = document.getElementById('diag-disk-sub');
  const diskBar = document.getElementById('diag-disk-bar');
  if (diskFree && t.disk_free_gb !== undefined) diskFree.innerText = `${t.disk_free_gb} GB Free`;
  if (diskSub && t.disk_total_gb !== undefined && t.disk_percent !== undefined) {
    diskSub.innerText = `Total: ${t.disk_total_gb} GB (${t.disk_percent}% used)`;
  }
  if (diskBar && t.disk_percent !== undefined) {
    diskBar.style.width = `${Math.min(100, Math.max(0, t.disk_percent))}%`;
    if (t.disk_percent > 90) diskBar.classList.add('warn'); else diskBar.classList.remove('warn');
  }
}

function startLiveTelemetryPolling() {
  if (telemetryTimer) clearInterval(telemetryTimer);

  async function update() {
    try {
      if (window.pywebview && window.pywebview.api && window.pywebview.api.get_live_telemetry) {
        const live = await window.pywebview.api.get_live_telemetry();
        applyLiveTelemetry(live);
      }
    } catch (e) {
      console.warn('Telemetry update notice:', e);
    }
  }

  // Immediate first update
  update();
  // Poll every 1.8 seconds for continuous live readings
  telemetryTimer = setInterval(update, 1800);
}

// =========================================================================
// UI STATE & HUD CONTROLLER
// =========================================================================
function setHUDState(state, statusText) {
  if (vortex) vortex.setState(state);

  const statusCapsule = document.getElementById('hud-status-capsule');
  const statusTextEl = document.getElementById('hud-status-text');
  const vortexBadge = document.getElementById('vortex-status-badge');
  const statusDot = document.getElementById('system-status-dot');
  const interruptBtn = document.getElementById('interrupt-btn');

  if (statusCapsule) {
    statusCapsule.className = `hud-status-capsule ${state}`;
  }

  let displayText = 'NEURAL CORE // ACTIVE';
  let badgeText = 'READY FOR VOICE OR TEXT COMMANDS';

  if (state === 'listening') {
    displayText = 'SENSORS // LISTENING (SPEAK NOW)';
    badgeText = 'LISTENING FOR VOCAL DIRECTIVE...';
  } else if (state === 'thinking') {
    displayText = 'COGNITION // CONSULTING LOCAL MATRIX';
    badgeText = 'PROCESSING QUERY & ENGAGING TOOLS...';
  } else if (state === 'speaking') {
    displayText = 'AUDIO MATRIX // TRANSMITTING VOCAL SYNTHESIS';
    badgeText = 'TRANSMITTING VOCAL SYNTHESIS...';
  } else if (statusText) {
    displayText = statusText;
    badgeText = statusText;
  }

  if (statusTextEl) statusTextEl.innerText = displayText;
  if (vortexBadge) vortexBadge.innerText = badgeText;

  if (statusDot) {
    statusDot.className = `status-indicator-dot ${state}`;
  }

  // Manage interrupt button pulse glow
  if (interruptBtn) {
    if (state === 'speaking' || state === 'thinking') {
      interruptBtn.classList.add('active');
    } else {
      interruptBtn.classList.remove('active');
    }
  }
}

// =========================================================================
// CAPSULE WAVEFORM VISUALIZER
// =========================================================================
function initWaveformVisualizer() {
  const canvas = document.getElementById('waveform-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let waveTime = 0;

  function renderWave() {
    waveTime += 0.08;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const barCount = 18;
    const barWidth = 3;
    const spacing = 4;
    const startX = (canvas.width - (barCount * (barWidth + spacing))) / 2;

    for (let i = 0; i < barCount; i++) {
      let amp = 0.15;
      if (isListening) {
        amp = 0.35 + 0.65 * Math.abs(Math.sin(waveTime * 3.5 + i * 0.45));
      } else if (isProcessing) {
        amp = 0.2 + 0.45 * Math.abs(Math.sin(waveTime * 5 + i * 0.8));
      } else {
        amp = 0.1 + 0.18 * Math.abs(Math.sin(waveTime * 1.5 + i * 0.35));
      }

      const barHeight = Math.max(3, amp * 22);
      const x = startX + i * (barWidth + spacing);
      const y = (canvas.height - barHeight) / 2;

      const grad = ctx.createLinearGradient(x, y, x, y + barHeight);
      grad.addColorStop(0, '#ffffff');
      grad.addColorStop(0.5, '#00f2fe');
      grad.addColorStop(1, '#0088cc');

      ctx.fillStyle = grad;
      ctx.beginPath();
      if (ctx.roundRect) {
        ctx.roundRect(x, y, barWidth, barHeight, 2);
      } else {
        ctx.rect(x, y, barWidth, barHeight);
      }
      ctx.fill();
    }

    waveformAnimId = requestAnimationFrame(renderWave);
  }

  renderWave();
}

// =========================================================================
// CHAT MESSAGES & TOOL RENDERING
// =========================================================================
function appendMessage(sender, text, toolInfo = null) {
  const container = document.getElementById('chat-messages');
  if (!container) return;

  // Remove existing temporary progress bubble if present
  const existingProg = document.getElementById('active-query-progress');
  if (existingProg) existingProg.remove();

  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${sender}`;

  const personaName = currentVoiceGender === 'female' ? 'F.R.I.D.A.Y.' : 'J.A.R.V.I.S.';

  // Sender Header
  const senderHeader = document.createElement('div');
  senderHeader.className = `bubble-sender ${sender === 'user' ? 'user' : (currentVoiceGender === 'female' ? 'female' : '')}`;
  senderHeader.innerText = sender === 'user' ? 'SIR' : personaName;
  bubble.appendChild(senderHeader);

  // If tool was executed, render badge
  if (toolInfo) {
    const badge = document.createElement('div');
    badge.className = 'tool-badge';
    badge.innerHTML = `<span>⚡</span> <span>Executed: ${escapeHtml(toolInfo)}</span>`;
    bubble.appendChild(badge);
  }

  // Text content
  const textEl = document.createElement('div');
  textEl.className = 'bubble-text';
  textEl.innerHTML = formatMessageContent(text);
  bubble.appendChild(textEl);

  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
}

function showProgressBubble(promptText = 'A new interaction is in progress, with a subtle progress animation.') {
  const container = document.getElementById('chat-messages');
  if (!container) return;

  const prog = document.createElement('div');
  prog.className = 'chat-bubble assistant progress-bubble';
  prog.id = 'active-query-progress';

  prog.innerHTML = `
    <div class="bubble-sender ${currentVoiceGender === 'female' ? 'female' : ''}">${currentVoiceGender === 'female' ? 'F.R.I.D.A.Y.' : 'J.A.R.V.I.S.'}</div>
    <div class="bubble-text">${promptText}</div>
    <div class="typing-dots">
      <span></span><span></span><span></span>
    </div>
  `;

  container.appendChild(prog);
  container.scrollTop = container.scrollHeight;
}

function escapeHtml(text) {
  return (text || '').replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function formatMessageContent(text) {
  if (!text) return '';
  let safe = escapeHtml(text);
  safe = safe.replace(/`([^`]+)`/g, '<code style="background: rgba(0,242,254,0.15); padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono); color: #00f2fe;">$1</code>');
  safe = safe.replace(/\*\*([^*]+)\*\*/g, '<strong style="color: #ffffff;">$1</strong>');
  safe = safe.replace(/\n/g, '<br/>');
  return safe;
}

// =========================================================================
// ACTIONS & EVENT DISPATCHERS
// =========================================================================

// Transmit Query
async function handleSendText() {
  const input = document.getElementById('chat-input');
  if (!input || isProcessing) return;

  const text = input.value.trim();
  if (!text) return;

  input.value = '';
  isProcessing = true;

  if (speechTimeout) {
    clearTimeout(speechTimeout);
    speechTimeout = null;
  }

  appendMessage('user', text);
  showProgressBubble();
  setHUDState('thinking');

  try {
    if (window.pywebview && window.pywebview.api) {
      const response = await window.pywebview.api.send_query(text);
      
      const responseText = response.text || response;
      const toolInfo = response.tool || null;

      setHUDState('speaking');
      appendMessage('assistant', responseText, toolInfo);

      const responseLen = responseText.length;
      const readingDuration = Math.min(16000, Math.max(2500, responseLen * 45));
      speechTimeout = setTimeout(() => {
        setHUDState('idle');
        isProcessing = false;
        speechTimeout = null;
      }, readingDuration);
    } else {
      setTimeout(() => {
        appendMessage('assistant', `Acknowledged, Sir. Query received: "${text}"`);
        setHUDState('idle');
        isProcessing = false;
      }, 1000);
    }
  } catch (err) {
    console.error('Query dispatch error:', err);
    appendMessage('assistant', `System processing error: ${err}`);
    setHUDState('idle');
    isProcessing = false;
  }
}

// Instant Speech Interrupt
async function handleInterruptSpeech() {
  if (speechTimeout) {
    clearTimeout(speechTimeout);
    speechTimeout = null;
  }

  isProcessing = false;
  try {
    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.stop_speech();
    }
  } catch (e) {
    console.error('Interrupt speech bridge error:', e);
  }

  setHUDState('idle', 'SPEECH HALTED // READY');
  setTimeout(() => setHUDState('idle'), 1800);
}

// Microphone Voice Listening
async function toggleVoiceListening() {
  const micBtn = document.getElementById('voice-mic-btn');
  if (isListening || isProcessing) return;

  if (speechTimeout) {
    clearTimeout(speechTimeout);
    speechTimeout = null;
  }

  isListening = true;
  if (micBtn) micBtn.classList.add('active');
  setHUDState('listening');

  try {
    if (window.pywebview && window.pywebview.api) {
      const result = await window.pywebview.api.listen_voice();

      if (micBtn) micBtn.classList.remove('active');
      isListening = false;

      if (result && result.text) {
        appendMessage('user', result.text);
        isProcessing = true;
        showProgressBubble('Transcribing audio directive...');
        setHUDState('thinking');

        const response = await window.pywebview.api.send_query(result.text);
        const responseText = response.text || response;
        const toolInfo = response.tool || null;

        setHUDState('speaking');
        appendMessage('assistant', responseText, toolInfo);

        const responseLen = responseText.length;
        const readingDuration = Math.min(16000, Math.max(2500, responseLen * 45));
        speechTimeout = setTimeout(() => {
          setHUDState('idle');
          isProcessing = false;
          speechTimeout = null;
        }, readingDuration);
      } else {
        setHUDState('idle', 'NO AUDIO DETECTED');
        setTimeout(() => setHUDState('idle'), 1800);
      }
    } else {
      setTimeout(() => {
        if (micBtn) micBtn.classList.remove('active');
        isListening = false;
        setHUDState('idle');
      }, 2500);
    }
  } catch (err) {
    console.error('Voice listening error:', err);
    if (micBtn) micBtn.classList.remove('active');
    isListening = false;
    setHUDState('idle', 'VOICE SENSOR ERROR');
  }
}

// Voice Persona Switch (Male J.A.R.V.I.S. / Female F.R.I.D.A.Y.)
async function handleToggleVoiceGender() {
  try {
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.toggle_voice_gender();
      if (res && res.gender) {
        updateVoicePersonaUI(res.gender);
      }
    } else {
      const target = currentVoiceGender === 'male' ? 'female' : 'male';
      updateVoicePersonaUI(target);
    }
  } catch (err) {
    console.error('Voice gender toggle error:', err);
  }
}

function updateVoicePersonaUI(gender) {
  currentVoiceGender = (gender || 'male').toLowerCase();
  const isFemale = currentVoiceGender === 'female';

  const telemetryPersona = document.getElementById('telemetry-persona');
  const personaBtn = document.getElementById('persona-btn');
  const personaIcon = document.getElementById('persona-btn-icon');
  const personaLabel = document.getElementById('persona-btn-label');
  const brandTitle = document.getElementById('hud-brand-title');
  const initialAgentLabel = document.getElementById('initial-agent-label');

  if (isFemale) {
    if (telemetryPersona) {
      telemetryPersona.innerText = 'FEMALE';
      telemetryPersona.classList.add('female');
    }
    if (personaBtn) personaBtn.classList.add('female-mode');
    if (personaIcon) personaIcon.innerText = '♀';
    if (personaLabel) personaLabel.innerText = 'Voice Female';
    if (brandTitle) brandTitle.innerText = 'F.R.I.D.A.Y.';
    if (initialAgentLabel) {
      initialAgentLabel.innerText = 'F.R.I.D.A.Y.';
      initialAgentLabel.classList.add('female');
    }
  } else {
    if (telemetryPersona) {
      telemetryPersona.innerText = 'MALE';
      telemetryPersona.classList.remove('female');
    }
    if (personaBtn) personaBtn.classList.remove('female-mode');
    if (personaIcon) personaIcon.innerText = '♂';
    if (personaLabel) personaLabel.innerText = 'Voice Male';
    if (brandTitle) brandTitle.innerText = 'J.A.R.V.I.S.';
    if (initialAgentLabel) {
      initialAgentLabel.innerText = 'J.A.R.V.I.S.';
      initialAgentLabel.classList.remove('female');
    }
  }
}

// Voice Audio Synthesis Toggle (Mute / Unmute)
async function toggleAudioMute() {
  voiceEnabled = !voiceEnabled;
  const powerBtn = document.getElementById('voice-power-btn');
  const powerIcon = document.getElementById('voice-power-icon');
  const powerLabel = document.getElementById('voice-power-label');

  if (voiceEnabled) {
    if (powerBtn) {
      powerBtn.classList.add('active');
      powerBtn.classList.remove('muted');
    }
    if (powerIcon) powerIcon.innerText = '🔊';
    if (powerLabel) powerLabel.innerText = 'Voice On';
  } else {
    if (powerBtn) {
      powerBtn.classList.remove('active');
      powerBtn.classList.add('muted');
    }
    if (powerIcon) powerIcon.innerText = '🔇';
    if (powerLabel) powerLabel.innerText = 'Voice Muted';
    handleInterruptSpeech();
  }

  if (window.pywebview && window.pywebview.api) {
    await window.pywebview.api.toggle_voice(voiceEnabled);
  }
}

// Launch Default Text Editor (Notepad)
async function handleOpenTextEditor() {
  try {
    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.open_text_editor();
    }
    setHUDState('idle', 'NOTEPAD LAUNCHED');
    setTimeout(() => setHUDState('idle'), 2000);
  } catch (err) {
    console.error('Open editor error:', err);
  }
}

// Quick Suggestion Click
function sendSuggestion(text) {
  const input = document.getElementById('chat-input');
  if (input) {
    input.value = text;
    handleSendText();
  }
}
