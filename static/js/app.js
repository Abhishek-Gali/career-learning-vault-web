/**
 * Career Learning Vault — Full-Stack Cloud Web Hub
 * Architecture & Engineering by Abhishek Gali
 * Powered by Refero Design & Watermelon UI System
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
    
    // Interview Quiz Engine State
    interviewTracks: {},
    selectedTrack: 'cybersecurity',
    selectedSet: 'domain1_security_principles',
    quizQuestions: [],
    currentQuizIdx: 0,
    selectedQuizOption: null,
    quizSubmitted: false,
    quizStats: { correct: 0, incorrect: 0 },

    // Cron Keep-Alive Telemetry
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
      btn.addEventListener('click', () => {
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

  // ── Platforms & Challenges (Coding Sandbox) ────────────────────────────────
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

    let totalAll = this.state.platforms.reduce((acc, p) => acc + p.count, 0);
    let html = `
      <button class="platform-pill ${this.state.selectedPlatform === 'all' ? 'active' : ''}" data-plat="all">
        <span>🌐 All Platforms</span>
        <span class="pill-counter">${totalAll}</span>
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
      countBadge.textContent = `${this.state.challenges.length} Available`;
    }

    if (!listEl) return;

    if (this.state.challenges.length === 0) {
      listEl.innerHTML = `
        <div class="p-8 text-center text-slate-400">
          <p class="text-sm font-medium">No challenges matching filter.</p>
          <button class="mt-3 text-xs text-emerald-400 underline" onclick="App.resetFilters()">Clear Filters</button>
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
              <span class="text-[10px] px-2 py-0.5 rounded-full ${diffClass} font-semibold">${ch.difficulty}</span>
              <span class="text-[11px] text-slate-400 truncate">${ch.platform}</span>
            </div>
            <h4 class="text-xs md:text-sm font-semibold text-white truncate">${ch.title}</h4>
          </div>
          <div class="text-right flex flex-col items-end">
            <span class="text-[11px] text-slate-500 font-mono">${ch.visible_tests_count + ch.hidden_tests_count} Tests</span>
            <span class="text-[10px] text-emerald-400/80 font-mono">Python 3</span>
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

  resetFilters() {
    this.state.selectedPlatform = 'all';
    this.state.selectedDifficulty = 'All';
    this.state.searchQuery = '';
    const searchInput = document.getElementById('search-input');
    if (searchInput) searchInput.value = '';
    document.querySelectorAll('.diff-pill').forEach(p => p.classList.toggle('active', p.dataset.diff === 'All'));
    this.renderPlatformPills();
    this.loadChallenges();
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
      this.renderChallengeList();
    } catch (e) {
      console.error('Failed to fetch challenge detail:', e);
    }
  },

  renderChallengeDetail() {
    const ch = this.state.activeChallenge;
    if (!ch) return;

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

    document.getElementById('ch-description').innerHTML = this.formatMarkdown(ch.description);
    
    const constEl = document.getElementById('ch-constraints');
    if (constEl) {
      if (ch.constraints) {
        constEl.innerHTML = `<div class="mt-3 p-3 rounded-lg bg-slate-900/80 border border-slate-800 text-xs text-slate-300 font-mono"><strong class="text-emerald-400">Constraints:</strong><br>${ch.constraints}</div>`;
      } else {
        constEl.innerHTML = '';
      }
    }

    const editor = document.getElementById('code-editor');
    if (editor) {
      editor.value = this.state.editorContent;
    }

    const resultsContainer = document.getElementById('results-container');
    if (resultsContainer) {
      resultsContainer.innerHTML = `
        <div class="text-slate-500 text-xs font-mono py-4 text-center">
          Click "Run Test Suite" to execute your solution against ${ch.visible_tests.length + ch.hidden_tests_count} test cases.
        </div>
      `;
    }
  },

  formatMarkdown(text) {
    if (!text) return '';
    return text
      .replace(/### (.*?)\n/g, '<h3 class="text-sm font-bold text-white mt-3 mb-1">$1</h3>')
      .replace(/## (.*?)\n/g, '<h2 class="text-base font-bold text-white mt-4 mb-2">$1</h2>')
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
      runBtn.innerHTML = '<span class="animate-spin inline-block mr-1">⚙</span> Running...';
      runBtn.disabled = true;
    }

    if (resultsContainer) {
      resultsContainer.innerHTML = `
        <div class="flex items-center justify-center gap-3 py-6 text-emerald-400 text-xs font-mono">
          <span class="animate-spin">⚙</span> Executing code inside isolated subprocess sandbox (3.0s timeout)...
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

      if (report.status === 'PASS' && typeof confetti === 'function') {
        confetti({
          particleCount: 120,
          spread: 80,
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
      <div class="flex items-center justify-between p-3 rounded-lg bg-slate-900/90 border border-slate-800 mb-3">
        <div class="flex items-center gap-2">
          <span class="text-sm font-bold ${statusColor}">● ${report.status}</span>
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
              <div class="bg-black/40 p-1.5 rounded">
                <span class="text-slate-400">Input:</span> ${JSON.stringify(r.input)}
              </div>
              <div class="bg-black/40 p-1.5 rounded">
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
      alert('Solution reference not available for this challenge.');
      return;
    }
    if (confirm('Reveal verified solution in the editor?')) {
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

  // ── Technical Interviews System (ROBUST DICT/ARRAY PARSING) ──────────────
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

    const tracks = this.state.interviewTracks;
    const trackIcons = {
      cybersecurity: '🛡️',
      data_science: '📊',
      machine_learning: '🧠',
      dsa: '⚡'
    };

    let html = '';
    Object.keys(tracks).forEach(key => {
      const track = tracks[key];
      const isSelected = this.state.selectedTrack === key;
      const icon = trackIcons[key] || '🎯';
      html += `
        <button class="px-4 py-2.5 rounded-xl text-xs md:text-sm font-semibold transition-all flex items-center gap-2 ${
          isSelected 
            ? 'bg-gradient-to-r from-emerald-500/25 to-teal-500/25 text-emerald-300 border border-emerald-500/50 shadow-lg shadow-emerald-500/10' 
            : 'bg-slate-900/60 text-slate-400 border border-slate-800 hover:text-white hover:border-slate-700'
        }" data-track="${key}">
          <span>${icon}</span>
          <span>${track.title}</span>
        </button>
      `;
    });
    trackContainer.innerHTML = html;

    trackContainer.querySelectorAll('button').forEach(btn => {
      btn.addEventListener('click', () => {
        this.state.selectedTrack = btn.dataset.track;
        this.state.selectedSet = ''; // Reset set so first set of new track is chosen
        this.state.quizStats = { correct: 0, incorrect: 0 };
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
      setContainer.innerHTML = '<span class="text-xs text-slate-400">No question sets available for this track.</span>';
      return;
    }

    // Auto-select first set if none selected or invalid
    const setIds = trackObj.sets.map(s => s.id);
    if (!setIds.includes(this.state.selectedSet)) {
      this.state.selectedSet = trackObj.sets[0].id;
    }

    let html = '';
    trackObj.sets.forEach(set => {
      const isSelected = this.state.selectedSet === set.id;
      html += `
        <button class="px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all flex items-center gap-1.5 ${
          isSelected 
            ? 'bg-gradient-to-r from-rose-500/25 to-coral-500/25 text-rose-300 border border-rose-500/50 shadow-md shadow-rose-500/10' 
            : 'bg-slate-900/80 text-slate-400 border border-slate-800 hover:text-white hover:border-slate-700'
        }" data-set="${set.id}">
          <span>${set.name}</span>
          <span class="px-1.5 py-0.2 text-[10px] rounded-full bg-slate-800 text-slate-300 font-mono">${set.question_count} Qs</span>
        </button>
      `;
    });

    setContainer.innerHTML = html;

    setContainer.querySelectorAll('button').forEach(btn => {
      btn.addEventListener('click', () => {
        this.state.selectedSet = btn.dataset.set;
        this.state.quizStats = { correct: 0, incorrect: 0 };
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
      container.innerHTML = '<div class="p-8 text-center text-slate-400">Loading interview question set...</div>';
      return;
    }

    const q = qList[this.state.currentQuizIdx];
    const qNum = this.state.currentQuizIdx + 1;
    const totalQ = qList.length;

    // Resolve Question Prompt across formats
    const questionPrompt = q.stem || q.question || q.prompt || 'Question prompt not specified.';
    const correctKey = (q.correct_key || q.answer || q.correct || '').toString().trim().toUpperCase();

    // Parse options safely from Dictionary or Array
    let optionsList = [];
    if (typeof q.options === 'object' && q.options !== null && !Array.isArray(q.options)) {
      optionsList = Object.keys(q.options).sort().map(k => ({
        key: k.toUpperCase(),
        text: q.options[k]
      }));
    } else if (Array.isArray(q.options)) {
      optionsList = q.options.map((opt, idx) => ({
        key: String.fromCharCode(65 + idx),
        text: typeof opt === 'object' ? (opt.text || opt.value || JSON.stringify(opt)) : opt
      }));
    }

    let optionsHtml = '';
    optionsList.forEach(opt => {
      const isChosen = this.state.selectedQuizOption === opt.key;
      let cardStyle = 'bg-slate-900/60 border-slate-800/80 hover:border-slate-700 hover:bg-slate-800/50';
      let badgeStyle = 'bg-slate-800 text-slate-300 border border-slate-700';

      if (this.state.quizSubmitted) {
        const isCorrect = (opt.key === correctKey);
        if (isCorrect) {
          cardStyle = 'bg-emerald-950/40 border-emerald-500/80 text-emerald-200 shadow-lg shadow-emerald-950/30';
          badgeStyle = 'bg-emerald-500 text-black font-black';
        } else if (isChosen) {
          cardStyle = 'bg-rose-950/40 border-rose-500/80 text-rose-200 shadow-lg shadow-rose-950/30';
          badgeStyle = 'bg-rose-500 text-white font-black';
        } else {
          cardStyle = 'bg-slate-900/40 border-slate-800/40 opacity-50';
        }
      } else if (isChosen) {
        cardStyle = 'bg-emerald-500/15 border-emerald-500 text-white shadow-md shadow-emerald-500/10';
        badgeStyle = 'bg-emerald-500 text-black font-black';
      }

      optionsHtml += `
        <div class="p-4 rounded-xl border transition-all cursor-pointer flex items-start gap-3.5 ${cardStyle}" onclick="App.selectQuizOption('${opt.key}')">
          <span class="w-7 h-7 rounded-lg flex-shrink-0 flex items-center justify-center text-xs font-bold ${badgeStyle}">
            ${opt.key}
          </span>
          <span class="text-sm leading-relaxed flex-1">${opt.text}</span>
        </div>
      `;
    });

    // Rationale breakdown container
    let rationaleHtml = '';
    if (this.state.quizSubmitted) {
      const userGotCorrect = (this.state.selectedQuizOption === correctKey);
      
      rationaleHtml = `
        <div class="mt-5 p-5 rounded-xl ${userGotCorrect ? 'bg-emerald-950/30 border-emerald-500/40' : 'bg-rose-950/30 border-rose-500/40'} border space-y-3">
          <div class="flex items-center gap-2">
            <span class="text-base">${userGotCorrect ? '🎉' : '💡'}</span>
            <span class="font-bold text-sm ${userGotCorrect ? 'text-emerald-400' : 'text-rose-400'}">
              ${userGotCorrect ? 'Correct Answer!' : `Incorrect — The correct answer is Option ${correctKey}`}
            </span>
          </div>
      `;

      if (q.rationales && typeof q.rationales === 'object') {
        if (q.rationales.correct) {
          rationaleHtml += `
            <div class="p-3 rounded-lg bg-black/40 text-xs text-emerald-300 font-medium leading-relaxed">
              <strong class="text-white">Core Principle:</strong> ${q.rationales.correct}
            </div>
          `;
        }
        rationaleHtml += '<div class="space-y-1.5 pt-2 text-xs text-slate-300">';
        optionsList.forEach(opt => {
          const rText = q.rationales[opt.key];
          if (rText) {
            const isOptCorrect = (opt.key === correctKey);
            rationaleHtml += `
              <div class="p-2 rounded bg-black/20">
                <strong class="${isOptCorrect ? 'text-emerald-400' : 'text-slate-400'}">Option ${opt.key}:</strong> 
                <span class="text-slate-300">${rText}</span>
              </div>
            `;
          }
        });
        rationaleHtml += '</div>';
      } else if (q.explanation) {
        rationaleHtml += `
          <div class="p-3 rounded-lg bg-black/40 text-xs text-slate-300 leading-relaxed">
            <strong class="text-emerald-400">Explanation:</strong> ${q.explanation}
          </div>
        `;
      }

      rationaleHtml += '</div>';
    }

    // Header metadata
    const topicText = q.domain_name || q.sub_objective || q.topic || q.level_name || 'Interview Drill';
    const cogLevel = q.cognitive_level || (q.difficulty ? q.difficulty.toUpperCase() : 'STANDARD');

    const totalAnswered = this.state.quizStats.correct + this.state.quizStats.incorrect;
    const accuracy = totalAnswered > 0 ? Math.round((this.state.quizStats.correct / totalAnswered) * 100) : 0;

    container.innerHTML = `
      <div class="space-y-4">
        <!-- Quiz Meta Bar -->
        <div class="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-800">
          <div class="flex items-center gap-2">
            <span class="text-xs font-mono text-emerald-400 font-bold tracking-wider uppercase">QUESTION ${qNum} OF ${totalQ}</span>
            <span class="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">${cogLevel}</span>
          </div>
          <div class="flex items-center gap-3 text-xs">
            <span class="text-slate-400 font-mono truncate max-w-xs">${topicText}</span>
            <span class="px-2.5 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-mono font-bold">
              Score: ${this.state.quizStats.correct}/${totalAnswered} (${accuracy}%)
            </span>
          </div>
        </div>

        <!-- Question Prompt -->
        <h3 class="text-base md:text-lg font-semibold text-slate-100 leading-relaxed pt-1">
          ${questionPrompt}
        </h3>

        <!-- Interactive Options -->
        <div class="space-y-2.5 pt-2">
          ${optionsHtml}
        </div>

        <!-- Pedagogical Rationale (Appears on submit) -->
        ${rationaleHtml}

        <!-- Action Footer Controls -->
        <div class="flex items-center justify-between pt-5 border-t border-slate-800 mt-6">
          <button class="btn-secondary text-xs" onclick="App.prevQuizQuestion()" ${qNum === 1 ? 'disabled' : ''}>
            ← Previous
          </button>
          
          <div class="flex items-center gap-2">
            ${!this.state.quizSubmitted ? `
              <button class="btn-primary text-xs px-5 py-2" onclick="App.submitQuizAnswer()">
                <span>Check Answer</span>
              </button>
            ` : `
              <button class="btn-coral text-xs px-5 py-2" onclick="App.nextQuizQuestion()">
                <span>${qNum < totalQ ? 'Next Question →' : 'Complete Set 🎉'}</span>
              </button>
            `}
          </div>
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
    const q = this.state.quizQuestions[this.state.currentQuizIdx];
    const correctKey = (q.correct_key || q.answer || q.correct || '').toString().trim().toUpperCase();
    
    if (this.state.selectedQuizOption === correctKey) {
      this.state.quizStats.correct += 1;
    } else {
      this.state.quizStats.incorrect += 1;
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
      const accuracy = Math.round((this.state.quizStats.correct / this.state.quizQuestions.length) * 100);
      alert(`🎉 Set Completed! Your score: ${this.state.quizStats.correct}/${this.state.quizQuestions.length} (${accuracy}%)`);
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

  // ── 24/7 Keep-Alive & Cron Monitor ────────────────────────────────────────
  initCronMonitor() {
    this.refreshHealthData();
    setInterval(() => {
      if (this.state.activeTab === 'monitor') {
        this.refreshHealthData();
      }
    }, 20000);
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
      console.warn('Health ping deferred:', e);
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
  },

  copyHealthUrl() {
    const host = window.location.origin;
    const url = `${host}/api/health`;
    navigator.clipboard.writeText(url).then(() => {
      const btn = document.getElementById('btn-copy-health-url');
      if (btn) {
        btn.innerHTML = '<span>✓ Copied to Clipboard!</span>';
        setTimeout(() => {
          btn.innerHTML = '<span>📋 Copy URL for cron-job.org</span>';
        }, 2500);
      }
    });
  }
};

window.addEventListener('DOMContentLoaded', () => {
  App.init();

  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    let timeout = null;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        App.state.searchQuery = e.target.value;
        App.loadChallenges();
      }, 200);
    });
  }

  document.querySelectorAll('.diff-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.diff-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      App.state.selectedDifficulty = pill.dataset.diff;
      App.loadChallenges();
    });
  });

  const btnRun = document.getElementById('btn-run-code');
  if (btnRun) btnRun.addEventListener('click', () => App.runCode());

  const btnReset = document.getElementById('btn-reset-code');
  if (btnReset) btnReset.addEventListener('click', () => App.resetCode());

  const btnReveal = document.getElementById('btn-reveal-solution');
  if (btnReveal) btnReveal.addEventListener('click', () => App.revealSolution());
});
