/**
 * Career Learning Vault — Cloud Command Hub
 * Architecture & Engineering by Abhishek Gali
 * Powered by Refero Design & Watermelon UI System
 */

const App = {
  state: {
    activeView: 'datascience',
    platforms: [],
    selectedPlatform: 'all',
    selectedDifficulty: 'All',
    selectedStatus: 'all', // 'all' | 'unsolved' | 'solved'
    searchQuery: '',
    challenges: [],
    activeChallenge: null,
    editorContent: '',
    testResults: null,
    isRunning: false,
    solvedChallenges: new Set(),
    sandboxTab: 'problem', // 'problem' | 'catalog'
    sandboxMode: 'grid', // 'grid' | 'ide'
    
    // Interview Quiz Engine State
    interviewTracks: {},
    activeTrackKey: 'data_science',
    activeSetId: 'ds_level1_foundations',
    quizQuestions: [],
    currentQuizIdx: 0,
    selectedQuizOption: null,
    quizSubmitted: false,
    quizStats: { correct: 0, incorrect: 0 }
  },

  libraryDocs: [
    {
      icon: "📘", title: "ISLP — Statistical Learning with Python",
      author: "James, Witten, Hastie, Tibshirani (Stanford)",
      desc: "The definitive machine learning textbook on regression, classification, resampling, and trees.",
      tag: "Stanford PDF", url: "https://www.statlearning.com/", accent: "#38bdf8"
    },
    {
      icon: "📘", title: "Mathematics for Machine Learning",
      author: "Deisenroth, Faisal, Ong (Cambridge)",
      desc: "Rigorous linear algebra, matrix decompositions, vector calculus, and optimization.",
      tag: "Cambridge Univ.", url: "https://mml-book.github.io/", accent: "#a855f7"
    },
    {
      icon: "📘", title: "Dive into Deep Learning (D2L.ai)",
      author: "Aston Zhang, Zack Lipton, Mu Li, Alex Smola",
      desc: "Interactive 1000+ page deep learning textbook from MLPs to Attention Transformers.",
      tag: "1000+ Pages", url: "https://d2l.ai/", accent: "#f59e0b"
    },
    {
      icon: "📘", title: "UC Berkeley Data 8 Textbook",
      author: "Ani Adhikari & John DeNero (UC Berkeley)",
      desc: "Foundations of Data Science: Python for simulation, estimation, and hypothesis tests.",
      tag: "UC Berkeley", url: "https://inferentialthinking.com/chapters/intro.html", accent: "#10b981"
    },
    {
      icon: "📘", title: "Think Stats (2nd Edition)",
      author: "Allen B. Downey (Green Tea Press)",
      desc: "Exploratory Data Analysis, probability distributions, CDFs, and statistical tests.",
      tag: "PDF Book", url: "https://greenteapress.com/wp/think-stats-2e/", accent: "#38bdf8"
    },
    {
      icon: "📘", title: "Think Python (2nd Edition)",
      author: "Allen B. Downey",
      desc: "How to Think Like a Computer Scientist with Python structures and algorithms.",
      tag: "PDF Book", url: "https://greenteapress.com/wp/think-python-2e/", accent: "#38bdf8"
    },
    {
      icon: "📘", title: "Think Bayes (2nd Edition)",
      author: "Allen B. Downey",
      desc: "Practical computational Bayesian statistics and belief updating in Python.",
      tag: "PDF Book", url: "https://greenteapress.com/wp/think-bayes/", accent: "#a855f7"
    },
    {
      icon: "📕", title: "NIST SP 800-61 Rev 2",
      author: "National Institute of Standards & Technology",
      desc: "Computer Security Incident Handling Guide: Preparation, Detection, Containment, Recovery.",
      tag: "NIST Standard", url: "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf", accent: "#f43f5e"
    },
    {
      icon: "📕", title: "NIST Cybersecurity Framework (CSF) 2.0",
      author: "NIST Official",
      desc: "Core cybersecurity functions: Govern, Identify, Protect, Detect, Respond, and Recover.",
      tag: "CSF 2.0", url: "https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf", accent: "#fb7185"
    },
    {
      icon: "📋", title: "Official Pandas Cheatsheet",
      author: "Pandas Development Team",
      desc: "Comprehensive syntax guide for DataFrame reshaping, grouping, and window operations.",
      tag: "Official PDF", url: "https://pandas.pydata.org/Pandas_Cheat_Sheet.pdf", accent: "#38bdf8"
    },
    {
      icon: "📋", title: "Advanced SQL Syntax Cheatsheet",
      author: "SQL Tutorial Guide",
      desc: "SELECT, JOIN types, GROUP BY, HAVING, subqueries, CTEs, and Window functions.",
      tag: "SQL Sheet", url: "https://www.sqltutorial.org/sql-cheat-sheet/", accent: "#38bdf8"
    },
    {
      icon: "📋", title: "Stanford CS229 ML Cheatsheet",
      author: "Afshine & Shervine Amidi (Stanford)",
      desc: "Supervised algorithms, SVMs, decision trees, neural networks, and regularization.",
      tag: "Stanford CS229", url: "https://stanford.edu/~shervine/teaching/cs-229/cheatsheet-supervised-learning", accent: "#f59e0b"
    },
    {
      icon: "📋", title: "Stanford CS229 Linear Algebra Review",
      author: "Zico Kolter (Stanford)",
      desc: "Matrices, operations, eigenvalues, eigenvectors, trace, and SVD decomposition.",
      tag: "Linear Algebra", url: "https://see.stanford.edu/materials/aimlcs229/cs229-linalg.pdf", accent: "#a855f7"
    },
    {
      icon: "📋", title: "Stanford CS229 Probability Review",
      author: "Apoorv Vyas (Stanford)",
      desc: "Random variables, joint distributions, conditional expectations, and variance.",
      tag: "Probability", url: "https://see.stanford.edu/materials/aimlcs229/cs229-prob.pdf", accent: "#f59e0b"
    },
    {
      icon: "📋", title: "Harvard Stat 110 Probability Cheatsheet",
      author: "Joe Blitzstein & William Chen (Harvard)",
      desc: "Master probability distribution formulas, expectations, and identities.",
      tag: "Harvard Stat 110", url: "https://wzchen.github.io/probability_cheatsheet/", accent: "#f59e0b"
    },
    {
      icon: "📋", title: "Official Git Cheatsheet",
      author: "GitHub Education",
      desc: "Branching, staging, diffing, rebasing, and remote team collaboration commands.",
      tag: "GitHub Sheet", url: "https://education.github.io/git-cheat-sheet-education.pdf", accent: "#10b981"
    }
  ],

  async init() {
    this.bindSidebarNavigation();
    this.bindSubtabNavigation();
    this.initSolvedState();
    this.bindSandboxEvents();
    await this.loadPlatforms();
    await this.loadChallenges();
    await this.loadInterviewTracks();
    this.renderLibraryCatalog();
    this.renderDrillsHub();

    if (this.state.challenges.length > 0) {
      await this.selectChallenge(this.state.challenges[0].id);
    }
  },

  // ── Challenge Completion Persistence ──────────────────────────────────────
  initSolvedState() {
    try {
      const local = JSON.parse(localStorage.getItem('vault_solved_challenges') || '[]');
      if (Array.isArray(local)) {
        local.forEach(id => this.state.solvedChallenges.add(id));
      }
    } catch (e) {
      console.warn('Could not read local solved challenges:', e);
    }

    // Sync with SQLite backend
    fetch('/api/solved-challenges')
      .then(r => r.json())
      .then(data => {
        if (data && Array.isArray(data.solved_ids)) {
          data.solved_ids.forEach(id => this.state.solvedChallenges.add(id));
          localStorage.setItem('vault_solved_challenges', JSON.stringify(Array.from(this.state.solvedChallenges)));
          this.updateGlobalSolvedProgress();
          this.renderNeetCodeGrid();
          this.renderChallengeList();
          this.renderChallengeDropdown();
          if (this.state.activeChallenge) {
            this.updateActiveChallengeSolvedUI();
          }
        }
      })
      .catch(err => console.warn('Solved challenges sync failed:', err));
  },

  updateGlobalSolvedProgress() {
    const count = this.state.solvedChallenges.size;
    const total = 312;
    const pct = Math.min(100, (count / total) * 100);

    const countEl = document.getElementById('global-solved-count');
    if (countEl) countEl.textContent = `${count} / ${total}`;

    const barEl = document.getElementById('global-progress-bar');
    if (barEl) barEl.style.width = `${pct.toFixed(1)}%`;

    const pctEl = document.getElementById('global-solved-percent');
    if (pctEl) pctEl.textContent = `${pct.toFixed(1)}%`;
  },

  // ── Sidebar Navigation ────────────────────────────────────────────────────
  bindSidebarNavigation() {
    document.querySelectorAll('.sidebar-item').forEach(item => {
      item.addEventListener('click', () => {
        const view = item.dataset.view;
        this.switchView(view);
      });
    });
  },

  switchView(viewName) {
    if (viewName === 'dsa-blueprint' || viewName === 'dsa') viewName = 'dsa-blueprint';
    if (viewName === 'dsa-drills' || viewName === 'interview-drills') viewName = 'drills';

    this.state.activeView = viewName;
    document.querySelectorAll('.sidebar-item').forEach(item => {
      const v = item.dataset.view;
      const isMatch = (v === viewName) ||
                      (viewName === 'dsa-blueprint' && v === 'dsa') ||
                      (viewName === 'drills' && (v === 'dsa-drills' || v === 'drills')) ||
                      (viewName === 'quiz' && (v === 'dsa-drills' || v === 'drills'));
      item.classList.toggle('active', isMatch);
    });

    document.querySelectorAll('.track-view').forEach(v => v.classList.add('hidden'));

    const target = document.getElementById(`view-${viewName}`);
    if (target) {
      target.classList.remove('hidden');
    }

    if (viewName === 'drills') {
      if (!this.state.activeTrackKey) {
        this.state.activeTrackKey = 'machine_learning';
      }
      this.renderDrillsHub();
    }

    if (viewName === 'sandbox') {
      if (this.state.sandboxMode === 'grid') {
        this.renderNeetCodeGrid();
      }
    }
  },

  // ── Sub-tab Navigation (Inside each track) ─────────────────────────────────
  bindSubtabNavigation() {
    document.querySelectorAll('.subtab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const subtabId = btn.dataset.subtab;
        const parentSection = btn.closest('.track-view');
        
        parentSection.querySelectorAll('.subtab-btn').forEach(b => {
          b.classList.remove('active', 'bg-cyan-500/15', 'text-cyan-300', 'border-cyan-500/30',
                             'bg-purple-500/15', 'text-purple-300', 'border-purple-500/30',
                             'bg-rose-500/15', 'text-rose-300', 'border-rose-500/30',
                             'bg-amber-500/15', 'text-amber-300', 'border-amber-500/30');
          b.classList.add('bg-slate-900/60', 'text-slate-400', 'border-slate-800');
        });

        btn.classList.remove('bg-slate-900/60', 'text-slate-400', 'border-slate-800');
        btn.classList.add('active', 'bg-emerald-500/15', 'text-emerald-300', 'border-emerald-500/30');

        // Toggle subtab panels
        const trackPrefix = subtabId.split('-')[0]; // ds, ml, cyber, dsa
        parentSection.querySelectorAll(`[id^="subtab-${trackPrefix}-"]`).forEach(panel => {
          panel.classList.add('hidden');
        });

        const targetPanel = document.getElementById(`subtab-${subtabId}`);
        if (targetPanel) {
          targetPanel.classList.remove('hidden');
        }

        // Trigger quiz loading when switching to prep subtab
        if (subtabId.endsWith('-prep')) {
          this.activatePrepSubtab(trackPrefix);
        }
      });
    });
  },

  formatSetName(setId, rawName) {
    const formattedMap = {
      'ml_level1_foundations': '🌱 Level 1: Foundations',
      'ml_level2_intermediate': '⚡ Level 2: Intermediate',
      'ml_level3_advanced': '🔥 Level 3: Advanced Mastery',
      'ds_level1_foundations': '🌱 Level 1: Foundations',
      'ds_level2_intermediate': '⚡ Level 2: Intermediate',
      'ds_level3_advanced': '🔥 Level 3: Advanced Mastery',
      'dsa_level1_foundations': '🌱 Level 1: Foundations',
      'dsa_level2_intermediate': '⚡ Level 2: Intermediate',
      'dsa_level3_advanced': '🔥 Level 3: Advanced Mastery',
      'domain1_security_principles': '🛡️ Domain 1: Security Principles',
      'domain2_bcp_dr_incident_response': '🔄 Domain 2: BCP & Incident Response',
      'domain3_access_controls': '🔑 Domain 3: Access Controls',
      'domain4_network_security': '🌐 Domain 4: Network Security',
      'domain5_security_operations': '⚙️ Domain 5: Security Operations',
      'ml_topic_loss_optimization': '📉 Loss Functions & Optimization',
      'ml_topic_regularization': '🎯 Regularization & Generalization',
      'ml_topic_model_evaluation': '🧪 Evaluation & Experimental Design',
      'ml_topic_feature_engineering': '📐 Feature Eng & PCA',
      'ml_topic_tree_ensembles': '🌲 Tree Ensembles & Kernel Methods',
      'ml_topic_unsupervised_learning': '🧩 Unsupervised & Calibration'
    };
    if (formattedMap[setId]) return formattedMap[setId];
    return (rawName || setId).replace(/(\w+)\s*Level(\d+)\s*(.*)/i, '$1 Level $2: $3');
  },

  getTrackTheme(trackPrefix) {
    const themes = {
      'ml': {
        name: 'Machine Learning',
        active: 'bg-purple-500/20 text-purple-300 border-purple-500/50 shadow-lg shadow-purple-500/10 ring-1 ring-purple-500/30',
        badge: 'bg-purple-500/30 text-purple-200',
        gradient: 'from-purple-500 via-pink-500 to-indigo-500',
        iconBg: 'bg-purple-500/15 border-purple-500/30 text-purple-300',
        selectedCard: 'bg-purple-500/15 border-purple-500 text-white shadow-lg shadow-purple-500/10 ring-1 ring-purple-500/50',
        selectedBadge: 'bg-purple-500 text-slate-950 font-black border-purple-400',
        btnNext: 'from-purple-500 to-pink-500 text-white hover:from-purple-400 hover:to-pink-400'
      },
      'ds': {
        name: 'Data Science',
        active: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/50 shadow-lg shadow-cyan-500/10 ring-1 ring-cyan-500/30',
        badge: 'bg-cyan-500/30 text-cyan-200',
        gradient: 'from-cyan-500 via-blue-500 to-teal-500',
        iconBg: 'bg-cyan-500/15 border-cyan-500/30 text-cyan-300',
        selectedCard: 'bg-cyan-500/15 border-cyan-500 text-white shadow-lg shadow-cyan-500/10 ring-1 ring-cyan-500/50',
        selectedBadge: 'bg-cyan-500 text-slate-950 font-black border-cyan-400',
        btnNext: 'from-cyan-500 to-blue-500 text-white hover:from-cyan-400 hover:to-blue-400'
      },
      'cyber': {
        name: 'Cyber Security',
        active: 'bg-rose-500/20 text-rose-300 border-rose-500/50 shadow-lg shadow-rose-500/10 ring-1 ring-rose-500/30',
        badge: 'bg-rose-500/30 text-rose-200',
        gradient: 'from-rose-500 via-pink-500 to-orange-500',
        iconBg: 'bg-rose-500/15 border-rose-500/30 text-rose-300',
        selectedCard: 'bg-rose-500/15 border-rose-500 text-white shadow-lg shadow-rose-500/10 ring-1 ring-rose-500/50',
        selectedBadge: 'bg-rose-500 text-white font-black border-rose-400',
        btnNext: 'from-rose-500 to-orange-500 text-white hover:from-rose-400 hover:to-orange-400'
      },
      'dsa': {
        name: 'DSA & Algorithms',
        active: 'bg-amber-500/20 text-amber-300 border-amber-500/50 shadow-lg shadow-amber-500/10 ring-1 ring-amber-500/30',
        badge: 'bg-amber-500/30 text-amber-200',
        gradient: 'from-amber-500 via-orange-500 to-yellow-500',
        iconBg: 'bg-amber-500/15 border-amber-500/30 text-amber-300',
        selectedCard: 'bg-amber-500/15 border-amber-500 text-white shadow-lg shadow-amber-500/10 ring-1 ring-amber-500/50',
        selectedBadge: 'bg-amber-500 text-slate-950 font-black border-amber-400',
        btnNext: 'from-amber-500 to-orange-500 text-slate-950 hover:from-amber-400 hover:to-orange-400'
      }
    };
    return themes[trackPrefix] || themes['ml'];
  },

  openDrillsForTrack(trackPrefix, setId = null) {
    const trackMap = {
      'ds': 'data_science',
      'ml': 'machine_learning',
      'cyber': 'cybersecurity',
      'dsa': 'dsa'
    };
    const trackKey = trackMap[trackPrefix] || 'machine_learning';
    this.state.activeTrackKey = trackKey;

    const trackObj = this.state.interviewTracks[trackKey];
    let targetSetId = setId;
    if (!targetSetId && trackObj && trackObj.sets && trackObj.sets.length > 0) {
      targetSetId = trackObj.sets[0].id;
    }

    this.startQuizSession(trackKey, trackPrefix, targetSetId);
  },

  startQuizSession(trackKey, pfx, setId) {
    this.state.activeTrackKey = trackKey;
    this.state.activeSetId = setId;
    this.state.quizStats = { correct: 0, incorrect: 0 };
    this.state.currentQuizIdx = 0;
    this.state.selectedQuizOption = null;
    this.state.quizSubmitted = false;

    if (!pfx) {
      const pfxMap = { 'machine_learning': 'ml', 'data_science': 'ds', 'cybersecurity': 'cyber', 'dsa': 'dsa' };
      pfx = pfxMap[trackKey] || 'ml';
    }

    // Update session header telemetry in view-quiz
    const trackMeta = {
      'machine_learning': { name: '🧠 AIML', color: 'bg-purple-500/20 text-purple-300 border-purple-500/30' },
      'data_science': { name: '📊 DATA SCIENCE', color: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30' },
      'cybersecurity': { name: '🛡️ CYBER SECURITY', color: 'bg-rose-500/20 text-rose-300 border-rose-500/30' },
      'dsa': { name: '⚡ DSA', color: 'bg-amber-500/20 text-amber-300 border-amber-500/30' }
    }[trackKey] || { name: '🎯 DRILLS', color: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' };

    const badgeEl = document.getElementById('quiz-session-domain-badge');
    if (badgeEl) {
      badgeEl.className = `px-2.5 py-1 rounded-full text-xs font-bold font-mono border ${trackMeta.color}`;
      badgeEl.textContent = trackMeta.name;
    }

    const titleEl = document.getElementById('quiz-session-level-title');
    if (titleEl) {
      const trackObj = this.state.interviewTracks[trackKey];
      const setObj = (trackObj?.sets || []).find(s => s.id === setId);
      const levelTitle = setObj ? this.formatSetName(setObj.id, setObj.name) : (setId || 'Practice Level');
      titleEl.textContent = levelTitle;
    }

    // Switch to dedicated quiz view
    this.switchView('quiz');

    // Load questions and render card
    this.loadQuizQuestions(pfx);

    // Scroll to top of the page
    window.scrollTo({ top: 0, behavior: 'smooth' });
  },

  activatePrepSubtab(trackPrefix) {
    this.openDrillsForTrack(trackPrefix);
  },

  renderDrillsHub() {
    const container = document.getElementById('drills-domain-cards-container');
    if (!container) return;

    const tracksMeta = [
      {
        key: 'machine_learning',
        pfx: 'ml',
        title: 'AI & Machine Learning (AIML)',
        badge: '🧠 AIML TRACK',
        desc: 'Stanford ISLP statistical modeling, Cambridge mathematics for ML, optimization, and deep learning neural nets.',
        icon: '🧠',
        borderActive: 'border-purple-500/60 ring-2 ring-purple-500/30 bg-purple-950/20',
        lineGradient: 'from-purple-500 via-pink-500 to-indigo-500',
        badgeColor: 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
      },
      {
        key: 'data_science',
        pfx: 'ds',
        title: 'Data Science (DS)',
        badge: '📊 DATA SCIENCE TRACK',
        desc: 'Statistical inference, advanced SQL window functions & CTEs, Pandas wrangling, and exploratory analytics.',
        icon: '📊',
        borderActive: 'border-cyan-500/60 ring-2 ring-cyan-500/30 bg-cyan-950/20',
        lineGradient: 'from-cyan-500 via-blue-500 to-teal-500',
        badgeColor: 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
      },
      {
        key: 'cybersecurity',
        pfx: 'cyber',
        title: 'Cyber Security (ISC2 CC)',
        badge: '🛡️ CYBER SECURITY TRACK',
        desc: 'ISC2 CC exam prep banks: Security Principles, BCP/DR, Access Control, Network Security & Incident Operations.',
        icon: '🛡️',
        borderActive: 'border-rose-500/60 ring-2 ring-rose-500/30 bg-rose-950/20',
        lineGradient: 'from-rose-500 via-pink-500 to-orange-500',
        badgeColor: 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
      },
      {
        key: 'dsa',
        pfx: 'dsa',
        title: 'Data Structures & Algorithms (DSA)',
        badge: '⚡ FAANG BLUEPRINT',
        desc: 'NeetCode 150 & Blind 75 core patterns, Python 3 Big-O analysis, and FAANG screening drills.',
        icon: '⚡',
        borderActive: 'border-amber-500/60 ring-2 ring-amber-500/30 bg-amber-950/20',
        lineGradient: 'from-amber-500 via-orange-500 to-yellow-500',
        badgeColor: 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
      }
    ];

    let html = '';
    tracksMeta.forEach(t => {
      const trackObj = this.state.interviewTracks[t.key] || { sets: [] };
      const isTrackActive = this.state.activeTrackKey === t.key;
      const theme = this.getTrackTheme(t.pfx);
      const totalQs = (trackObj.sets || []).reduce((acc, s) => acc + (s.question_count || 0), 0);

      html += `
        <div class="glass-panel p-5 relative overflow-hidden transition-all duration-300 rounded-2xl border ${
          isTrackActive ? t.borderActive : 'border-slate-800/80 hover:border-slate-700 bg-slate-900/50'
        }" data-track="${t.key}">
          <!-- Top theme accent line -->
          <div class="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r ${t.lineGradient} ${isTrackActive ? 'opacity-100' : 'opacity-40'}"></div>
          
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-3.5">
            <div class="space-y-1">
              <div class="flex items-center gap-2.5 flex-wrap">
                <span class="text-xl">${t.icon}</span>
                <h3 class="text-base font-bold text-white tracking-tight">${t.title}</h3>
                <span class="text-[10px] px-2 py-0.5 rounded-full font-mono font-bold ${t.badgeColor}">${t.badge}</span>
                <span class="text-[11px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">${totalQs} Questions</span>
              </div>
              <p class="text-xs text-slate-400">${t.desc}</p>
            </div>
            ${isTrackActive ? `<span class="px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-[10px] font-mono font-bold flex items-center gap-1.5 self-start md:self-center"><span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> ACTIVE DOMAIN</span>` : ''}
          </div>

          <!-- Nested Sub-Levels Pills (Wireframed by User in media_1789455278758.png) -->
          <div class="pt-3 border-t border-slate-800/80">
            <div class="text-[10px] font-mono font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <span>🎯</span> <span>Sub-Levels & Assessments:</span>
            </div>
            <div class="flex flex-wrap items-center gap-2">
      `;

      (trackObj.sets || []).forEach(set => {
        const isLevelSelected = isTrackActive && (this.state.activeSetId === set.id);
        const displayName = this.formatSetName(set.id, set.name);
        html += `
          <button class="level-pill-btn px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all flex items-center gap-2 cursor-pointer ${
            isLevelSelected 
              ? theme.active 
              : 'bg-slate-900/90 text-slate-400 border border-slate-800 hover:text-white hover:border-slate-700 hover:bg-slate-800/60'
          }" data-track="${t.key}" data-pfx="${t.pfx}" data-set="${set.id}">
            <span>${displayName}</span>
            <span class="px-2 py-0.5 text-[10px] rounded-full ${isLevelSelected ? theme.badge : 'bg-slate-800 text-slate-400'} font-mono font-bold">${set.question_count} Qs</span>
          </button>
        `;
      });

      html += `
            </div>
          </div>
        </div>
      `;
    });

    container.innerHTML = html;

    // Attach click listeners to level pills
    container.querySelectorAll('.level-pill-btn').forEach(btn => {
      btn.onclick = (e) => {
        e.stopPropagation();
        const trackKey = btn.dataset.track;
        const pfx = btn.dataset.pfx;
        const setId = btn.dataset.set;

        this.startQuizSession(trackKey, pfx, setId);
      };
    });
  },

  async loadQuizQuestions(trackPrefix) {
    const trackKey = this.state.activeTrackKey;
    const setId = this.state.activeSetId;
    if (!trackKey || !setId) return;

    try {
      const res = await fetch(`/api/interviews/${trackKey}/${setId}`);
      if (!res.ok) return;
      const data = await res.json();
      this.state.quizQuestions = data.questions || [];
      this.state.currentQuizIdx = 0;
      this.state.selectedQuizOption = null;
      this.state.quizSubmitted = false;
      this.renderQuizCard(trackPrefix);
    } catch (e) {
      console.error('Failed to load quiz questions:', e);
    }
  },

  renderQuizCard(trackPrefix) {
    let container = document.getElementById('unified-quiz-container');
    if (!container) {
      container = document.getElementById(`${trackPrefix}-quiz-container`);
    }
    if (!container) return;

    const theme = this.getTrackTheme(trackPrefix);
    const qList = this.state.quizQuestions;
    if (!qList || qList.length === 0) {
      container.innerHTML = '<div class="p-12 text-center text-slate-400 font-mono text-xs">Loading questions for this level...</div>';
      return;
    }

    const q = qList[this.state.currentQuizIdx];
    const qNum = this.state.currentQuizIdx + 1;
    const totalQ = qList.length;
    const progressPct = ((qNum / totalQ) * 100).toFixed(1);

    const questionPrompt = q.stem || q.question || q.prompt || 'Question prompt not specified.';
    const correctKey = (q.correct_key || q.answer || q.correct || '').toString().trim().toUpperCase();

    // Parse options safely from Dict or Array
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
    optionsList.forEach((opt, optIdx) => {
      const isChosen = this.state.selectedQuizOption === opt.key;
      let cardStyle = 'bg-slate-950/50 border-slate-800/80 hover:border-slate-600 hover:bg-slate-900/80 hover:translate-x-1 shadow-sm';
      let badgeStyle = 'bg-slate-900 text-slate-300 border border-slate-700/80 group-hover:border-slate-500 group-hover:text-white';
      let statusBadge = '';

      if (this.state.quizSubmitted) {
        const isCorrect = (opt.key === correctKey);
        if (isCorrect) {
          cardStyle = 'bg-emerald-950/60 border-emerald-400 text-emerald-100 shadow-xl shadow-emerald-950/40 ring-1 ring-emerald-400/50';
          badgeStyle = 'bg-emerald-500 text-slate-950 font-black border-emerald-400';
          statusBadge = '<span class="text-[11px] px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-bold ml-auto flex items-center gap-1">✓ Correct Answer</span>';
        } else if (isChosen) {
          cardStyle = 'bg-rose-950/60 border-rose-500 text-rose-100 shadow-xl shadow-rose-950/40 ring-1 ring-rose-500/50';
          badgeStyle = 'bg-rose-500 text-white font-black border-rose-400';
          statusBadge = '<span class="text-[11px] px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40 font-bold ml-auto flex items-center gap-1">✗ Your Choice</span>';
        } else {
          cardStyle = 'bg-slate-950/30 border-slate-900/40 text-slate-500 opacity-40 cursor-default';
        }
      } else if (isChosen) {
        cardStyle = theme.selectedCard;
        badgeStyle = theme.selectedBadge;
      }

      optionsHtml += `
        <div class="group p-4 rounded-xl border transition-all duration-200 cursor-pointer flex items-start gap-3.5 relative overflow-hidden select-none ${cardStyle}" onclick="App.selectQuizOption('${opt.key}', '${trackPrefix}')">
          <span class="w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center text-xs font-mono font-bold transition-all ${badgeStyle}">
            ${this.state.quizSubmitted && opt.key === correctKey ? '✓' : opt.key}
          </span>
          <span class="text-sm leading-relaxed flex-1 pt-0.5 font-medium">${opt.text}</span>
          ${statusBadge}
        </div>
      `;
    });

    let rationaleHtml = '';
    if (this.state.quizSubmitted) {
      const userGotCorrect = (this.state.selectedQuizOption === correctKey);
      
      rationaleHtml = `
        <div class="mt-6 p-5 rounded-2xl ${userGotCorrect ? 'bg-emerald-950/30 border-emerald-500/40' : 'bg-rose-950/30 border-rose-500/40'} border space-y-3.5 shadow-xl">
          <div class="flex items-center gap-2.5">
            <span class="text-lg">${userGotCorrect ? '🎉' : '💡'}</span>
            <span class="font-bold text-sm ${userGotCorrect ? 'text-emerald-300' : 'text-rose-300'}">
              ${userGotCorrect ? 'Excellent! You answered correctly.' : `Pedagogical Feedback — Correct Answer is Option ${correctKey}`}
            </span>
          </div>
      `;

      if (q.rationales && typeof q.rationales === 'object') {
        if (q.rationales.correct) {
          rationaleHtml += `
            <div class="p-3.5 rounded-xl bg-black/40 border border-slate-800/80 text-xs text-emerald-300 font-medium leading-relaxed">
              <strong class="text-white block mb-1">Core Technical Principle:</strong>
              ${q.rationales.correct}
            </div>
          `;
        }
        rationaleHtml += '<div class="space-y-2 pt-1 text-xs text-slate-300">';
        optionsList.forEach(opt => {
          const rText = q.rationales[opt.key];
          if (rText) {
            const isOptCorrect = (opt.key === correctKey);
            rationaleHtml += `
              <div class="p-2.5 rounded-lg ${isOptCorrect ? 'bg-emerald-950/20 border border-emerald-500/20' : 'bg-black/30 border border-slate-800/40'} flex items-start gap-2">
                <span class="font-mono font-bold ${isOptCorrect ? 'text-emerald-400' : 'text-slate-400'} flex-shrink-0">Option ${opt.key}:</span> 
                <span class="text-slate-300 leading-relaxed">${rText}</span>
              </div>
            `;
          }
        });
        rationaleHtml += '</div>';
      } else if (q.explanation) {
        rationaleHtml += `
          <div class="p-3.5 rounded-xl bg-black/40 border border-slate-800/80 text-xs text-slate-300 leading-relaxed">
            <strong class="text-emerald-400 block mb-1">Detailed Explanation:</strong>
            ${q.explanation}
          </div>
        `;
      }
      rationaleHtml += '</div>';
    }

    const topicText = q.domain_name || q.sub_objective || q.topic || q.level_name || 'Interview Assessment';
    const totalAnswered = this.state.quizStats.correct + this.state.quizStats.incorrect;
    const accuracy = totalAnswered > 0 ? Math.round((this.state.quizStats.correct / totalAnswered) * 100) : 0;

    container.innerHTML = `
      <!-- Top Accent Line -->
      <div class="h-1 -mx-6 -mt-6 md:-mx-8 md:-mt-8 mb-5 bg-gradient-to-r ${theme.gradient}"></div>

      <div class="space-y-5">
        <!-- Telemetry & Header -->
        <div class="space-y-3 pb-3 border-b border-slate-800/80">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div class="flex items-center gap-2">
              <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full ${theme.iconBg} font-mono text-xs font-bold tracking-wider uppercase">
                <span class="w-1.5 h-1.5 rounded-full bg-current animate-pulse"></span>
                Question ${qNum} of ${totalQ}
              </span>
              <span class="text-[10px] px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono border border-slate-700/60">
                ${q.cognitive_level || 'STANDARD'}
              </span>
            </div>
            <div class="flex items-center gap-3 text-xs">
              <span class="text-slate-400 font-mono hidden sm:inline-flex items-center gap-1.5">
                <span>📂</span> <span class="truncate max-w-xs">${topicText}</span>
              </span>
              <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono text-xs font-bold">
                <span>Score:</span>
                <span class="text-white">${this.state.quizStats.correct}/${totalAnswered}</span>
                <span class="text-emerald-300">(${accuracy}%)</span>
              </div>
            </div>
          </div>

          <!-- Question Progress Bar -->
          <div class="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden border border-slate-800/60">
            <div class="h-1.5 rounded-full bg-gradient-to-r ${theme.gradient} transition-all duration-500 shadow-sm" style="width: ${progressPct}%"></div>
          </div>
        </div>

        <!-- Question Prompt -->
        <div class="space-y-2 py-1">
          <div class="flex items-start gap-3">
            <div class="w-7 h-7 rounded-lg ${theme.iconBg} flex items-center justify-center font-bold text-xs flex-shrink-0 mt-0.5 shadow-inner">
              ?
            </div>
            <h3 class="text-base md:text-lg font-bold text-white leading-relaxed tracking-tight flex-1">
              ${questionPrompt}
            </h3>
          </div>
        </div>

        <!-- Option Cards (A, B, C, D) -->
        <div class="space-y-2.5 pt-1">
          ${optionsHtml}
        </div>

        ${rationaleHtml}

        <!-- Footer Controls -->
        <div class="flex items-center justify-between pt-5 border-t border-slate-800/80 mt-6">
          <button class="btn-secondary text-xs px-4 py-2 flex items-center gap-1.5 hover:text-white" onclick="App.prevQuizQuestion('${trackPrefix}')" ${qNum === 1 ? 'disabled style="opacity:0.3;cursor:not-allowed;"' : ''}>
            <span>←</span> <span>Previous</span>
          </button>
          
          <div class="flex items-center gap-3">
            <span class="text-[11px] text-slate-500 font-mono hidden md:inline">
              Press <kbd class="px-1.5 py-0.5 bg-slate-800 rounded text-slate-300 text-[10px]">A</kbd>-<kbd class="px-1.5 py-0.5 bg-slate-800 rounded text-slate-300 text-[10px]">D</kbd> or <kbd class="px-1.5 py-0.5 bg-slate-800 rounded text-slate-300 text-[10px]">Enter</kbd>
            </span>
            ${!this.state.quizSubmitted ? `
              <button class="px-6 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 hover:from-emerald-400 hover:to-teal-400 shadow-lg shadow-emerald-950/50 hover:shadow-emerald-500/20 transition-all flex items-center gap-1.5" onclick="App.submitQuizAnswer('${trackPrefix}')">
                <span>⚡</span> <span>Check Answer</span>
              </button>
            ` : `
              <button class="px-6 py-2 rounded-xl text-xs font-bold bg-gradient-to-r ${theme.btnNext} shadow-lg transition-all flex items-center gap-1.5" onclick="App.nextQuizQuestion('${trackPrefix}')">
                <span>${qNum < totalQ ? 'Next Question →' : 'Complete Set 🎉'}</span>
              </button>
            `}
          </div>
        </div>
      </div>
    `;
  },

  selectQuizOption(key, trackPrefix) {
    if (this.state.quizSubmitted) return;
    this.state.selectedQuizOption = key;
    this.renderQuizCard(trackPrefix);
  },

  submitQuizAnswer(trackPrefix) {
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
    this.renderQuizCard(trackPrefix);

    if (this.state.selectedQuizOption === correctKey && typeof confetti === 'function') {
      confetti({
        particleCount: 50,
        spread: 60,
        origin: { y: 0.7 }
      });
    }
  },

  nextQuizQuestion(trackPrefix) {
    if (this.state.currentQuizIdx + 1 < this.state.quizQuestions.length) {
      this.state.currentQuizIdx += 1;
      this.state.selectedQuizOption = null;
      this.state.quizSubmitted = false;
      this.renderQuizCard(trackPrefix);
    } else {
      const accuracy = Math.round((this.state.quizStats.correct / this.state.quizQuestions.length) * 100);
      if (typeof confetti === 'function') {
        confetti({
          particleCount: 150,
          spread: 90,
          origin: { y: 0.5 }
        });
      }
      alert(`🎉 Set Completed! Your score: ${this.state.quizStats.correct}/${this.state.quizQuestions.length} (${accuracy}%)`);
    }
  },

  prevQuizQuestion(trackPrefix) {
    if (this.state.currentQuizIdx > 0) {
      this.state.currentQuizIdx -= 1;
      this.state.selectedQuizOption = null;
      this.state.quizSubmitted = false;
      this.renderQuizCard(trackPrefix);
    }
  },

  async loadInterviewTracks() {
    try {
      const res = await fetch('/api/interviews');
      this.state.interviewTracks = await res.json();
    } catch (e) {
      console.error('Failed to load interview tracks:', e);
    }
  },

  // ── Vault Library Catalog (All PDFs & Cheats) ─────────────────────────────
  renderLibraryCatalog() {
    const container = document.getElementById('library-cards');
    if (!container) return;

    let html = '';
    this.libraryDocs.forEach(doc => {
      html += `
        <div class="action-card flex-col items-start gap-2.5 p-4">
          <div class="action-card-accent" style="background: ${doc.accent};"></div>
          <div class="flex items-center justify-between w-full">
            <div class="flex items-center gap-2">
              <span class="text-xl">${doc.icon}</span>
              <h4 class="text-xs font-bold text-white truncate max-w-[190px]">${doc.title}</h4>
            </div>
            <span class="text-[9px] px-1.5 py-0.2 rounded-full font-mono font-semibold" style="background: ${doc.accent}20; color: ${doc.accent};">
              ${doc.tag}
            </span>
          </div>
          <p class="text-[11px] text-slate-400 line-clamp-2">${doc.desc}</p>
          <div class="pt-2 w-full flex items-center justify-between border-t border-slate-800/80">
            <span class="text-[10px] text-slate-500">${doc.author}</span>
            <a href="${doc.url}" target="_blank" class="text-xs font-bold hover:underline" style="color: ${doc.accent};">
              Open Resource ↗
            </a>
          </div>
        </div>
      `;
    });
    container.innerHTML = html;
  },

  // ── Coding Sandbox (Fleet of 312) ─────────────────────────────────────────
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
        <span>All Platforms</span>
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

  computeSubdivision(category, tags) {
    const combined = `${category || ''} ${(tags || []).join(' ')}`.toLowerCase();
    if (combined.includes('two pointer') || combined.includes('sliding window') || combined.includes('fast-slow')) {
      return 'Two Pointers & Sliding Window';
    }
    if (combined.includes('array') || combined.includes('hash') || combined.includes('matrix') || combined.includes('prefix sum') || combined.includes('set') || combined.includes('table')) {
      return 'Arrays & Hashing';
    }
    if (combined.includes('stack') || combined.includes('queue') || combined.includes('deque')) {
      return 'Stacks & Queues';
    }
    if (combined.includes('binary search') || combined.includes('search')) {
      return 'Binary Search';
    }
    if (combined.includes('linked list')) {
      return 'Linked Lists';
    }
    if (combined.includes('tree') || combined.includes('graph') || combined.includes('bfs') || combined.includes('dfs') || combined.includes('trie') || combined.includes('bst')) {
      return 'Trees & Graphs';
    }
    if (combined.includes('dynamic programming') || combined.includes('dp') || combined.includes('recursion') || combined.includes('backtrack') || combined.includes('kadane')) {
      return 'Dynamic Programming';
    }
    if (combined.includes('greedy') || combined.includes('interval')) {
      return 'Greedy';
    }
    if (combined.includes('bit') || combined.includes('math') || combined.includes('number theory') || combined.includes('geometry') || combined.includes('combinatorics') || combined.includes('statistics')) {
      return 'Math & Bit Manipulation';
    }
    if (combined.includes('string') || combined.includes('regex') || combined.includes('suffix')) {
      return 'Strings';
    }
    return 'Core Programming & Logic';
  },

  renderFrequencyBars(ch) {
    let count = 4;
    const plat = ch.platform || '';
    const diff = (ch.difficulty || 'Easy').toLowerCase();

    if (plat.includes('Placement') || plat.includes('LeetCode') || plat.includes('Foundational')) {
      count = diff === 'easy' ? 5 : 4;
    } else if (diff === 'easy') {
      count = 5;
    } else if (diff === 'medium') {
      count = 4;
    } else {
      count = 3;
    }

    let bars = '<div class="freq-meter" title="Interview Yield: ' + count + '/5">';
    for (let i = 0; i < 5; i++) {
      bars += `<span class="freq-block ${i < count ? 'active' : ''}"></span>`;
    }
    bars += '</div>';
    return bars;
  },

  switchSandboxMode(mode) {
    this.state.sandboxMode = mode;
    const gridView = document.getElementById('sandbox-grid-view');
    const ideView = document.getElementById('sandbox-ide-view');
    const btnGrid = document.getElementById('btn-mode-grid');
    const btnIde = document.getElementById('btn-mode-ide');

    if (mode === 'grid') {
      if (gridView) gridView.classList.remove('hidden');
      if (ideView) ideView.classList.add('hidden');
      if (btnGrid) btnGrid.classList.add('active');
      if (btnIde) btnIde.classList.remove('active');
      this.renderNeetCodeGrid();
    } else {
      if (gridView) gridView.classList.add('hidden');
      if (ideView) ideView.classList.remove('hidden');
      if (btnIde) btnIde.classList.add('active');
      if (btnGrid) btnGrid.classList.remove('active');
      if (!this.state.activeChallenge && this.state.challenges && this.state.challenges.length > 0) {
        this.selectChallenge(this.state.challenges[0].id);
      }
    }
  },

  async loadChallenges() {
    const plat = this.state.selectedPlatform;
    const diff = this.state.selectedDifficulty;
    const q = encodeURIComponent(this.state.searchQuery || '');
    const url = `/api/challenges?platform=${plat}&difficulty=${diff}&search=${q}&limit=500`;

    try {
      const res = await fetch(url);
      const data = await res.json();
      let all = data.challenges || [];

      // Apply Status Filter (All / Unsolved / Solved)
      if (this.state.selectedStatus === 'solved') {
        all = all.filter(ch => this.state.solvedChallenges.has(ch.id));
      } else if (this.state.selectedStatus === 'unsolved') {
        all = all.filter(ch => !this.state.solvedChallenges.has(ch.id));
      }

      this.state.challenges = all;
      this.renderNeetCodeGrid();
      this.renderChallengeList();
      this.renderChallengeDropdown();
      this.updateGlobalSolvedProgress();
    } catch (e) {
      console.error('Failed to load challenges:', e);
    }
  },

  renderNeetCodeGrid() {
    const container = document.getElementById('neetcode-roadmap-container');
    if (!container) return;

    if (!this.state.challenges || this.state.challenges.length === 0) {
      container.innerHTML = `
        <div class="p-12 text-center text-slate-400 text-xs font-mono rounded-xl bg-slate-900/60 border border-slate-800">
          No challenges match the active filter. Try selecting 'All Platforms' or 'All Status'.
        </div>
      `;
      return;
    }

    const orderedPlatformNames = [
      "LeetCode",
      "HackerRank",
      "GeeksforGeeks",
      "CodeChef",
      "GUVI - CodeKata",
      "Placement Preparation",
      "Codewars",
      "HackerEarth",
      "Programiz",
      "W3Schools",
      "Foundational Sandbox"
    ];

    const platformsMap = new Map();
    orderedPlatformNames.forEach(p => platformsMap.set(p, []));

    this.state.challenges.forEach(ch => {
      const platName = ch.platform || "Foundational Sandbox";
      if (!platformsMap.has(platName)) {
        platformsMap.set(platName, []);
      }
      platformsMap.get(platName).push(ch);
    });

    let html = '';

    platformsMap.forEach((pChallenges, platName) => {
      // If no challenges match for this platform under current filters, skip it
      if (pChallenges.length === 0) {
        return;
      }

      const platSolvedCount = pChallenges.filter(ch => this.state.solvedChallenges.has(ch.id)).length;
      const platTotal = pChallenges.length;
      const platPct = platTotal > 0 ? (platSolvedCount / platTotal) * 100 : 0;

      // Group by subdivision
      const subMap = new Map();
      const SUBDIVISION_ORDER = [
        'Arrays & Hashing',
        'Two Pointers & Sliding Window',
        'Stacks & Queues',
        'Binary Search',
        'Linked Lists',
        'Trees & Graphs',
        'Dynamic Programming',
        'Greedy',
        'Math & Bit Manipulation',
        'Strings',
        'Core Programming & Logic'
      ];
      SUBDIVISION_ORDER.forEach(s => subMap.set(s, []));

      pChallenges.forEach(ch => {
        const sub = ch.subdivision || this.computeSubdivision(ch.category, ch.tags || []);
        if (!subMap.has(sub)) subMap.set(sub, []);
        subMap.get(sub).push(ch);
      });

      html += `
        <div class="neetcode-accordion is-open rounded-xl overflow-hidden border border-slate-800/80 mb-4" data-platform="${platName}">
          <!-- Website Accordion Header (like NeetCode) -->
          <div class="neetcode-accordion-header p-4 flex items-center justify-between cursor-pointer hover:bg-slate-800/60 transition-all select-none">
            <div class="flex items-center gap-3">
              <span class="neetcode-chevron text-slate-400 font-bold">▼</span>
              <span class="text-base font-bold text-white tracking-tight flex items-center gap-2">
                <span class="text-emerald-400">🌐</span>
                <span>${platName}</span>
              </span>
              <span class="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">${platTotal} Challenges</span>
            </div>
            <div class="flex items-center gap-4">
              <span class="text-xs font-mono text-slate-300">
                <strong class="text-emerald-400">${platSolvedCount}</strong> / ${platTotal}
              </span>
              <div class="w-24 md:w-36 bg-slate-800 rounded-full h-2 overflow-hidden">
                <div class="bg-gradient-to-r from-emerald-500 to-teal-400 h-2 rounded-full transition-all duration-500" style="width: ${platPct.toFixed(1)}%"></div>
              </div>
            </div>
          </div>

          <!-- Website Accordion Body (Subdivisions like Arrays, Strings, etc.) -->
          <div class="neetcode-accordion-body p-4 pt-2 space-y-4 bg-slate-950/40">
      `;

      let hasSubdivisions = false;
      subMap.forEach((subChallenges, subName) => {
        if (subChallenges.length === 0) return;
        hasSubdivisions = true;

        const subSolvedCount = subChallenges.filter(ch => this.state.solvedChallenges.has(ch.id)).length;
        const subTotal = subChallenges.length;
        const subPct = subTotal > 0 ? (subSolvedCount / subTotal) * 100 : 0;

        html += `
          <div class="subdivision-block">
            <!-- Subdivision Header (like Arrays in screenshot) -->
            <div class="subdivision-header px-3.5 py-2.5 border-b border-slate-800/80 bg-slate-900/90 flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-cyan-400 text-xs">📂</span>
                <span class="text-white font-bold text-xs">${subName}</span>
                <span class="text-[11px] text-slate-500 font-mono">(${subTotal})</span>
              </div>
              <div class="flex items-center gap-3">
                <span class="text-[11px] font-mono text-slate-400">
                  <span class="text-emerald-400 font-semibold">${subSolvedCount}</span> / ${subTotal}
                </span>
                <div class="w-16 md:w-24 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                  <div class="bg-emerald-500 h-1.5 rounded-full transition-all duration-500" style="width: ${subPct.toFixed(1)}%"></div>
                </div>
              </div>
            </div>

            <!-- NeetCode-Style Table -->
            <div class="overflow-x-auto">
              <table class="neetcode-table w-full text-left">
                <thead>
                  <tr class="text-slate-400 border-b border-slate-800/60 text-[11px]">
                    <th class="w-12 text-center py-2 px-3">Status</th>
                    <th class="py-2 px-3">Problem</th>
                    <th class="w-24 py-2 px-3">Difficulty</th>
                    <th class="w-24 text-center py-2 px-3">Frequency</th>
                    <th class="w-32 py-2 px-3">Category</th>
                    <th class="w-28 text-right py-2 px-3">Actions</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-800/40">
        `;

        subChallenges.forEach(ch => {
          const isSolved = this.state.solvedChallenges.has(ch.id);
          const diffBadge = ch.difficulty.toLowerCase() === 'easy' ? 'badge-easy' :
                            ch.difficulty.toLowerCase() === 'medium' ? 'badge-medium' : 'badge-hard';
          const freqBars = this.renderFrequencyBars(ch);

          html += `
            <tr class="hover:bg-slate-800/50 transition-colors group ${isSolved ? 'bg-emerald-950/10' : ''}" data-row-cid="${ch.id}">
              <td class="py-2.5 px-3 text-center">
                <input type="checkbox" class="problem-checkbox" data-cid="${ch.id}" ${isSolved ? 'checked' : ''} title="Mark solved/unsolved">
              </td>
              <td class="py-2.5 px-3 font-medium">
                <a href="javascript:void(0)" class="text-slate-200 hover:text-emerald-300 transition-colors flex items-center gap-2 problem-open-link font-medium" data-cid="${ch.id}">
                  <span class="${isSolved ? 'line-through text-slate-400' : ''}">${ch.title}</span>
                </a>
              </td>
              <td class="py-2.5 px-3">
                <span class="text-[11px] px-2 py-0.5 rounded-full font-semibold ${diffBadge}">${ch.difficulty}</span>
              </td>
              <td class="py-2.5 px-3 text-center">
                ${freqBars}
              </td>
              <td class="py-2.5 px-3">
                <span class="text-[11px] text-slate-400 font-mono truncate block max-w-[150px]">${ch.category}</span>
              </td>
              <td class="py-2.5 px-3 text-right">
                <button class="btn-solve-now px-2.5 py-1 rounded bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/30 text-[11px] font-semibold transition-all inline-flex items-center gap-1" data-cid="${ch.id}">
                  <span>▶</span> <span>Solve</span>
                </button>
              </td>
            </tr>
          `;
        });

        html += `
                </tbody>
              </table>
            </div>
          </div>
        `;
      });

      if (!hasSubdivisions && pChallenges.length > 0) {
        html += '<div class="text-xs text-slate-500 font-mono p-3">No problems matching filter.</div>';
      }

      html += `
          </div>
        </div>
      `;
    });

    if (!html) {
      container.innerHTML = '<div class="p-12 text-center text-slate-400 text-xs font-mono">No problems match the selected platform, difficulty, or search query.</div>';
      return;
    }

    container.innerHTML = html;

    // Bind accordion toggles
    container.querySelectorAll('.neetcode-accordion-header').forEach(hdr => {
      hdr.onclick = (e) => {
        if (e.target.closest('button') || e.target.closest('input')) return;
        const acc = hdr.closest('.neetcode-accordion');
        if (acc) acc.classList.toggle('is-open');
      };
    });

    // Bind checkboxes
    container.querySelectorAll('.problem-checkbox').forEach(cb => {
      cb.onchange = (e) => {
        const cid = e.target.dataset.cid;
        this.toggleChallengeSolvedById(cid);
      };
    });

    // Bind problem open links and Solve buttons
    container.querySelectorAll('.problem-open-link, .btn-solve-now').forEach(btn => {
      btn.onclick = (e) => {
        e.preventDefault();
        const cid = btn.dataset.cid;
        this.selectChallenge(cid, true);
      };
    });
  },

    toggleChallengeSolvedById(cid) {
    if (!cid) return;
    const currentlySolved = this.state.solvedChallenges.has(cid);
    if (currentlySolved) {
      this.state.solvedChallenges.delete(cid);
    } else {
      this.state.solvedChallenges.add(cid);
    }

    localStorage.setItem('vault_solved_challenges', JSON.stringify(Array.from(this.state.solvedChallenges)));
    this.updateGlobalSolvedProgress();
    this.renderNeetCodeGrid();
    this.renderChallengeList();
    this.renderChallengeDropdown();
    if (this.state.activeChallenge && this.state.activeChallenge.id === cid) {
      this.updateActiveChallengeSolvedUI();
    }

    // Sync to SQLite in background
    fetch('/api/mark-solved', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ challenge_id: cid, solved: !currentlySolved })
    }).catch(err => console.warn('mark-solved error:', err));
  },

  renderChallengeDropdown() {
    const dropdown = document.getElementById('challenge-select-dropdown');
    if (!dropdown) return;

    let html = `<option value="">-- Jump to Challenge (${this.state.challenges.length}) --</option>`;
    this.state.challenges.forEach(ch => {
      const isSolved = this.state.solvedChallenges.has(ch.id);
      const mark = isSolved ? '✓ ' : '○ ';
      const isSelected = this.state.activeChallenge && this.state.activeChallenge.id === ch.id;
      html += `<option value="${ch.id}" ${isSelected ? 'selected' : ''}>${mark}${ch.platform}: ${ch.title}</option>`;
    });

    dropdown.innerHTML = html;
  },

  renderChallengeList() {
    const listEl = document.getElementById('challenge-list');
    const countBadge = document.getElementById('challenge-count-badge');
    const tabCount = document.getElementById('catalog-tab-count');

    if (countBadge) {
      countBadge.textContent = `${this.state.challenges.length} Available`;
    }
    if (tabCount) {
      tabCount.textContent = this.state.challenges.length;
    }

    if (!listEl) return;

    if (this.state.challenges.length === 0) {
      listEl.innerHTML = '<div class="p-8 text-center text-slate-400 text-xs font-mono">No challenges matching active filter.</div>';
      return;
    }

    let html = '';
    this.state.challenges.forEach(ch => {
      const isSelected = this.state.activeChallenge && this.state.activeChallenge.id === ch.id;
      const isSolved = this.state.solvedChallenges.has(ch.id);
      const diffClass = ch.difficulty.toLowerCase() === 'easy' ? 'badge-easy' : 
                        ch.difficulty.toLowerCase() === 'medium' ? 'badge-medium' : 'badge-hard';
      
      const solvedBadge = isSolved
        ? '<span class="text-[10px] px-2 py-0.5 rounded-full badge-solved font-bold flex items-center gap-1"><span>✓</span> <span>Solved</span></span>'
        : '<span class="text-[10px] px-2 py-0.5 rounded-full badge-unsolved font-medium flex items-center gap-1"><span>○</span> <span>Unsolved</span></span>';

      html += `
        <div class="challenge-item ${isSelected ? 'active' : ''} ${isSolved ? 'is-solved' : ''}" data-cid="${ch.id}">
          <div class="flex-1 min-w-0 pr-2">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-[10px] px-2 py-0.5 rounded-full ${diffClass} font-semibold">${ch.difficulty}</span>
              <span class="text-[11px] text-slate-400 truncate font-mono">${ch.platform}</span>
              ${solvedBadge}
            </div>
            <h4 class="text-xs md:text-sm font-semibold text-white truncate">${ch.title}</h4>
          </div>
          <div class="text-right flex flex-col items-end flex-shrink-0">
            <span class="text-[11px] text-slate-500 font-mono">${ch.visible_tests_count + ch.hidden_tests_count} Tests</span>
          </div>
        </div>
      `;
    });

    listEl.innerHTML = html;

    listEl.querySelectorAll('.challenge-item').forEach(item => {
      item.addEventListener('click', () => {
        this.selectChallenge(item.dataset.cid, true);
        this.switchSandboxTab('problem');
      });
    });
  },

  async selectChallenge(cid, autoOpenIde = false) {
    try {
      const res = await fetch(`/api/challenges/${cid}`);
      if (!res.ok) return;
      const ch = await res.json();
      this.state.activeChallenge = ch;
      this.state.editorContent = ch.initial_code;
      this.state.testResults = null;

      const ideTitle = document.getElementById('ide-active-title');
      if (ideTitle) {
        ideTitle.textContent = `${ch.platform}: ${ch.title}`;
      }

      this.renderChallengeDetail();
      this.renderChallengeList();
      this.renderChallengeDropdown();

      if (autoOpenIde) {
        this.switchSandboxMode('ide');
      }
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
    
    // Constraints & Targets
    const constEl = document.getElementById('ch-constraints');
    const constContainer = document.getElementById('ch-constraints-container');
    if (constEl && constContainer) {
      if (ch.constraints) {
        constEl.textContent = ch.constraints;
        constContainer.classList.remove('hidden');
      } else {
        constContainer.classList.add('hidden');
      }
    }

    // SAMPLE TEST CASES (Examples Box right beside the Editor!)
    const examplesContainer = document.getElementById('ch-examples-container');
    const examplesList = document.getElementById('ch-examples-list');
    if (examplesList && examplesContainer) {
      if (ch.visible_tests && ch.visible_tests.length > 0) {
        let exHtml = '';
        ch.visible_tests.forEach((vt, idx) => {
          let inpStr = '';
          if (typeof vt.input === 'object' && vt.input !== null && !Array.isArray(vt.input)) {
            inpStr = Object.entries(vt.input)
              .map(([k, v]) => `${k} = ${typeof v === 'object' ? JSON.stringify(v) : v}`)
              .join(', ');
          } else {
            inpStr = typeof vt.input === 'object' ? JSON.stringify(vt.input) : String(vt.input);
          }
          const outStr = typeof vt.expected === 'object' ? JSON.stringify(vt.expected) : String(vt.expected);

          exHtml += `
            <div class="example-card space-y-1">
              <div class="text-amber-400 font-bold text-[11px] tracking-wide">Example ${idx + 1}:</div>
              <div class="text-slate-200"><span class="text-slate-400 font-medium">Input:</span> ${this.escapeHtml(inpStr)}</div>
              <div class="text-emerald-400 font-semibold"><span class="text-slate-400 font-medium">Output:</span> ${this.escapeHtml(outStr)}</div>
            </div>
          `;
        });
        examplesList.innerHTML = exHtml;
        examplesContainer.classList.remove('hidden');
      } else {
        examplesContainer.classList.add('hidden');
      }
    }

    this.updateActiveChallengeSolvedUI();

    const editor = document.getElementById('code-editor');
    if (editor) {
      editor.value = this.state.editorContent;
    }

    const resultsContainer = document.getElementById('results-container');
    if (resultsContainer) {
      resultsContainer.innerHTML = `
        <div class="text-slate-500 text-xs font-mono py-6 text-center">
          Click 'Run Sample Cases' or 'Submit Solution' to execute code against tests.
        </div>
      `;
    }
  },

  updateActiveChallengeSolvedUI() {
    const ch = this.state.activeChallenge;
    if (!ch) return;

    const isSolved = this.state.solvedChallenges.has(ch.id);
    const statusPill = document.getElementById('active-ch-status-pill');
    const solvedAlert = document.getElementById('ch-solved-alert');

    if (statusPill) {
      if (isSolved) {
        statusPill.innerHTML = '<span>✓ Solved</span>';
        statusPill.className = 'text-xs font-mono px-3 py-1 rounded-full badge-solved font-bold cursor-pointer transition-all';
        statusPill.title = 'Click to mark as unsolved';
      } else {
        statusPill.innerHTML = '<span>○ Unsolved</span>';
        statusPill.className = 'text-xs font-mono px-3 py-1 rounded-full badge-unsolved font-medium cursor-pointer transition-all hover:border-slate-500';
        statusPill.title = 'Click to mark as solved';
      }
    }

    if (solvedAlert) {
      if (isSolved) {
        solvedAlert.classList.remove('hidden');
      } else {
        solvedAlert.classList.add('hidden');
      }
    }
  },

  toggleActiveChallengeSolved() {
    const ch = this.state.activeChallenge;
    if (!ch) return;
    this.toggleChallengeSolvedById(ch.id);
  },

  switchSandboxTab(tabName) {
    this.state.sandboxTab = tabName;
    const tabProblem = document.getElementById('tab-btn-problem');
    const tabCatalog = document.getElementById('tab-btn-catalog');
    const paneDetail = document.getElementById('pane-problem-detail');
    const paneCatalog = document.getElementById('pane-problem-catalog');

    if (tabName === 'problem') {
      if (tabProblem) tabProblem.className = 'sandbox-tab-btn active px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30';
      if (tabCatalog) tabCatalog.className = 'sandbox-tab-btn px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-900/80 text-slate-400 border border-slate-800 hover:text-white';
      if (paneDetail) paneDetail.classList.remove('hidden');
      if (paneCatalog) paneCatalog.classList.add('hidden');
    } else {
      if (tabCatalog) tabCatalog.className = 'sandbox-tab-btn active px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30';
      if (tabProblem) tabProblem.className = 'sandbox-tab-btn px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-900/80 text-slate-400 border border-slate-800 hover:text-white';
      if (paneCatalog) paneCatalog.classList.remove('hidden');
      if (paneDetail) paneDetail.classList.add('hidden');
    }
  },

  bindSandboxEvents() {
    // View Mode Switcher
    const btnModeGrid = document.getElementById('btn-mode-grid');
    const btnModeIde = document.getElementById('btn-mode-ide');
    const btnBackGrid = document.getElementById('btn-back-to-grid');
    if (btnModeGrid) btnModeGrid.onclick = () => this.switchSandboxMode('grid');
    if (btnModeIde) btnModeIde.onclick = () => this.switchSandboxMode('ide');
    if (btnBackGrid) btnBackGrid.onclick = () => this.switchSandboxMode('grid');

    // Expand / Collapse All
    const btnExpand = document.getElementById('btn-expand-all');
    const btnCollapse = document.getElementById('btn-collapse-all');
    if (btnExpand) {
      btnExpand.onclick = () => {
        document.querySelectorAll('.neetcode-accordion').forEach(a => a.classList.add('is-open'));
      };
    }
    if (btnCollapse) {
      btnCollapse.onclick = () => {
        document.querySelectorAll('.neetcode-accordion').forEach(a => a.classList.remove('is-open'));
      };
    }

    // Tab switching inside IDE left pane
    const tabProblem = document.getElementById('tab-btn-problem');
    const tabCatalog = document.getElementById('tab-btn-catalog');
    if (tabProblem) tabProblem.onclick = () => this.switchSandboxTab('problem');
    if (tabCatalog) tabCatalog.onclick = () => this.switchSandboxTab('catalog');

    // Solved pill toggle
    const statusPill = document.getElementById('active-ch-status-pill');
    if (statusPill) statusPill.onclick = () => this.toggleActiveChallengeSolved();

    // Quick Challenge Dropdown
    const dropdown = document.getElementById('challenge-select-dropdown');
    if (dropdown) {
      dropdown.onchange = (e) => {
        if (e.target.value) {
          this.selectChallenge(e.target.value, true);
          this.switchSandboxTab('problem');
        }
      };
    }

    // Status filter pills (All / Unsolved / Solved)
    document.querySelectorAll('.status-pill').forEach(pill => {
      pill.onclick = () => {
        document.querySelectorAll('.status-pill').forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        this.state.selectedStatus = pill.dataset.status;
        this.loadChallenges();
      };
    });

    // Run Sample Cases button
    const btnSamples = document.getElementById('btn-run-samples');
    if (btnSamples) btnSamples.onclick = () => this.runCode(false);

    // Submit Solution button
    const btnRun = document.getElementById('btn-run-code');
    if (btnRun) btnRun.onclick = () => this.runCode(true);

    // Reset & Reveal
    const btnReset = document.getElementById('btn-reset-code');
    if (btnReset) btnReset.onclick = () => this.resetCode();

    const btnReveal = document.getElementById('btn-reveal-solution');
    if (btnReveal) btnReveal.onclick = () => this.revealSolution();

    // Code Editor keyboard shortcuts: Tab key & Ctrl+Enter
    const editor = document.getElementById('code-editor');
    if (editor) {
      editor.onkeydown = (e) => {
        if (e.key === 'Tab') {
          e.preventDefault();
          const start = editor.selectionStart;
          const end = editor.selectionEnd;
          editor.value = editor.value.substring(0, start) + '    ' + editor.value.substring(end);
          editor.selectionStart = editor.selectionEnd = start + 4;
          this.state.editorContent = editor.value;
        } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
          e.preventDefault();
          this.runCode(false);
        }
      };
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

  escapeHtml(str) {
    if (typeof str !== 'string') str = String(str);
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  },

  async runCode(runHidden = true) {
    if (!this.state.activeChallenge || this.state.isRunning) return;

    const editor = document.getElementById('code-editor');
    const userCode = editor ? editor.value : this.state.editorContent;
    this.state.editorContent = userCode;

    const runBtn = runHidden ? document.getElementById('btn-run-code') : document.getElementById('btn-run-samples');
    const resultsContainer = document.getElementById('results-container');
    const terminalBadge = document.getElementById('terminal-status-badge');

    this.state.isRunning = true;
    if (runBtn) {
      runBtn.innerHTML = '<span class="animate-spin inline-block mr-1">⚙</span> Executing...';
      runBtn.disabled = true;
    }

    if (resultsContainer) {
      resultsContainer.innerHTML = `
        <div class="flex items-center justify-center gap-3 py-8 text-emerald-400 text-xs font-mono">
          <span class="animate-spin">⚙</span> Executing code inside isolated subprocess sandbox (3.0s limit)...
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
          run_hidden: runHidden
        })
      });

      const report = await res.json();
      this.state.testResults = report;
      this.renderTestResults(report, runHidden);

      if (report.status === 'PASS' && runHidden) {
        this.state.solvedChallenges.add(this.state.activeChallenge.id);
        localStorage.setItem('vault_solved_challenges', JSON.stringify(Array.from(this.state.solvedChallenges)));
        this.updateActiveChallengeSolvedUI();
        this.updateGlobalSolvedProgress();
        this.renderChallengeList();
        this.renderChallengeDropdown();
        this.renderNeetCodeGrid();

        if (typeof confetti === 'function') {
          confetti({
            particleCount: 120,
            spread: 80,
            origin: { y: 0.6 },
            colors: ['#10b981', '#34d399', '#f43f5e', '#fb7185', '#38bdf8']
          });
        }
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
      const btnSamples = document.getElementById('btn-run-samples');
      if (btnSamples) {
        btnSamples.innerHTML = '<span>▶</span> <span>Run Sample Cases</span>';
        btnSamples.disabled = false;
      }
      const btnSubmit = document.getElementById('btn-run-code');
      if (btnSubmit) {
        btnSubmit.innerHTML = '<span>⚡</span> <span>Submit Solution (Hidden Cases)</span>';
        btnSubmit.disabled = false;
      }
    }
  },

  renderTestResults(report, runHidden) {
    const container = document.getElementById('results-container');
    const terminalBadge = document.getElementById('terminal-status-badge');
    if (!container) return;

    const isPass = report.status === 'PASS';
    const statusColor = isPass ? 'text-emerald-400' : report.status === 'TIMEOUT' ? 'text-amber-400' : 'text-rose-400';
    const modeLabel = runHidden ? 'Full Test Suite (With Hidden Cases)' : 'Sample Test Cases Only';

    if (terminalBadge) {
      terminalBadge.innerHTML = `<span class="text-[11px] px-2 py-0.5 rounded-full font-mono font-semibold ${isPass ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-500/30' : 'bg-rose-950/80 text-rose-300 border border-rose-500/30'}">${report.status} (${report.passed_count}/${report.total_count})</span>`;
    }

    let html = `
      <div class="flex flex-wrap items-center justify-between p-3 rounded-lg bg-slate-900/90 border border-slate-800 mb-3 gap-2">
        <div class="flex items-center gap-2">
          <span class="text-sm font-bold ${statusColor}">● ${report.status}</span>
          <span class="text-xs text-slate-300 font-mono">(${report.passed_count}/${report.total_count} Passed)</span>
          <span class="text-slate-600">•</span>
          <span class="text-[11px] text-slate-400 font-mono">${modeLabel}</span>
        </div>
        <div class="text-xs font-mono text-slate-400">
          Runtime: <span class="text-white font-semibold">${report.runtime_ms} ms</span>
        </div>
      </div>
    `;

    if (isPass && runHidden) {
      html += `
        <div class="mb-3 p-3 rounded-lg bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 text-xs flex items-center gap-2 font-mono">
          <span>🎉</span> <span><strong>All tests passed!</strong> Challenge has been saved as <strong>✓ Solved</strong>.</span>
        </div>
      `;
    }

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
        
        let inpDisplay = '';
        if (typeof r.input === 'object' && r.input !== null) {
          inpDisplay = Object.entries(r.input).map(([k, v]) => `${k}=${JSON.stringify(v)}`).join(', ');
        } else {
          inpDisplay = JSON.stringify(r.input);
        }

        html += `
          <div class="${passClass}">
            <div class="flex justify-between items-center text-xs font-semibold mb-1">
              <span>Test Case #${r.index} ${badge}</span>
              <span class="text-slate-400 font-mono">${r.runtime_ms} ms</span>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs font-mono mt-1">
              <div class="bg-black/40 p-1.5 rounded">
                <span class="text-slate-400">Input:</span> ${this.escapeHtml(inpDisplay)}
              </div>
              <div class="bg-black/40 p-1.5 rounded">
                <span class="text-slate-400">Expected:</span> <span class="text-emerald-300">${this.escapeHtml(JSON.stringify(r.expected))}</span>
              </div>
            </div>
            ${!r.passed ? `
              <div class="mt-1.5 p-1.5 rounded bg-rose-950/40 border border-rose-900 text-xs font-mono">
                <span class="text-rose-300">Got:</span> <span class="text-white">${this.escapeHtml(JSON.stringify(r.got))}</span>
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
  }
};

window.addEventListener('DOMContentLoaded', () => {
  App.init();

  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    let timeout = null;
    searchInput.oninput = (e) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        App.state.searchQuery = e.target.value;
        App.loadChallenges();
      }, 200);
    };
  }

  document.querySelectorAll('.diff-pill').forEach(pill => {
    pill.onclick = () => {
      document.querySelectorAll('.diff-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      App.state.selectedDifficulty = pill.dataset.diff;
      App.loadChallenges();
    };
  });
});

  // Global Quiz Keyboard Shortcuts (A, B, C, D, Enter)
  window.addEventListener('keydown', (e) => {
    // Only if not inside an input, textarea or editor
    if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return;
    
    const activeView = App.state.activeView;
    const isDrillsOrQuizView = activeView === 'drills' || activeView === 'dsa-drills' || activeView === 'interview-drills' || activeView === 'quiz';
    if (!isDrillsOrQuizView) return;

    // Esc key returns to drills catalog if in quiz view
    if (e.key === 'Escape' && activeView === 'quiz') {
      App.switchView('drills');
      return;
    }

    const pfxMap = { 'machine_learning': 'ml', 'data_science': 'ds', 'cybersecurity': 'cyber', 'dsa': 'dsa' };
    const pfx = pfxMap[App.state.activeTrackKey] || 'ml';

    const key = e.key.toUpperCase();
    if (['A', 'B', 'C', 'D'].includes(key) || ['1', '2', '3', '4'].includes(e.key)) {
      const optKey = ['1', '2', '3', '4'].includes(e.key) ? String.fromCharCode(64 + parseInt(e.key)) : key;
      App.selectQuizOption(optKey, pfx);
    } else if (e.key === 'Enter') {
      if (!App.state.quizSubmitted) {
        App.submitQuizAnswer(pfx);
      } else {
        App.nextQuizQuestion(pfx);
      }
    } else if (e.key === 'ArrowLeft') {
      App.prevQuizQuestion(pfx);
    } else if (e.key === 'ArrowRight' && App.state.quizSubmitted) {
      App.nextQuizQuestion(pfx);
    }
  });
