/**
 * J.A.R.V.I.S. Neural Particle Vortex Core Engine
 * 60 FPS HTML5 Canvas 3D Accretion Vortex, Spiral Arm Physics, & Kinetic Audio Reactivity.
 * Recreates the iconic glowing cyan/azure vortex from the Liquid Glass HUD.
 */

class JarvisVortexCore {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');

    this.state = 'idle'; // 'idle', 'listening', 'thinking', 'speaking'
    this.time = 0;
    this.rotationAngle = 0;
    this.targetRotSpeed = 0.006;
    this.rotSpeed = 0.006;
    this.pulseFactor = 1.0;
    this.audioWave = 0.0;

    // High DPI Support & Canvas Sizing
    this.resize();
    window.addEventListener('resize', () => this.resize());

    // Particle Swarm Configuration
    this.particleCount = 420;
    this.particles = [];
    this.arms = 3; // Logarithmic spiral arms
    this.initParticles();

    // Orbital dust ring
    this.dustCount = 60;
    this.dustParticles = [];
    this.initDust();

    // Energy filaments
    this.filaments = [
      { radius: this.cx * 0.36, speed: 0.015, width: 1.8, alpha: 0.7, dash: [14, 28] },
      { radius: this.cx * 0.50, speed: -0.011, width: 1.2, alpha: 0.5, dash: [8, 16] },
      { radius: this.cx * 0.66, speed: 0.008, width: 1.5, alpha: 0.4, dash: [4, 12] },
    ];

