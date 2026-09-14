/**
 * Career Learning Vault — Activity-Gated Focus Timer
 * Tracks active learning time with intelligent idle detection (2 min auto-pause),
 * local persistence, and background SQLite synchronization.
 */

class FocusTracker {
  constructor() {
    this.targetSeconds = 7200; // 2 Hours
    this.todaySeconds = 0;
    this.unsavedActiveSeconds = 0;
    this.isActive = true;
    this.lastActivityTime = Date.now();
    this.idleThresholdMs = 120 * 1000; // 2 minutes

    this.timerDisplayEl = document.getElementById('timer-digits');
    this.progressBarEl = document.getElementById('timer-progress-bar');
    this.statusBadgeEl = document.getElementById('timer-status-badge');
    this.pctDisplayEl = document.getElementById('timer-percentage');

    this.initEventListeners();
    this.loadInitialState();
    this.startHeartbeat();
  }

  initEventListeners() {
    const recordActivity = () => {
      this.lastActivityTime = Date.now();
      if (!this.isActive) {
        this.isActive = true;
        this.renderStatus();
      }
    };

    const events = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'scroll', 'click'];
    events.forEach(ev => window.addEventListener(ev, recordActivity, { passive: true }));

    // Send unsaved progress before page unloads
    window.addEventListener('beforeunload', () => {
      if (this.unsavedActiveSeconds > 0) {
        navigator.sendBeacon('/api/timer/sync', JSON.stringify({
          elapsed_seconds: this.unsavedActiveSeconds,
          is_active: true
        }));
      }
    });
  }

  async loadInitialState() {
    const todayKey = 'vault_timer_' + new Date().toISOString().slice(0, 10);
    const localSaved = parseInt(localStorage.getItem(todayKey) || '0', 10);

    try {
      const res = await fetch('/api/timer');
      if (res.ok) {
        const data = await res.json();
        this.targetSeconds = data.target_seconds || 7200;
        // Use greater of server or local to prevent losing seconds during reconnects
        this.todaySeconds = Math.max(data.seconds_active || 0, localSaved);
      } else {
        this.todaySeconds = localSaved;
      }
    } catch (err) {
      console.warn('Could not reach timer API, using local storage cache:', err);
      this.todaySeconds = localSaved;
    }

    this.updateDisplay();
    this.renderStatus();
  }

  startHeartbeat() {
    // 1-second local tick
    setInterval(() => {
      const idleElapsed = Date.now() - this.lastActivityTime;
      if (idleElapsed > this.idleThresholdMs) {
        if (this.isActive) {
          this.isActive = false;
          this.renderStatus();
        }
      } else {
        if (!this.isActive) {
          this.isActive = true;
          this.renderStatus();
        }
        this.todaySeconds += 1;
        this.unsavedActiveSeconds += 1;
        
        // Cache to localStorage
        const todayKey = 'vault_timer_' + new Date().toISOString().slice(0, 10);
        localStorage.setItem(todayKey, this.todaySeconds.toString());
        
        this.updateDisplay();
      }
    }, 1000);

    // 30-second server sync interval
    setInterval(() => {
      this.syncToServer();
    }, 30000);
  }

  async syncToServer() {
    if (this.unsavedActiveSeconds <= 0) return;
    const toSync = this.unsavedActiveSeconds;

    try {
      const res = await fetch('/api/timer/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          elapsed_seconds: toSync,
          is_active: true
        })
      });

      if (res.ok) {
        const data = await res.json();
        this.unsavedActiveSeconds = Math.max(0, this.unsavedActiveSeconds - toSync);
        if (data.seconds_active) {
          this.todaySeconds = Math.max(this.todaySeconds, data.seconds_active);
          this.updateDisplay();
        }
      }
    } catch (e) {
      console.warn('Background timer sync deferred, will retry next interval:', e);
    }
  }

  formatTime(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    const pad = (n) => n.toString().padStart(2, '0');
    return `${pad(h)}:${pad(m)}:${pad(s)}`;
  }

  updateDisplay() {
    if (this.timerDisplayEl) {
      this.timerDisplayEl.textContent = `${this.formatTime(this.todaySeconds)} / 02:00:00`;
    }
    const pct = Math.min(100, Math.round((this.todaySeconds / this.targetSeconds) * 1000) / 10);
    if (this.progressBarEl) {
      this.progressBarEl.style.width = `${pct}%`;
    }
    if (this.pctDisplayEl) {
      this.pctDisplayEl.textContent = `${pct}%`;
    }
  }

  renderStatus() {
    if (!this.statusBadgeEl) return;
    if (this.isActive) {
      this.statusBadgeEl.className = 'timer-badge-active';
      this.statusBadgeEl.innerHTML = '<span class="pulse-dot"></span> <span>ACTIVE</span>';
    } else {
      this.statusBadgeEl.className = 'timer-badge-idle';
      this.statusBadgeEl.innerHTML = '<span class="pulse-dot" style="background: var(--amber-warning);"></span> <span>IDLE (PAUSED)</span>';
    }
  }
}

// Instantiate on DOM load
window.addEventListener('DOMContentLoaded', () => {
  window.vaultTimer = new FocusTracker();
});
