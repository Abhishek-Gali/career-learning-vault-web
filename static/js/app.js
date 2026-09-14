/**
 * Career Learning Vault — SPA Application Controller
 * High-performance vanilla JS controller for Refero Design & Watermelon UI
 */

const App = {
  state: {
    activeTab: 'sandbox',
    platforms: [],
    selectedPlatform: 'all',
    selectedDifficulty: 'All',
    searchQuery: '',
    challenges: [],
    activeChallenge: null,
    editorContent: '',
    testResults: null,
    isRunning: false,
    
    // Interview Quiz State
    interviewTracks: {},
    selectedTrack: 'data_science',
    selectedSet: '',
    quizQuestions: [],
    currentQuizIdx: 0,
    selectedQuizOption: null,
    quizSubmitted: false,
    quizScore: 0,

    // Cron monitor
    healthData: null
  },

  async init() {
    this.bindGlobalNavigation();
    await this.loadPlatforms();
    await this.loadChallenges();
    await this.loadInterviewTracks();
    this.initCronMonitor();
    
    // Auto-select first challenge if available
    if (this.state.challenges.length > 0) {
      await this.selectChallenge(this.state.challenges[0].id);
    }
  },

  bindGlobalNavigation() {
    document.querySelectorAll('.nav-tab-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const tab = btn.dataset.tab;
        this.switchTab(tab);
      });
    });
  },

  switchTab(tabName) {
    this.state.activeTab = tabName;
    document.querySelectorAll('.nav-tab-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    ['sandbox-view', 'interviews-view', 'roadmap-view', 'monitor-view'].forEach(viewId => {
      const el = document.getElementById(viewId);
      if (el) el.classList.add('hidden');
    });

    const target = document.getElementById(`${tabName}-view`);
    if (target) {
      target.classList.remove('hidden');
    }

    if (tabName === 'monitor') {
      this.refreshHealthData();
    }
  },

  // ── Platforms & Challenges ────────────────────────────────────────────────
  async loadPlatforms() {
    try {
      const res = await fetch('/api/platforms');
      const data = await res.json();
      this.state.platforms = data.platforms || [];
      this.renderPlatformPills();
    } catch (e) {
      console.error('Failed to load platforms:', e);
    }
  },

  renderPlatformPills() {
    const container = document.getElementById('platform-pills');
    if (!container) return;

    let html = `
      <button class="platform-pill ${this.state.selectedPlatform === 'all' ? 'active' : ''}" data-plat="all">
        <span>All Platforms</span>
        <span class="pill-counter">${this.state.platforms.reduce((acc, p) => acc + p.count, 0)}</span>
      </button>
    `;

    this.state.platforms.forEach(p => {
      const isActive = this.state.selectedPlatform === p.id;
      html += `
        <button class="platform-pill ${isActive ? 'active' : ''}" data-plat="${p.id}">
          <span>${p.name}</span>
          <span class="pill-counter">${p.count}</span>
        </button>
      `;
    });

    container.innerHTML = html;

    container.querySelectorAll('.platform-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        this.state.selectedPlatform = pill.dataset.plat;
        this.renderPlatformPills();
        this.loadChallenges();
      });
    });
  },

  async loadChallenges() {
    const plat = this.state.selectedPlatform;
    const diff = this.state.selectedDifficulty;
    const q = encodeURIComponent(this.state.searchQuery || '');
    const url = `/api/challenges?platform=${plat}&difficulty=${diff}&search=${q}&limit=200`;

    try {
      const res = await fetch(url);
      const data = await res.json();
      this.state.challenges = data.challenges || [];
      this.renderChallengeList();
    } catch (e) {
      console.error('Failed to load challenges:', e);
    }
  },

  renderChallengeList() {
    const listEl = document.getElementById('challenge-list');
    const countBadge = document.getElementById('challenge-count-badge');
    if (countBadge) {
      countBadge.textContent = `${this.state.challenges.length} Found`;
    }

    if (!listEl) return;

    if (this.state.challenges.length === 0) {
      listEl.innerHTML = `
        <div class="p-8 text-center text-slate-400">
          <p class="text-sm">No matching challenges found.</p>
        </div>
      `;
      return;
    }

    let html = '';
    this.state.challenges.forEach(ch => {
      const isSelected = this.state.activeChallenge && this.state.activeChallenge.id === ch.id;
      const diffClass = ch.difficulty.toLowerCase() === 'easy' ? 'badge-easy' : 
                        ch.difficulty.toLowerCase() === 'medium' ? 'badge-medium' : 'badge-hard';
      
      html += `
        <div class="challenge-item ${isSelected ? 'active' : ''}" data-cid="${ch.id}">
          <div class="flex-1 min-w-0 pr-2">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-xs px-2 py-0.5 rounded-full ${diffClass} font-semibold">${ch.difficulty}</span>
              <span class="text-xs text-slate-400 truncate">${ch.platform}</span>
            </div>
            <h4 class="text-sm font-semibold text-white truncate">${ch.title}</h4>
          </div>
          <div class="text-right">
            <span class="text-xs text-slate-500 font-mono">${ch.visible_tests_count + ch.hidden_tests_count} Tests</span>
          </div>
        </div>
      `;
    });

    listEl.innerHTML = html;

    listEl.querySelectorAll('.challenge-item').forEach(item => {
      item.addEventListener('click', () => {
        this.selectChallenge(item.dataset.cid);
      });
    });
  },

  async selectChallenge(cid) {
    try {
      const res = await fetch(`/api/challenges/${cid}`);
      if (!res.ok) return;
      const ch = await res.json();
      this.state.activeChallenge = ch;
      this.state.editorContent = ch.initial_code;
      this.state.testResults = null;

      this.renderChallengeDetail();
      this.renderChallengeList(); // Updates active card highlight
    } catch (e) {
      console.error('Failed to fetch challenge detail:', e);
    }
  },

  renderChallengeDetail() {
    const ch = this.state.activeChallenge;
    if (!ch) return;

    // Header info
    document.getElementById('ch-title').textContent = ch.title;
    document.getElementById('ch-platform').textContent = ch.platform;
    document.getElementById('ch-category').textContent = ch.category;
    document.getElementById('ch-function').textContent = `def ${ch.function_name}()`;

    const diffBadge = document.getElementById('ch-difficulty');
    diffBadge.textContent = ch.difficulty;
    diffBadge.className = `text-xs px-2.5 py-0.5 rounded-full font-semibold ${
      ch.difficulty.toLowerCase() === 'easy' ? 'badge-easy' :
      ch.difficulty.toLowerCase() === 'medium' ? 'badge-medium' : 'badge-hard'
    }`;

    // Description text
    document.getElementById('ch-description').innerHTML = this.formatMarkdown(ch.description);
    
    // Constraints
    const constEl = document.getElementById('ch-constraints');
    if (constEl) {
      if (ch.constraints) {
        constEl.innerHTML = `<div class="mt-4 p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs text-slate-300 font-mono"><strong>Constraints:</strong><br>${ch.constraints}</div>`;
      } else {
        constEl.innerHTML = '';
      }
    }

    // Set Editor Content
    const editor = document.getElementById('code-editor');
    if (editor) {
      editor.value = this.state.editorContent;
    }

    // Reset results pane
    const resultsContainer = document.getElementById('results-container');
    if (resultsContainer) {
      resultsContainer.innerHTML = `
        <div class="text-slate-500 text-xs font-mono py-4 text-center">
          Click "Run Test Suite" to execute your Python solution against test cases.
        </div>
      `;
    }
  },

  formatMarkdown(text) {
    if (!text) return '';
    return text
      .replace(/### (.*?)\n/g, '<h3 class="text-base font-bold text-white mt-3 mb-1">$1</h3>')
      .replace(/## (.*?)\n/g, '<h2 class="text-lg font-bold text-white mt-4 mb-2">$1</h2>')
      .replace(/\*\*(.*?)\*\*/g, '<strong class="text-slate-200">$1</strong>')
      .replace(/`(.*?)`/g, '<code class="px-1.5 py-0.5 bg-slate-800 text-emerald-300 rounded font-mono text-xs">$1</code>')
      .replace(/\n/g, '<br>');
  },

  async runCode() {
    if (!this.state.activeChallenge || this.state.isRunning) return;

    const editor = document.getElementById('code-editor');
    const userCode = editor ? editor.value : this.state.editorContent;
    this.state.editorContent = userCode;

    const runBtn = document.getElementById('btn-run-code');
    const resultsContainer = document.getElementById('results-container');

    this.state.isRunning = true;
    if (runBtn) {
      runBtn.innerHTML = '<span class="animate-spin inline-block mr-2">⚙</span> Running Sandbox...';
      runBtn.disabled = true;
    }

    if (resultsContainer) {
      resultsContainer.innerHTML = `
        <div class="flex items-center justify-center gap-3 py-6 text-emerald-400 text-sm font-mono">
          <span class="animate-spin">⚙</span> Executing candidate code in isolated subprocess...
        </div>
      `;
    }

    try {
      const res = await fetch('/api/run-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          challenge_id: this.state.activeChallenge.id,
          code: userCode,
          run_hidden: true
        })
      });

      const report = await res.json();
      this.state.testResults = report;
      this.renderTestResults(report);

      // Trigger Confetti blast on PASS
      if (report.status === 'PASS' && typeof confetti === 'function') {
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 },
          colors: ['#10b981', '#34d399', '#f43f5e', '#fb7185', '#38bdf8']
        });
      }
    } catch (err) {
      if (resultsContainer) {
        resultsContainer.innerHTML = `
          <div class="test-card-fail">
            <span class="font-bold">Execution Error:</span> ${err.message}
          </div>
        `;
      }
    } finally {
      this.state.isRunning = false;
      if (runBtn) {
        runBtn.innerHTML = '<span>⚡</span> <span>Run Test Suite</span>';
        runBtn.disabled = false;
      }
    }
  },

  renderTestResults(report) {
    const container = document.getElementById('results-container');
    if (!container) return;

    const isPass = report.status === 'PASS';
    const statusColor = isPass ? 'text-emerald-400' : report.status === 'TIMEOUT' ? 'text-amber-400' : 'text-rose-400';

    let html = `
      <div class="flex items-center justify-between p-3 rounded-lg bg-slate-900/80 border border-slate-800 mb-3">
        <div class="flex items-center gap-2">
          <span class="text-base font-bold ${statusColor}">● ${report.status}</span>
          <span class="text-xs text-slate-400 font-mono">(${report.passed_count}/${report.total_count} Passed)</span>
        </div>
        <div class="text-xs font-mono text-slate-400">
          Runtime: <span class="text-white">${report.runtime_ms} ms</span>
        </div>
      </div>
    `;

    if (report.error_message) {
      html += `
        <div class="test-card-fail font-mono text-xs mb-3 whitespace-pre-wrap">
          ${report.error_message}
        </div>
      `;
    }

    if (report.results && report.results.length > 0) {
      html += '<div class="space-y-2">';
      report.results.forEach(r => {
        const passClass = r.passed ? 'test-card-pass' : 'test-card-fail';
        const badge = r.passed ? '<span class="text-emerald-400 font-bold">✓ PASS</span>' : '<span class="text-rose-400 font-bold">✗ FAIL</span>';
        
        html += `
          <div class="${passClass}">
            <div class="flex justify-between items-center text-xs font-semibold mb-1">
              <span>Test Case #${r.index} ${badge}</span>
              <span class="text-slate-400 font-mono">${r.runtime_ms} ms</span>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs font-mono mt-1">
              <div class="bg-black/30 p-1.5 rounded">
                <span class="text-slate-400">Input:</span> ${JSON.stringify(r.input)}
              </div>
              <div class="bg-black/30 p-1.5 rounded">
                <span class="text-slate-400">Expected:</span> <span class="text-emerald-300">${JSON.stringify(r.expected)}</span>
              </div>
            </div>
            ${!r.passed ? `
              <div class="mt-1.5 p-1.5 rounded bg-rose-950/40 border border-rose-900 text-xs font-mono">
                <span class="text-rose-300">Got:</span> <span class="text-white">${JSON.stringify(r.got)}</span>
              </div>
            ` : ''}
          </div>
        `;
      });
      html += '</div>';
    }

    container.innerHTML = html;
  },

  revealSolution() {
    if (!this.state.activeChallenge) return;
    const sol = this.state.activeChallenge.solution_code;
    if (!sol) {
      alert('Solution not available for this challenge.');
      return;
    }
    if (confirm('Reveal verified reference solution in editor?')) {
      const editor = document.getElementById('code-editor');
      if (editor) {
        editor.value = sol;
        this.state.editorContent = sol;
      }
    }
  },

  resetCode() {
    if (!this.state.activeChallenge) return;
    const starter = this.state.activeChallenge.initial_code;
    const editor = document.getElementById('code-editor');
    if (editor) {
      editor.value = starter;
      this.state.editorContent = starter;
    }
  },

  // ── Technical Interviews System ──────────────────────────────────────────
  async loadInterviewTracks() {
    try {
      const res = await fetch('/api/interviews');
      this.state.interviewTracks = await res.json();
      this.renderInterviewTrackSelectors();
    } catch (e) {
      console.error('Failed to load interview tracks:', e);
    }
  },

  renderInterviewTrackSelectors() {
    const trackContainer = document.getElementById('interview-track-selector');
    if (!trackContainer) return;

    let html = '';
    const tracks = this.state.interviewTracks;
    Object.keys(tracks).forEach(key => {
      const track = tracks[key];
      const isSelected = this.state.selectedTrack === key;
      html += `
        <button class="px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
          isSelected ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' : 'bg-slate-800/40 text-slate-400 border border-transparent hover:text-white'
        }" data-track="${key}">
          ${track.title}
        </button>
      `;
    });
    trackContainer.innerHTML = html;

    trackContainer.querySelectorAll('button').forEach(btn => {
      btn.addEventListener('click', () => {
        this.state.selectedTrack = btn.dataset.track;
        this.renderInterviewTrackSelectors();
        this.renderInterviewSetPills();
      });
    });

    this.renderInterviewSetPills();
  },

  renderInterviewSetPills() {
    const setContainer = document.getElementById('interview-set-selector');
    if (!setContainer) return;

    const trackObj = this.state.interviewTracks[this.state.selectedTrack];
    if (!trackObj || !trackObj.sets || trackObj.sets.length === 0) {
      setContainer.innerHTML = '<span class="text-xs text-slate-400">No question sets loaded.</span>';
      return;
    }

    if (!this.state.selectedSet && trackObj.sets.length > 0) {
      this.state.selectedSet = trackObj.sets[0].id;
    }

    let html = '';
    trackObj.sets.forEach(set => {
      const isSelected = this.state.selectedSet === set.id;
      html += `
        <button class="px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${
          isSelected ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' : 'bg-slate-800/60 text-slate-400 border border-slate-700/50 hover:text-white'
        }" data-set="${set.id}">
          ${set.name} (${set.question_count} Qs)
        </button>
      `;
    });

    setContainer.innerHTML = html;

    setContainer.querySelectorAll('button').forEach(btn => {
      btn.addEventListener('click', () => {
        this.state.selectedSet = btn.dataset.set;
        this.renderInterviewSetPills();
        this.loadQuizQuestions();
      });
    });

    this.loadQuizQuestions();
  },

  async loadQuizQuestions() {
    const track = this.state.selectedTrack;
    const setId = this.state.selectedSet;
    if (!track || !setId) return;

    try {
      const res = await fetch(`/api/interviews/${track}/${setId}`);
      if (!res.ok) return;
      const data = await res.json();
      this.state.quizQuestions = data.questions || [];
      this.state.currentQuizIdx = 0;
      this.state.selectedQuizOption = null;
      this.state.quizSubmitted = false;
      this.renderQuizQuestion();
    } catch (e) {
      console.error('Failed to load quiz questions:', e);
    }
  },

  renderQuizQuestion() {
    const container = document.getElementById('quiz-question-container');
    if (!container) return;

    const qList = this.state.quizQuestions;
    if (!qList || qList.length === 0) {
      container.innerHTML = '<div class="p-8 text-center text-slate-400">No questions available in this set.</div>';
      return;
    }

    const q = qList[this.state.currentQuizIdx];
    const qNum = this.state.currentQuizIdx + 1;
    const totalQ = qList.length;

    let optionsHtml = '';
    const options = q.options || [];

    options.forEach((opt, idx) => {
      let optKey = String.fromCharCode(65 + idx); // A, B, C, D
      let optText = opt;
      if (typeof opt === 'object') {
        optKey = opt.key || optKey;
        optText = opt.text || opt.value || JSON.stringify(opt);
      }

      const isChosen = this.state.selectedQuizOption === optKey;
      let extraClass = 'bg-slate-900/60 border-slate-800 hover:border-slate-700';

      if (this.state.quizSubmitted) {
        const isCorrectOpt = (q.correct_key === optKey || q.answer === optKey || q.correct === optKey);
        if (isCorrectOpt) {
          extraClass = 'bg-emerald-950/40 border-emerald-500/60 text-emerald-200';
        } else if (isChosen) {
          extraClass = 'bg-rose-950/40 border-rose-500/60 text-rose-200';
        }
      } else if (isChosen) {
        extraClass = 'bg-emerald-500/15 border-emerald-500 text-white';
      }

      optionsHtml += `
        <div class="p-3.5 rounded-lg border transition-all cursor-pointer flex items-center gap-3 ${extraClass}" onclick="App.selectQuizOption('${optKey}')">
          <span class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${isChosen ? 'bg-emerald-500 text-black' : 'bg-slate-800 text-slate-300'}">
            ${optKey}
          </span>
          <span class="text-sm flex-1">${optText}</span>
        </div>
      `;
    });

    let rationaleHtml = '';
    if (this.state.quizSubmitted && q.rationales) {
      rationaleHtml = `
        <div class="mt-4 p-4 rounded-xl bg-slate-900/90 border border-slate-800 text-xs leading-relaxed space-y-2">
          <div class="text-emerald-400 font-bold text-sm">Pedagogical Rationale:</div>
          ${Object.entries(q.rationales).map(([k, r]) => `
            <div><strong class="text-slate-300">Option ${k}:</strong> <span class="text-slate-400">${r}</span></div>
          `).join('')}
        </div>
      `;
    } else if (this.state.quizSubmitted && q.explanation) {
      rationaleHtml = `
        <div class="mt-4 p-4 rounded-xl bg-slate-900/90 border border-slate-800 text-xs leading-relaxed">
          <div class="text-emerald-400 font-bold text-sm mb-1">Explanation:</div>
          <p class="text-slate-300">${q.explanation}</p>
        </div>
      `;
    }

    container.innerHTML = `
      <div class="flex justify-between items-center mb-4">
        <span class="text-xs font-mono text-emerald-400 font-semibold uppercase">Question ${qNum} of ${totalQ}</span>
        <span class="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">${q.domain || q.topic || 'Interview Drill'}</span>
      </div>
      <h3 class="text-base md:text-lg font-semibold text-white mb-5 leading-snug">${q.question || q.prompt}</h3>
      <div class="space-y-3 mb-6">
        ${optionsHtml}
      </div>
      ${rationaleHtml}
      <div class="flex justify-between items-center mt-6 pt-4 border-t border-slate-800">
        <button class="btn-secondary text-xs" onclick="App.prevQuizQuestion()" ${this.state.currentQuizIdx === 0 ? 'disabled' : ''}>
          ← Previous
        </button>
        <div>
          ${!this.state.quizSubmitted ? `
            <button class="btn-primary text-xs" onclick="App.submitQuizAnswer()">
              Check Answer
            </button>
          ` : `
            <button class="btn-coral text-xs" onclick="App.nextQuizQuestion()">
              ${this.state.currentQuizIdx + 1 < totalQ ? 'Next Question →' : 'Complete Quiz 🎉'}
            </button>
          `}
        </div>
      </div>
    `;
  },

  selectQuizOption(key) {
    if (this.state.quizSubmitted) return;
    this.state.selectedQuizOption = key;
    this.renderQuizQuestion();
  },

  submitQuizAnswer() {
    if (!this.state.selectedQuizOption) {
      alert('Please select an option before checking.');
      return;
    }
    this.state.quizSubmitted = true;
    this.renderQuizQuestion();
  },

  nextQuizQuestion() {
    if (this.state.currentQuizIdx + 1 < this.state.quizQuestions.length) {
      this.state.currentQuizIdx += 1;
      this.state.selectedQuizOption = null;
      this.state.quizSubmitted = false;
      this.renderQuizQuestion();
    } else {
      alert('Quiz set completed! Great study session.');
    }
  },

  prevQuizQuestion() {
    if (this.state.currentQuizIdx > 0) {
      this.state.currentQuizIdx -= 1;
      this.state.selectedQuizOption = null;
      this.state.quizSubmitted = false;
      this.renderQuizQuestion();
    }
  },

  // ── 24/7 Keep-Alive & Cron Monitor ──────────────────────────────────────
  initCronMonitor() {
    this.refreshHealthData();
    // Poll health every 30s when active
    setInterval(() => {
      if (this.state.activeTab === 'monitor') {
        this.refreshHealthData();
      }
    }, 30000);
  },

  async refreshHealthData() {
    const t0 = performance.now();
    try {
      const res = await fetch('/api/health');
      const t1 = performance.now();
      const latencyMs = Math.round(t1 - t0);
      const data = await res.json();
      this.state.healthData = data;
      this.renderCronMonitor(data, latencyMs);
    } catch (e) {
      console.warn('Health ping failed:', e);
    }
  },

  renderCronMonitor(data, latencyMs) {
    const elUptime = document.getElementById('mon-uptime');
    const elPings = document.getElementById('mon-pings');
    const elLatency = document.getElementById('mon-latency');
    const elCronStatus = document.getElementById('mon-cron-status');
    const elTimestamp = document.getElementById('mon-timestamp');

    if (elUptime) elUptime.textContent = `${Math.floor(data.uptime_seconds / 60)}m ${Math.floor(data.uptime_seconds % 60)}s`;
    if (elPings) elPings.textContent = data.ping_count;
    if (elLatency) elLatency.textContent = `${latencyMs} ms`;
    if (elCronStatus) elCronStatus.textContent = data.cron_status;
    if (elTimestamp) elTimestamp.textContent = new Date(data.timestamp_utc).toLocaleTimeString();
  }
};

window.addEventListener('DOMContentLoaded', () => {
  App.init();

  // Search input binding
  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    let timeout = null;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        App.state.searchQuery = e.target.value;
        App.loadChallenges();
      }, 250);
    });
  }

  // Difficulty filter pills
  document.querySelectorAll('.diff-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.diff-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      App.state.selectedDifficulty = pill.dataset.diff;
      App.loadChallenges();
    });
  });

  // Action buttons
  const btnRun = document.getElementById('btn-run-code');
  if (btnRun) btnRun.addEventListener('click', () => App.runCode());

  const btnReset = document.getElementById('btn-reset-code');
  if (btnReset) btnReset.addEventListener('click', () => App.resetCode());

  const btnReveal = document.getElementById('btn-reveal-solution');
  if (btnReveal) btnReveal.addEventListener('click', () => App.revealSolution());
});