    this.animate = this.animate.bind(this);
    requestAnimationFrame(this.animate);
  }

  resize() {
    if (!this.canvas) return;
    const parent = this.canvas.parentElement;
    const rect = parent ? parent.getBoundingClientRect() : null;
    const available = rect ? Math.min(rect.width || 420, rect.height || 420) : 420;
    const size = Math.max(300, Math.min(available * 0.92, 540));
    this.dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.width = size;
    this.height = size;
    this.canvas.width = size * this.dpr;
    this.canvas.height = size * this.dpr;
    this.canvas.style.width = `${size}px`;
    this.canvas.style.height = `${size}px`;
    this.ctx.scale(this.dpr, this.dpr);

    const prevCx = this.cx;
    this.cx = size / 2;
    this.cy = size / 2;

    if (prevCx && prevCx !== this.cx) {
      const scale = this.cx / prevCx;
      if (this.particles) {
        for (let p of this.particles) {
          p.baseR *= scale;
          p.r *= scale;
        }
      }
      if (this.dustParticles) {
        for (let d of this.dustParticles) {
          d.r *= scale;
        }
      }
      if (this.filaments) {
        for (let f of this.filaments) {
          f.radius *= scale;
        }
      }
    }
  }

  initParticles() {
    this.particles = [];
    for (let i = 0; i < this.particleCount; i++) {
      const armIndex = i % this.arms;
      const armOffset = (armIndex * (Math.PI * 2)) / this.arms;
      
      // Radius distribution: dense near center, thinning out
      const normDist = Math.pow(Math.random(), 1.6);
      const r = 24 + normDist * (this.cx * 0.72);
      
      // Logarithmic spiral angle + jitter
      const spiralTheta = Math.log(r / 20) * 3.2 + armOffset + (Math.random() - 0.5) * 0.45;
      const speed = (0.007 + (1 - normDist) * 0.014) * (0.8 + Math.random() * 0.4);
      const size = 1.0 + Math.random() * 2.2 * (1 - normDist * 0.5);
      const alpha = 0.35 + Math.random() * 0.65;

      this.particles.push({
        r,
        baseR: r,
        theta: spiralTheta,
        speed,
        size,
        alpha,
        armIndex,
        z: (Math.random() - 0.5) * 40,
        colorType: Math.random() > 0.85 ? 'white' : (Math.random() > 0.3 ? 'cyan' : 'azure')
      });
    }
  }

  initDust() {
    this.dustParticles = [];
    for (let i = 0; i < this.dustCount; i++) {
      this.dustParticles.push({
        r: 10 + Math.random() * (this.cx * 0.88),
        angle: Math.random() * Math.PI * 2,
        speed: (Math.random() - 0.5) * 0.005,
        size: 0.8 + Math.random() * 1.5,
        alpha: 0.2 + Math.random() * 0.4,
        pulseSpeed: 0.02 + Math.random() * 0.04
      });
    }
  }

  setState(newState) {
    this.state = newState;
    if (newState === 'thinking') {
      this.targetRotSpeed = 0.024;
    } else if (newState === 'listening') {
      this.targetRotSpeed = 0.014;
    } else if (newState === 'speaking') {
      this.targetRotSpeed = 0.018;
    } else {
      this.targetRotSpeed = 0.006;
    }
  }

  animate() {
    this.time += 0.028;
    // Smooth speed transitions
    this.rotSpeed += (this.targetRotSpeed - this.rotSpeed) * 0.05;
    this.rotationAngle += this.rotSpeed;

    // Reactivity to voice states
    if (this.state === 'speaking') {
      this.audioWave = Math.sin(this.time * 6) * 0.35 + Math.sin(this.time * 12) * 0.2;
      this.pulseFactor = 1.0 + Math.abs(this.audioWave) * 0.18;
    } else if (this.state === 'listening') {
      this.audioWave = Math.sin(this.time * 8) * 0.25;
      this.pulseFactor = 1.0 + Math.abs(this.audioWave) * 0.12;
    } else if (this.state === 'thinking') {
      this.audioWave = Math.sin(this.time * 14) * 0.15;
      this.pulseFactor = 0.95 + Math.sin(this.time * 9) * 0.08;
    } else {
      this.audioWave = 0;
      this.pulseFactor = 1.0 + Math.sin(this.time * 1.8) * 0.025;
    }

    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    // Composite mode for additive neon glow
    ctx.save();
    this.drawNebulaGlow();
    this.drawEnergyFilaments();
    this.drawVortexParticles();
    this.drawCoreAccretionDisk();
    this.drawDustSparkles();
    ctx.restore();

    requestAnimationFrame(this.animate);
  }

  drawNebulaGlow() {
    const ctx = this.ctx;
    const cx = this.cx;
    const cy = this.cy;
    const t = this.time;

    // Deep cyan/blue outer atmospheric glow
    let glowColor1 = 'rgba(0, 229, 255, 0.12)';
    let glowColor2 = 'rgba(0, 140, 255, 0.06)';
    if (this.state === 'thinking') {
      glowColor1 = 'rgba(255, 170, 0, 0.16)';
      glowColor2 = 'rgba(0, 229, 255, 0.08)';
    } else if (this.state === 'listening') {
      glowColor1 = 'rgba(0, 255, 200, 0.18)';
      glowColor2 = 'rgba(0, 200, 255, 0.08)';
    } else if (this.state === 'speaking') {
      glowColor1 = 'rgba(0, 240, 255, 0.22)';
      glowColor2 = 'rgba(0, 160, 255, 0.12)';
    }

    const grad = ctx.createRadialGradient(cx, cy, 14, cx, cy, cx * 0.88 * this.pulseFactor);
    grad.addColorStop(0, 'rgba(0, 242, 254, 0.28)');
    grad.addColorStop(0.35, glowColor1);
    grad.addColorStop(0.7, glowColor2);
    grad.addColorStop(1, 'transparent');

    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(cx, cy, cx * 0.9, 0, Math.PI * 2);
    ctx.fill();
  }

  drawEnergyFilaments() {
    const ctx = this.ctx;
    const cx = this.cx;
    const cy = this.cy;
    const t = this.time;

    ctx.globalCompositeOperation = 'lighter';

    for (let f of this.filaments) {
      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(t * f.speed * (this.state === 'thinking' ? 2.5 : 1.0));

      const r = f.radius * this.pulseFactor;
      ctx.strokeStyle = this.state === 'thinking' 
        ? `rgba(255, 180, 50, ${f.alpha})`
        : `rgba(0, 230, 255, ${f.alpha})`;
      ctx.lineWidth = f.width;
      ctx.setLineDash(f.dash);

      ctx.beginPath();
      ctx.arc(0, 0, r, 0, Math.PI * 2);
      ctx.stroke();

      // Accent filament nodes
      const nodeCount = 3;
      for (let n = 0; n < nodeCount; n++) {
        const nodeAngle = (n * Math.PI * 2) / nodeCount + t * 0.5;
        const nx = r * Math.cos(nodeAngle);
        const ny = r * Math.sin(nodeAngle);
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(nx, ny, 1.8, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.restore();
    }
  }

  drawVortexParticles() {
    const ctx = this.ctx;
    const cx = this.cx;
    const cy = this.cy;
    ctx.globalCompositeOperation = 'lighter';

    for (let p of this.particles) {
      // Advance angle based on angular velocity
      p.theta += p.speed * (this.rotSpeed / 0.006);

      // Radial inward-outward gentle drift
      let currentR = p.baseR * this.pulseFactor;
      if (this.state === 'speaking') {
        currentR += Math.sin(p.theta * 3 + this.time * 8) * 8 * this.audioWave;
      }

      const x = cx + currentR * Math.cos(p.theta);
      const y = cy + currentR * Math.sin(p.theta);

      // Color selection with luminous glow
      let fillStyle = 'rgba(0, 240, 255, 0.8)';
      if (p.colorType === 'white') {
        fillStyle = `rgba(255, 255, 255, ${p.alpha})`;
      } else if (p.colorType === 'azure') {
        fillStyle = `rgba(0, 160, 255, ${p.alpha * 0.8})`;
      } else {
        if (this.state === 'thinking') {
          fillStyle = `rgba(255, 185, 45, ${p.alpha})`;
        } else if (this.state === 'listening') {
          fillStyle = `rgba(0, 255, 210, ${p.alpha})`;
        } else {
          fillStyle = `rgba(0, 235, 255, ${p.alpha})`;
        }
      }

      ctx.fillStyle = fillStyle;
      ctx.beginPath();
      ctx.arc(x, y, p.size, 0, Math.PI * 2);
      ctx.fill();

      // Subtle motion tail on faster inner particles
      if (p.r < 80) {
        const tailX = cx + currentR * Math.cos(p.theta - p.speed * 2.2);
        const tailY = cy + currentR * Math.sin(p.theta - p.speed * 2.2);
        ctx.strokeStyle = fillStyle;
        ctx.lineWidth = p.size * 0.7;
        ctx.beginPath();
        ctx.moveTo(tailX, tailY);
        ctx.lineTo(x, y);
        ctx.stroke();
      }
    }
  }

  drawCoreAccretionDisk() {
    const ctx = this.ctx;
    const cx = this.cx;
    const cy = this.cy;
    const t = this.time;

    // Central dark void with blinding event horizon ring
    const voidRadius = (16 + Math.sin(t * 3) * 2) * (this.state === 'thinking' ? 0.85 : 1.0);
    const ringRadius = voidRadius + 4;

    // Glowing intense accretion rim
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(-t * 0.4);

    let rimColor = 'rgba(0, 255, 255, 0.9)';
    if (this.state === 'thinking') rimColor = 'rgba(255, 190, 50, 0.95)';
    else if (this.state === 'listening') rimColor = 'rgba(50, 255, 220, 0.95)';

    const rimGrad = ctx.createRadialGradient(0, 0, voidRadius * 0.8, 0, 0, ringRadius * 2);
    rimGrad.addColorStop(0, 'rgba(2, 6, 18, 0.9)');
    rimGrad.addColorStop(0.35, rimColor);
    rimGrad.addColorStop(0.7, 'rgba(0, 180, 255, 0.5)');
    rimGrad.addColorStop(1, 'transparent');

    ctx.fillStyle = rimGrad;
    ctx.beginPath();
    ctx.arc(0, 0, ringRadius * 2.2, 0, Math.PI * 2);
    ctx.fill();

    // Central pitch black iris / void
    ctx.fillStyle = '#020612';
    ctx.beginPath();
    ctx.arc(0, 0, voidRadius, 0, Math.PI * 2);
    ctx.fill();

    // Singularity center point spark
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(0, 0, 2.2 + Math.sin(t * 7) * 0.8, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();
  }

  drawDustSparkles() {
    const ctx = this.ctx;
    const cx = this.cx;
    const cy = this.cy;
    const t = this.time;

    for (let d of this.dustParticles) {
      d.angle += d.speed;
      const x = cx + d.r * Math.cos(d.angle);
      const y = cy + d.r * Math.sin(d.angle);
      const alpha = d.alpha * (0.6 + 0.4 * Math.sin(t * 4 + d.r));

      ctx.fillStyle = `rgba(180, 245, 255, ${alpha})`;
      ctx.beginPath();
      ctx.arc(x, y, d.size, 0, Math.PI * 2);
      ctx.fill();
    }
  }
}

window.JarvisVortexCore = JarvisVortexCore;
