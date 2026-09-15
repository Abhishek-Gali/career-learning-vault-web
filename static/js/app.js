/**
 * Career Learning Vault — Cloud Command Hub
 * Architecture & Engineering by Abhishek Gali
 * Powered by Refero Design & Watermelon UI System
 */

const App = {
  state: {
    currentUser: null,
    adminUsers: [],
    authToken: (typeof localStorage !== 'undefined' ? localStorage.getItem('vault_auth_token') : '') || (typeof sessionStorage !== 'undefined' ? sessionStorage.getItem('vault_auth_token') : '') || '',
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
    quizStats: { correct: 0, incorrect: 0 },

    // Trilingual Structured Course Hub State
    courses: null,
    courseLanguage: { ml: 'en', ds: 'en', cyber: 'en', dsa: 'en' },
    activeCourseId: { ml: 'karpathy_zero_to_hero', ds: 'mit_60002', cyber: 'mit_6858_security', dsa: 'striver_a2z_dsa' },
    activeVideoIdx: { ml: 0, ds: 0, cyber: 0, dsa: 0 },

    // Custom Video & Playlist Ingestion State
    customCourses: { ml: [], ds: [], cyber: [], dsa: [] },
    deferredInstallPrompt: null,
    loginParticlesAnimId: null
  },

  getAuthHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    if (this.state.authToken) {
      headers['Authorization'] = 'Bearer ' + this.state.authToken;
    }
    return headers;
  },

  escapeHtml(str) {
    if (str == null) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  },

  handleSessionExpired(message = 'Your session has expired. Please sign in again to continue.') {
    this.state.authToken = '';
    this.state.currentUser = null;
    try {
      localStorage.removeItem('vault_auth_token');
      sessionStorage.removeItem('vault_auth_token');
    } catch (e) {}

    const loginView = document.getElementById('view-login');
    if (loginView) {
      loginView.classList.remove('hidden');
      const errAlert = document.getElementById('login-error-alert');
      const errMsg = document.getElementById('login-error-message');
      if (errAlert && errMsg) {
        errMsg.textContent = message;
        errAlert.classList.remove('hidden');
      }
    }
  },

  async checkAuth() {
    try {
      const res = await fetch('/api/auth/me', { headers: this.getAuthHeaders() });
      if (res.ok) {
        const data = await res.json();
        this.state.currentUser = data.user;
        this.updateUserUI(data.user);
        const loginView = document.getElementById('view-login');
        if (loginView) loginView.classList.add('hidden');
        return true;
      } else if (res.status === 401) {
        // Clear stale/expired token immediately
        try {
          localStorage.removeItem('vault_auth_token');
          sessionStorage.removeItem('vault_auth_token');
        } catch (e) {}
        this.state.authToken = '';
      }
    } catch (e) {
      console.warn('Auth validation failed:', e);
    }

    this.state.currentUser = null;
    const loginView = document.getElementById('view-login');
    if (loginView) loginView.classList.remove('hidden');
    return false;
  },

  updateUserUI(user) {
    if (!user) return;
    const initials = (user.full_name || user.username).split(' ').map(p => p[0]).join('').toUpperCase().slice(0, 2) || 'US';
    const initialsEl = document.getElementById('user-avatar-initials');
    if (initialsEl) initialsEl.textContent = initials;

    const nameEl = document.getElementById('user-display-name');
    if (nameEl) nameEl.textContent = user.full_name || user.username;

    const roleEl = document.getElementById('user-role-badge');
    if (roleEl) {
      roleEl.textContent = user.role.toUpperCase();
      if (user.role === 'admin') {
        roleEl.className = 'text-[9px] px-1.5 py-0.2 rounded font-mono font-bold uppercase bg-rose-500/15 text-rose-400 border border-rose-500/30';
      } else {
        roleEl.className = 'text-[9px] px-1.5 py-0.2 rounded font-mono font-bold uppercase bg-cyan-500/15 text-cyan-400 border border-cyan-500/30';
      }
    }

    const adminSection = document.getElementById('sidebar-admin-section');
    if (adminSection) {
      adminSection.classList.toggle('hidden', user.role !== 'admin');
    }
  },

  async handleLogin(e) {
    if (e) e.preventDefault();
    const uInput = document.getElementById('login-username');
    const pInput = document.getElementById('login-password');
    const rInput = document.getElementById('login-remember');
    const errAlert = document.getElementById('login-error-alert');
    const errMsg = document.getElementById('login-error-message');
    const submitBtn = document.getElementById('login-submit-btn');

    if (!uInput || !pInput) return;
    const username = uInput.value.trim();
    const password = pInput.value;
    const rememberMe = rInput ? rInput.checked : true;

    if (!username || !password) return;

    if (errAlert) errAlert.classList.add('hidden');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span>Verifying credentials...</span>';
    }

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, remember_me: rememberMe })
      });

      const data = await res.json();
      if (res.ok && data.status === 'ok') {
        this.state.authToken = data.token;
        if (rememberMe) {
          localStorage.setItem('vault_auth_token', data.token);
        } else {
          sessionStorage.setItem('vault_auth_token', data.token);
        }
        this.state.currentUser = data.user;
        this.updateUserUI(data.user);

        const loginView = document.getElementById('view-login');
        if (loginView) loginView.classList.add('hidden');

        // Initialize user-scoped state
        this.state.solvedChallenges.clear();
        this.initSolvedState();
        if (window.vaultTimer) {
          window.vaultTimer.loadInitialState();
        }
        await this.loadPlatforms();
        await this.loadChallenges();
        await this.loadInterviewTracks();
        await this.loadCourseCatalog();
        await this.loadCustomCourses();
        this.renderLibraryCatalog();
        this.renderDrillsHub();
        this.renderAllCourseTracks();

        if (data.user.role === 'admin') {
          this.loadAdminUsers();
        }
      } else {
        if (errAlert) {
          errAlert.classList.remove('hidden');
          if (errMsg) errMsg.textContent = data.detail || 'Invalid username or password.';
        }
      }
    } catch (err) {
      if (errAlert) {
        errAlert.classList.remove('hidden');
        if (errMsg) errMsg.textContent = 'Server connection failed. Please try again.';
      }
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span>Sign In to Vault</span><span>→</span>';
      }
    }
  },

  async logout() {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        headers: this.getAuthHeaders()
      });
    } catch (e) {}

    localStorage.removeItem('vault_auth_token');
    sessionStorage.removeItem('vault_auth_token');
    this.state.authToken = '';
    this.state.currentUser = null;
    this.state.solvedChallenges.clear();

    const loginView = document.getElementById('view-login');
    if (loginView) loginView.classList.remove('hidden');

    const adminSection = document.getElementById('sidebar-admin-section');
    if (adminSection) adminSection.classList.add('hidden');

    this.switchView('datascience');
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
    this.initPWA();
    this.initLoginParticles();

    this.bindSidebarNavigation();
    this.bindSubtabNavigation();
    this.bindSandboxEvents();

    const isAuthed = await this.checkAuth();
    if (!isAuthed) {
      return;
    }

    this.initSolvedState();
    await this.loadPlatforms();
    await this.loadChallenges();
    await this.loadInterviewTracks();
    await this.loadCourseCatalog();
    await this.loadCustomCourses();
    this.renderLibraryCatalog();
    this.renderDrillsHub();
    this.renderAllCourseTracks();

    if (this.state.currentUser && this.state.currentUser.role === 'admin') {
      this.loadAdminUsers();
    }

    if (this.state.challenges.length > 0) {
      await this.selectChallenge(this.state.challenges[0].id);
    }
  },

  // ── Challenge Completion Persistence ──────────────────────────────────────
  initSolvedState() {
    if (!this.state.currentUser) return;
    const uid = this.state.currentUser.id;
    const storageKey = `vault_u${uid}_solved_challenges`;

    try {
      const local = JSON.parse(localStorage.getItem(storageKey) || '[]');
      if (Array.isArray(local)) {
        local.forEach(id => this.state.solvedChallenges.add(id));
      }
    } catch (e) {
      console.warn('Could not read local solved challenges:', e);
    }

    // Sync with SQLite backend strictly for authenticated user
    fetch('/api/solved-challenges', { headers: this.getAuthHeaders() })
      .then(r => r.json())
      .then(data => {
        if (data && Array.isArray(data.solved_ids)) {
          this.state.solvedChallenges.clear();
          data.solved_ids.forEach(id => this.state.solvedChallenges.add(id));
          localStorage.setItem(storageKey, JSON.stringify(Array.from(this.state.solvedChallenges)));
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
        // Auto-close sidebar on mobile after navigation
        if (window.innerWidth < 768) {
          this.closeMobileSidebar();
        }
      });
    });
  },

  switchView(viewName) {
    // Pause all playing videos immediately across all tracks upon navigation
    this.pauseAllVideos();

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

    if (viewName === 'admin') {
      this.loadAdminUsers();
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
      'cyber_level1_foundations': '🌱 Cyber L1: Security Foundations',
      'cyber_level2_defensive': '⚡ Cyber L2: Defensive Security (OWASP)',
      'cyber_level3_advanced': '🔥 Cyber L3: Security Engineering (ATT&CK)',
      'cyber_level4_architecture': '🏛️ Cyber L4: Architecture & NIST CSF 2.0',
      'cyber_applied_mastery_pack': '🏆 Cyber Applied Mastery Pack',
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

  getAllTrackCourses(trackKey) {
    const track = this.state.courses ? this.state.courses[trackKey] : null;
    if (!track) return [];
    const currentLang = (this.state.courseLanguage && this.state.courseLanguage[trackKey]) ? this.state.courseLanguage[trackKey] : 'en';
    const langData = (track.languages && track.languages[currentLang]) ? track.languages[currentLang] : (track.languages ? track.languages['en'] : null);
    const goldenAnchors = track.golden_anchors || [];
    const languageCourses = (langData && langData.courses) ? langData.courses : [];
    
    const trackCustoms = (this.state.customCourses && this.state.customCourses[trackKey]) ? this.state.customCourses[trackKey] : [];
    const formattedCustomCourses = trackCustoms.map(c => {
      const cId = c.course_id || c.id;
      const isPersonal = (c.course_type === 'personal' || cId === 'personal');
      return {
        id: cId,
        course_id: cId,
        title: c.title || (isPersonal ? '📌 Personal' : 'Custom Playlist'),
        instructor: isPersonal ? 'My Saved Videos' : (c.title || 'Custom Playlist'),
        institution: 'Custom Ingestion',
        course_type: isPersonal ? 'personal' : (c.course_type || 'playlist'),
        isCustom: true,
        videos: c.videos || []
      };
    });

    return [...goldenAnchors, ...languageCourses, ...formattedCustomCourses];
  },

  async loadCustomCourses() {
    try {
      const res = await fetch('/api/custom-courses', { headers: this.getAuthHeaders() });
      if (!res.ok) return;
      const data = await res.json();
      const mapped = { ml: [], ds: [], cyber: [], dsa: [] };
      if (data && data.tracks) {
        Object.keys(data.tracks).forEach(t => {
          if (mapped[t]) {
            mapped[t] = data.tracks[t];
          }
        });
      }
      this.state.customCourses = mapped;
    } catch (e) {
      console.warn('Failed to load custom courses:', e);
    }
  },

  async handleAddCustomVideo(e, trackKey) {
    if (e) e.preventDefault();
    const inputEl = document.getElementById(`${trackKey}-custom-url-input`);
    const titleEl = document.getElementById(`${trackKey}-custom-title-input`);
    const statusEl = document.getElementById(`${trackKey}-custom-status`);
    const btnEl = document.getElementById(`${trackKey}-custom-submit-btn`);

    if (!inputEl) return;
    const url = inputEl.value.trim();
    if (!url) return;
    const customTitle = titleEl ? titleEl.value.trim() : '';

    if (btnEl) {
      btnEl.disabled = true;
      btnEl.innerHTML = '<span>Processing...</span>';
    }
    if (statusEl) {
      statusEl.classList.remove('hidden', 'text-rose-400', 'text-emerald-400');
      statusEl.classList.add('text-slate-400');
      statusEl.textContent = 'Extracting video / playlist metadata...';
    }

    try {
      const res = await fetch('/api/custom-courses/add', {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ track_key: trackKey, url: url, title: customTitle })
      });
      const data = await res.json();

      if (res.ok && data.status === 'ok') {
        inputEl.value = '';
        if (titleEl) titleEl.value = '';
        if (statusEl) {
          statusEl.classList.remove('text-slate-400', 'text-rose-400');
          statusEl.classList.add('text-emerald-400');
          const cType = data.type || data.course_type || 'personal';
          if (cType === 'playlist') {
            statusEl.textContent = `✓ Added playlist "${data.title}" (${(data.videos || []).length} lectures) as a new tab!`;
          } else {
            const vTitle = data.title || (data.video && data.video.title) || 'video';
            statusEl.textContent = `✓ Added "${vTitle}" to your 📌 Personal tab!`;
          }
          setTimeout(() => {
            if (statusEl) statusEl.classList.add('hidden');
          }, 5000);
        }

        await this.loadCustomCourses();
        this.selectCourse(trackKey, data.course_id);
      } else {
        if (res.status === 401) {
          if (statusEl) {
            statusEl.classList.remove('text-slate-400', 'text-emerald-400');
            statusEl.classList.add('text-rose-400');
            statusEl.textContent = '⚠️ Your session has expired. Please sign in again.';
          }
          this.handleSessionExpired('Your session has expired. Please sign in again to add custom videos.');
          return;
        }
        if (statusEl) {
          statusEl.classList.remove('text-slate-400', 'text-emerald-400');
          statusEl.classList.add('text-rose-400');
          statusEl.textContent = `⚠️ ${this.escapeHtml(data.detail || 'Could not add video or playlist URL.')}`;
        }
      }
    } catch (err) {
      if (statusEl) {
        statusEl.classList.remove('text-slate-400', 'text-emerald-400');
        statusEl.classList.add('text-rose-400');
        statusEl.textContent = '⚠️ Network error communicating with server.';
      }
    } finally {
      if (btnEl) {
        btnEl.disabled = false;
        btnEl.innerHTML = '<span>Save to Track</span><span>→</span>';
      }
    }
  },

  async renameCustomCourse(trackKey, courseId, currentTitle) {
    const cleanTitle = (currentTitle || '').replace(/^[📌📑\s]+/, '');
    const newTitle = prompt("Enter a custom name for this course / playlist:", cleanTitle);
    if (!newTitle || !newTitle.trim() || newTitle.trim() === cleanTitle) return;
    try {
      const res = await fetch('/api/custom-courses/rename', {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({
          track_key: trackKey,
          course_id: courseId,
          new_title: newTitle.trim()
        })
      });
      if (res.ok) {
        await this.loadCustomCourses();
        this.renderCourseTrack(trackKey);
      } else if (res.status === 401) {
        this.handleSessionExpired('Your session has expired. Please sign in again.');
      }
    } catch (e) {
      console.error("Failed to rename course:", e);
    }
  },

  async deleteCustomCourse(trackKey, courseId) {
    if (!confirm('Are you sure you want to remove this course and its videos from your vault?')) return;
    try {
      const res = await fetch(`/api/custom-courses/${courseId}?track_key=${trackKey}`, {
        method: 'DELETE',
        headers: this.getAuthHeaders()
      });
      if (res.ok) {
        await this.loadCustomCourses();
        if (this.state.activeCourseId[trackKey] === courseId) {
          const track = this.state.courses ? this.state.courses[trackKey] : null;
          if (track && track.golden_anchors && track.golden_anchors.length > 0) {
            this.state.activeCourseId[trackKey] = track.golden_anchors[0].id;
          }
          this.state.activeVideoIdx[trackKey] = 0;
        }
        this.renderCourseTrack(trackKey);
      } else if (res.status === 401) {
        this.handleSessionExpired('Your session has expired. Please sign in again.');
      }
    } catch (e) {
      console.error('Failed to delete custom course:', e);
    }
  },

  async removeVideoFromCustomCourse(trackKey, courseId, videoId) {
    try {
      const res = await fetch(`/api/custom-courses/${courseId}/video/${videoId}?track_key=${trackKey}`, {
        method: 'DELETE',
        headers: this.getAuthHeaders()
      });
      if (res.ok) {
        await this.loadCustomCourses();
        const curIdx = this.state.activeVideoIdx[trackKey] || 0;
        if (curIdx > 0) {
          this.state.activeVideoIdx[trackKey] = curIdx - 1;
        }
        this.renderCourseTrack(trackKey);
      } else if (res.status === 401) {
        this.handleSessionExpired('Your session has expired. Please sign in again.');
      }
    } catch (e) {
      console.error('Failed to remove video:', e);
    }
  },

  // ── PWA Mobile Install Engine ─────────────────────────────────────────────
  initPWA() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js')
        .then(reg => console.log('Career Vault ServiceWorker registered:', reg.scope))
        .catch(err => console.warn('ServiceWorker registration error:', err));
    }

    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      this.state.deferredInstallPrompt = e;
      const banner = document.getElementById('pwa-install-banner');
      if (banner && !sessionStorage.getItem('vault_pwa_dismissed')) {
        banner.classList.remove('hidden');
      }
    });

    window.addEventListener('appinstalled', () => {
      console.log('Career Vault PWA was installed successfully.');
      this.dismissPWA();
    });
  },

  installPWA() {
    const promptEvent = this.state.deferredInstallPrompt;
    if (!promptEvent) {
      alert('To install Career Vault on your phone:\n1. Tap Chrome menu (⋮)\n2. Tap "Install app" or "Add to Home screen".');
      return;
    }
    promptEvent.prompt();
    promptEvent.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('PWA installation accepted');
      }
      this.state.deferredInstallPrompt = null;
      this.dismissPWA();
    });
  },

  dismissPWA() {
    const banner = document.getElementById('pwa-install-banner');
    if (banner) banner.classList.add('hidden');
    try {
      sessionStorage.setItem('vault_pwa_dismissed', 'true');
    } catch (e) {}
  },

  // ── Login Cyber Particle Background Canvas ─────────────────────────────────
  loginParticlesAnimId: null,

  initLoginParticles() {
    const canvas = document.getElementById('login-particles-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    window.addEventListener('resize', () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    });

    const particles = [];
    const count = Math.min(45, Math.floor((width * height) / 28000));
    const colors = ['#10b981', '#38bdf8', '#fb7185', '#34d399', '#38bdf8'];

    for (let i = 0; i < count; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.6,
        vy: (Math.random() - 0.5) * 0.6,
        radius: Math.random() * 2 + 1,
        color: colors[Math.floor(Math.random() * colors.length)]
      });
    }

    let mouse = { x: -1000, y: -1000 };
    window.addEventListener('mousemove', (e) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    });

    const animate = () => {
      const loginView = document.getElementById('view-login');
      if (!loginView || loginView.classList.contains('hidden')) {
        this.loginParticlesAnimId = requestAnimationFrame(animate);
        return;
      }

      ctx.clearRect(0, 0, width, height);

      // Draw connections
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 130) {
            ctx.beginPath();
            ctx.strokeStyle = `rgba(16, 185, 129, ${(1 - dist / 130) * 0.2})`;
            ctx.lineWidth = 0.8;
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.stroke();
          }
        }
      }

      // Update & draw particles
      particles.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;

        const mdx = p.x - mouse.x;
        const mdy = p.y - mouse.y;
        const mdist = Math.sqrt(mdx * mdx + mdy * mdy);
        if (mdist < 100) {
          const angle = Math.atan2(mdy, mdx);
          p.x += Math.cos(angle) * 1.5;
          p.y += Math.sin(angle) * 1.5;
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.shadowColor = p.color;
        ctx.shadowBlur = 6;
        ctx.fill();
        ctx.shadowBlur = 0;
      });

      this.loginParticlesAnimId = requestAnimationFrame(animate);
    };

    if (this.loginParticlesAnimId) cancelAnimationFrame(this.loginParticlesAnimId);
    animate();
  },

  // ── Trilingual Structured Course Hub & Golden Anchors ──────────────────────
  async loadCourseCatalog() {
    try {
      ['ml', 'ds', 'cyber', 'dsa'].forEach(t => {
        const saved = localStorage.getItem('vault_course_lang_' + t);
        if (saved && ['en', 'hi', 'te'].includes(saved)) {
          this.state.courseLanguage[t] = saved;
        }
      });

      const res = await fetch('/api/courses');
      if (!res.ok) return;
      const data = await res.json();
      this.state.courses = data.tracks || {};
    } catch (e) {
      console.error('Failed to load course catalog:', e);
    }
  },

  renderAllCourseTracks() {
    ['ds', 'ml', 'cyber', 'dsa'].forEach(t => this.renderCourseTrack(t));
  },

  getYoutubeEmbedUrl(videoId, autoplay = false) {
    const origin = (typeof window !== 'undefined' && window.location && window.location.origin && window.location.origin !== 'null')
      ? encodeURIComponent(window.location.origin)
      : '';
    let url;
    if (videoId && videoId.startsWith('videoseries?list=')) {
      const listId = videoId.replace('videoseries?list=', '');
      url = `https://www.youtube-nocookie.com/embed/videoseries?list=${listId}&enablejsapi=1`;
    } else {
      url = `https://www.youtube-nocookie.com/embed/${videoId}?rel=0&enablejsapi=1`;
    }
    if (autoplay) url += '&autoplay=1';
    if (origin) url += `&origin=${origin}`;
    return url;
  },

  switchCourseLanguage(trackKey, langKey) {
    this.pauseAllVideos();
    if (!this.state.courseLanguage) this.state.courseLanguage = {};
    this.state.courseLanguage[trackKey] = langKey;
    try {
      localStorage.setItem('vault_course_lang_' + trackKey, langKey);
    } catch (e) {
      console.warn('Could not save course language to localStorage:', e);
    }

    // If currently selected course is not a golden anchor, switch to first course of new language
    const track = this.state.courses ? this.state.courses[trackKey] : null;
    if (track) {
      const isAnchor = (track.golden_anchors || []).some(a => a.id === this.state.activeCourseId[trackKey]);
      if (!isAnchor) {
        const langData = track.languages && track.languages[langKey];
        if (langData && langData.courses && langData.courses.length > 0) {
          this.state.activeCourseId[trackKey] = langData.courses[0].id;
          this.state.activeVideoIdx[trackKey] = 0;
        }
      }
    }

    this.renderCourseTrack(trackKey);
  },

  selectCourse(trackKey, courseId) {
    this.pauseAllVideos();
    if (!this.state.activeCourseId) this.state.activeCourseId = {};
    if (!this.state.activeVideoIdx) this.state.activeVideoIdx = {};
    this.state.activeCourseId[trackKey] = courseId;
    this.state.activeVideoIdx[trackKey] = 0;
    this.renderCourseTrack(trackKey);
  },

  selectCourseVideo(trackKey, idx) {
    if (!this.state.activeVideoIdx) this.state.activeVideoIdx = {};
    this.state.activeVideoIdx[trackKey] = idx;

    const allCourses = this.getAllTrackCourses(trackKey);
    const activeCourse = allCourses.find(c => c.id === this.state.activeCourseId[trackKey]) || allCourses[0];
    if (!activeCourse) return;
    const videos = activeCourse.videos || [];
    const v = videos[idx];
    if (!v) return;

    // Smooth theater update — pause all other videos first
    this.pauseAllVideos(`${trackKey}-theater-iframe`);
    const iframe = document.getElementById(`${trackKey}-theater-iframe`);
    if (iframe) {
      iframe.src = this.getYoutubeEmbedUrl(v.id, true);
    }

    const titleEl = document.getElementById(`${trackKey}-video-title`);
    if (titleEl) titleEl.textContent = v.title;

    const durEl = document.getElementById(`${trackKey}-video-dur`);
    if (durEl && v.duration) durEl.textContent = `⏱️ ${v.duration}`;

    const counterEl = document.getElementById(`${trackKey}-playlist-counter`);
    if (counterEl) counterEl.textContent = `Lecture ${idx + 1} of ${videos.length}`;

    const barEl = document.getElementById(`${trackKey}-playlist-progress-bar`);
    if (barEl) barEl.style.width = `${((idx + 1) / videos.length) * 100}%`;

    const ytLink = document.getElementById(`${trackKey}-yt-direct-link`);
    if (ytLink) {
      if (v.id.startsWith('videoseries')) {
        const listMatch = v.id.match(/list=([a-zA-Z0-9_-]+)/);
        ytLink.href = listMatch ? `https://www.youtube.com/playlist?list=${listMatch[1]}` : `https://www.youtube.com/`;
      } else {
        ytLink.href = `https://www.youtube.com/watch?v=${v.id}`;
      }
    }

    const prevBtn = document.getElementById(`${trackKey}-prev-btn`);
    if (prevBtn) {
      prevBtn.disabled = (idx === 0);
      prevBtn.style.opacity = (idx === 0) ? '0.35' : '1';
      prevBtn.style.cursor = (idx === 0) ? 'not-allowed' : 'pointer';
    }

    const nextBtn = document.getElementById(`${trackKey}-next-btn`);
    if (nextBtn) {
      nextBtn.disabled = (idx >= videos.length - 1);
      nextBtn.style.opacity = (idx >= videos.length - 1) ? '0.35' : '1';
      nextBtn.style.cursor = (idx >= videos.length - 1) ? 'not-allowed' : 'pointer';
    }

    // Highlight active playlist item
    const queue = document.getElementById(`${trackKey}-playlist-queue`);
    if (queue) {
      queue.querySelectorAll('.playlist-card').forEach((card, i) => {
        const isAct = (i === idx);
        card.classList.toggle('active-playlist-card', isAct);
        card.classList.toggle('bg-emerald-950/40', isAct);
        card.classList.toggle('border-emerald-500/60', isAct);
        card.classList.toggle('ring-1', isAct);
        card.classList.toggle('ring-emerald-400/50', isAct);
        const chip = card.querySelector('.playing-badge');
        if (chip) chip.style.display = isAct ? 'inline-flex' : 'none';
      });
      const activeCard = queue.querySelector(`.playlist-card[data-idx="${idx}"]`);
      if (activeCard) {
        activeCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }
  },

  prevCourseVideo(trackKey) {
    const cur = (this.state.activeVideoIdx && this.state.activeVideoIdx[trackKey]) || 0;
    if (cur > 0) {
      this.selectCourseVideo(trackKey, cur - 1);
    }
  },

  nextCourseVideo(trackKey) {
    const allCourses = this.getAllTrackCourses(trackKey);
    const activeCourse = allCourses.find(c => c.id === this.state.activeCourseId[trackKey]) || allCourses[0];
    if (!activeCourse) return;
    const videos = activeCourse.videos || [];
    const cur = (this.state.activeVideoIdx && this.state.activeVideoIdx[trackKey]) || 0;
    if (cur < videos.length - 1) {
      this.selectCourseVideo(trackKey, cur + 1);
    }
  },

  renderCourseTrack(trackKey) {
    const container = document.getElementById(`course-section-${trackKey}`);
    if (!container) return;
    if (!this.state.courses || !this.state.courses[trackKey]) {
      container.innerHTML = '<div class="p-8 text-center text-slate-400 font-mono text-xs">Loading course syllabus and video masterclasses...</div>';
      return;
    }

    const track = this.state.courses[trackKey];
    const currentLang = (this.state.courseLanguage && this.state.courseLanguage[trackKey]) ? this.state.courseLanguage[trackKey] : 'en';
    const langData = (track.languages && track.languages[currentLang]) ? track.languages[currentLang] : (track.languages ? track.languages['en'] : null);

    // Track Theme
    const themeMap = {
      'ml': {
        accent: '#a855f7',
        border: 'border-purple-500/30',
        bg: 'bg-purple-500/10',
        text: 'text-purple-300',
        badge: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
        pillActive: 'bg-purple-500/25 text-purple-200 border-purple-500/60 shadow-lg shadow-purple-500/15 ring-1 ring-purple-500/40',
        cardGlow: 'hover:border-purple-500/50'
      },
      'ds': {
        accent: '#38bdf8',
        border: 'border-cyan-500/30',
        bg: 'bg-cyan-500/10',
        text: 'text-cyan-300',
        badge: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
        pillActive: 'bg-cyan-500/25 text-cyan-200 border-cyan-500/60 shadow-lg shadow-cyan-500/15 ring-1 ring-cyan-500/40',
        cardGlow: 'hover:border-cyan-500/50'
      },
      'cyber': {
        accent: '#f43f5e',
        border: 'border-rose-500/30',
        bg: 'bg-rose-500/10',
        text: 'text-rose-300',
        badge: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
        pillActive: 'bg-rose-500/25 text-rose-200 border-rose-500/60 shadow-lg shadow-rose-500/15 ring-1 ring-rose-500/40',
        cardGlow: 'hover:border-rose-500/50'
      },
      'dsa': {
        accent: '#f59e0b',
        border: 'border-amber-500/30',
        bg: 'bg-amber-500/10',
        text: 'text-amber-300',
        badge: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
        pillActive: 'bg-amber-500/25 text-amber-200 border-amber-500/60 shadow-lg shadow-amber-500/15 ring-1 ring-amber-500/40',
        cardGlow: 'hover:border-amber-500/50'
      }
    };
    const tTheme = themeMap[trackKey] || themeMap['ml'];

    // All available courses for this track: Golden Anchors + Active Language Courses + Custom Courses
    const goldenAnchors = track.golden_anchors || [];
    const languageCourses = (langData && langData.courses) ? langData.courses : [];
    const allAvailableCourses = this.getAllTrackCourses(trackKey);

    // Determine currently active course
    let activeCourseId = this.state.activeCourseId ? this.state.activeCourseId[trackKey] : null;
    let activeCourse = allAvailableCourses.find(c => c.id === activeCourseId);
    if (!activeCourse) {
      activeCourse = goldenAnchors[0] || allAvailableCourses[0];
      if (activeCourse) {
        if (!this.state.activeCourseId) this.state.activeCourseId = {};
        this.state.activeCourseId[trackKey] = activeCourse.id;
      }
    }

    const videos = (activeCourse && activeCourse.videos && activeCourse.videos.length > 0)
      ? activeCourse.videos
      : [{ id: 'dQw4w9WgXcQ', title: activeCourse.title, duration: '' }];

    let currentVideoIdx = (this.state.activeVideoIdx && this.state.activeVideoIdx[trackKey]) || 0;
    if (currentVideoIdx >= videos.length) currentVideoIdx = 0;
    const activeVideo = videos[currentVideoIdx];

    // 1. Language Switcher Buttons
    const languages = [
      { id: 'en', flag: '🇬🇧', label: 'English', sub: 'Academic & Systems' },
      { id: 'hi', flag: '🇮🇳', label: 'Hindi', sub: 'Industrial Bootcamp' },
      { id: 'te', flag: '🇮🇳', label: 'Telugu', sub: 'Vernacular Intuition' }
    ];

    let langButtonsHtml = languages.map(lang => {
      const isSelected = lang.id === currentLang;
      const activeClass = isSelected
        ? tTheme.pillActive + ' font-bold'
        : 'bg-slate-900/80 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-white';
      return `
        <button 
          onclick="App.switchCourseLanguage('${trackKey}', '${lang.id}')"
          class="px-3 py-1.5 rounded-xl border text-xs flex items-center gap-2 transition-all cursor-pointer select-none ${activeClass}">
          <span class="text-base">${lang.flag}</span>
          <span class="leading-tight">${lang.label}</span>
          ${isSelected ? '<span class="text-emerald-400 text-xs font-bold">✓</span>' : ''}
        </button>
      `;
    }).join('');

    // 2. Course Shelf Tabs (Golden Anchors + Current Language Courses + Custom Courses)
    let courseTabsHtml = '';
    allAvailableCourses.forEach(c => {
      const isSelected = (c.id === activeCourse.id);
      const isAnchor = goldenAnchors.some(a => a.id === c.id);
      const isCustom = c.isCustom;
      const vidCount = (c.videos || []).length;
      
      let tabStyle = 'bg-slate-900/80 text-slate-300 border-slate-800 hover:border-slate-700 hover:text-white';
      if (isSelected) {
        tabStyle = isAnchor
          ? 'bg-amber-500/20 text-amber-200 border-amber-500/60 shadow-lg shadow-amber-500/10 ring-1 ring-amber-500/40 font-bold'
          : (isCustom ? 'bg-emerald-500/20 text-emerald-200 border-emerald-500/60 shadow-lg shadow-emerald-500/10 ring-1 ring-emerald-500/40 font-bold' : tTheme.pillActive + ' font-bold');
      }

      const icon = isAnchor ? '⭐' : (c.course_type === 'personal' ? '📌' : (isCustom ? '📑' : '🎓'));
      const escapedTitle = this.escapeHtml(c.title || '').replace(/'/g, "\\'");
      const renameBtn = isCustom
        ? `<button onclick="event.stopPropagation(); App.renameCustomCourse('${trackKey}', '${c.id}', '${escapedTitle}')" title="Rename Course/Playlist" class="p-0.5 rounded text-slate-400 hover:text-emerald-400 hover:bg-slate-800 transition">✏️</button>`
        : '';
      const deleteBtn = (isCustom && c.course_type !== 'personal')
        ? `<button onclick="event.stopPropagation(); App.deleteCustomCourse('${trackKey}', '${c.id}')" title="Delete playlist course" class="p-0.5 rounded text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition">✕</button>`
        : '';

      courseTabsHtml += `
        <button 
          onclick="App.selectCourse('${trackKey}', '${c.id}')"
          class="px-3.5 py-2 rounded-xl border text-xs flex items-center gap-2 transition-all cursor-pointer select-none flex-shrink-0 ${tabStyle}">
          <span>${icon}</span>
          <span class="truncate max-w-[220px] sm:max-w-xs">${this.escapeHtml(c.title)}</span>
          <span class="text-[10px] font-mono px-1.5 py-0.2 rounded-full ${isAnchor ? 'bg-amber-500/20 text-amber-300' : 'bg-slate-800 text-slate-400'}">
            ${vidCount} vids
          </span>
          ${renameBtn}
          ${deleteBtn}
        </button>
      `;
    });

    // 3. YouTube Playlist Queue Items
    let playlistItemsHtml = '';
    videos.forEach((v, i) => {
      const isPlaying = (i === currentVideoIdx);
      const cardActiveStyle = isPlaying
        ? 'active-playlist-card bg-emerald-950/40 border-emerald-500/60 ring-1 ring-emerald-400/50 shadow-md'
        : 'bg-slate-900/50 border-slate-800/80 hover:bg-slate-800/80 hover:border-slate-700';

      const removeVidBtn = (activeCourse.isCustom && activeCourse.course_type === 'personal')
        ? `<button onclick="event.stopPropagation(); App.removeVideoFromCustomCourse('${trackKey}', '${activeCourse.id}', '${v.id}')" title="Remove from Personal" class="p-1 rounded text-slate-500 hover:text-rose-400 hover:bg-slate-800 transition text-xs flex-shrink-0 ml-auto">✕</button>`
        : '';

      const isPlaylistId = v.id && v.id.startsWith('videoseries');
      const thumbUrl = isPlaylistId
        ? 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 60" fill="%230f172a"><rect width="100" height="60" fill="%230f172a"/><path d="M40 20 L65 30 L40 40 Z" fill="%2310b981"/><line x1="20" y1="15" x2="80" y2="15" stroke="%23334155" stroke-width="3"/><line x1="20" y1="45" x2="80" y2="45" stroke="%23334155" stroke-width="3"/></svg>'
        : `https://img.youtube.com/vi/${v.id}/mqdefault.jpg`;

      playlistItemsHtml += `
        <div 
          data-idx="${i}"
          onclick="App.selectCourseVideo('${trackKey}', ${i})"
          class="playlist-card group p-2.5 rounded-xl border flex items-start gap-3 transition-all cursor-pointer select-none ${cardActiveStyle}">
          
          <!-- Thumbnail with duration overlay -->
          <div class="relative w-28 h-16 rounded-lg overflow-hidden bg-black flex-shrink-0 border border-slate-800/80">
            <img 
              src="${thumbUrl}" 
              alt="${this.escapeHtml(v.title)}" 
              loading="lazy"
              class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              onerror="this.style.opacity='0.5'">
            ${v.duration ? `
              <span class="absolute bottom-1 right-1 px-1 py-0.2 rounded bg-black/85 text-[9px] font-mono text-slate-200 font-semibold">
                ${v.duration}
              </span>
            ` : ''}
            <div class="absolute inset-0 bg-black/20 group-hover:bg-transparent transition-colors"></div>
          </div>

          <!-- Title & Number -->
          <div class="flex-1 min-w-0 space-y-1">
            <div class="flex items-center gap-1.5 justify-between">
              <div class="flex items-center gap-1.5">
                <span class="text-[10px] font-mono font-bold ${isPlaying ? 'text-emerald-400' : 'text-slate-500'}">
                  #${i + 1}
                </span>
                <span class="playing-badge text-[9px] px-1.5 py-0.2 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-bold ${isPlaying ? 'inline-flex' : 'hidden'} items-center gap-1">
                  ▶ Playing
                </span>
              </div>
              ${removeVidBtn}
            </div>
            <h4 class="text-xs font-semibold leading-snug line-clamp-2 ${isPlaying ? 'text-white font-bold' : 'text-slate-300 group-hover:text-white'}">
              ${this.escapeHtml(v.title)}
            </h4>
          </div>
        </div>
      `;
    });

    // Action links for active course
    let courseLinksHtml = '';
    if (activeCourse.github_url) {
      courseLinksHtml += `
        <a href="${activeCourse.github_url}" target="_blank" class="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-xs font-semibold text-slate-200 hover:text-white flex items-center gap-1.5 transition-all">
          <span>💻</span> <span>GitHub Repo ↗</span>
        </a>
      `;
    }
    if (activeCourse.notes_url) {
      courseLinksHtml += `
        <a href="${activeCourse.notes_url}" target="_blank" class="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-xs font-semibold text-slate-200 hover:text-white flex items-center gap-1.5 transition-all">
          <span>📝</span> <span>Lecture Notes ↗</span>
        </a>
      `;
    }
    if (activeCourse.book_url) {
      courseLinksHtml += `
        <a href="${activeCourse.book_url}" target="_blank" class="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-xs font-semibold text-slate-200 hover:text-white flex items-center gap-1.5 transition-all">
          <span>📖</span> <span>Official Book ↗</span>
        </a>
      `;
    }
    if (activeCourse.playlist_url) {
      courseLinksHtml += `
        <a href="${activeCourse.playlist_url}" target="_blank" class="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-xs font-semibold text-slate-200 hover:text-white flex items-center gap-1.5 transition-all">
          <span>▶</span> <span>Full Playlist on YouTube ↗</span>
        </a>
      `;
    }

    // 4. Intermediate Technical Notes & Formulations
    let intermediateNotesHtml = '';
    if (track.intermediate_notes && track.intermediate_notes.length > 0) {
      intermediateNotesHtml = track.intermediate_notes.map((note, idx) => `
        <div class="glass-panel p-5 space-y-3 border border-slate-800/80 hover:border-slate-700 transition-all shadow-lg">
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              <span class="w-6 h-6 rounded-md ${tTheme.bg} ${tTheme.text} flex items-center justify-center text-xs font-mono font-bold">
                ${idx + 1}
              </span>
              <span class="px-2.5 py-0.5 rounded-full ${tTheme.bg} ${tTheme.text} text-[10px] font-mono font-semibold uppercase tracking-wider border ${tTheme.border}">
                ${note.tag || 'Systems Formulation'}
              </span>
            </div>
            <span class="text-[11px] text-slate-500 font-mono">${note.author || ''}</span>
          </div>

          <h4 class="text-sm md:text-base font-bold text-white tracking-tight">${note.title}</h4>

          <!-- Math / Formulation Block -->
          <div class="p-3 rounded-xl bg-slate-950/90 border border-slate-800 font-mono text-xs text-emerald-400 overflow-x-auto shadow-inner leading-relaxed select-all">
            ${note.math}
          </div>

          <!-- Deep Explanation Content -->
          <p class="text-xs text-slate-300 leading-relaxed">${note.content}</p>
        </div>
      `).join('');
    }

    // Full Assembled HTML
    container.innerHTML = `
      <!-- Track Header & Language Selector -->
      <div class="glass-panel p-5 md:p-6 space-y-4 border ${tTheme.border} bg-gradient-to-r ${tTheme.bg} via-slate-900/60 to-transparent shadow-xl">
        <div class="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <div class="space-y-1">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="px-2.5 py-0.5 rounded-full ${tTheme.badge} text-xs font-bold font-mono tracking-wider">
                ${track.badge}
              </span>
              <span class="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20 font-semibold">
                100% Free & Open-Access
              </span>
            </div>
            <h2 class="text-lg md:text-xl font-extrabold text-white tracking-tight">${track.title}</h2>
            <p class="text-xs text-slate-300 max-w-3xl leading-relaxed">${track.description}</p>
          </div>

          <!-- Trilingual Switcher Buttons -->
          <div class="space-y-1.5 w-full lg:w-auto flex-shrink-0">
            <div class="text-[10px] font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <span>🌐</span> <span>Select Lecture Language:</span>
            </div>
            <div class="flex flex-wrap items-center gap-2">
              ${langButtonsHtml}
            </div>
          </div>
        </div>

        <!-- Golden Anchor Guarantee Notification -->
        <div class="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center gap-2.5 text-xs text-amber-200">
          <span class="text-base flex-shrink-0">🔒</span>
          <span>
            <strong>Golden Anchors Guarantee:</strong> World-class benchmarks (Karpathy, Stanford, MIT, Striver) remain <strong>permanently pinned below</strong>, unaffected by language changes.
          </span>
        </div>
      </div>

      <!-- CUSTOM VIDEO & PLAYLIST INGESTION BAR -->
      <div class="custom-paste-container p-3.5 sm:p-4 bg-slate-900/60 rounded-2xl space-y-2.5">
        <div class="flex items-center justify-between gap-2 flex-wrap">
          <div class="flex items-center gap-2">
            <span class="text-emerald-400 text-base">➕</span>
            <h3 class="text-xs font-bold text-white tracking-wide uppercase">Add Your Custom Video or YouTube Playlist</h3>
          </div>
          <div class="flex items-center gap-2 text-[10px] text-slate-400 font-mono">
            <span class="custom-shelf-badge">Single Video → 📌 Personal</span>
            <span class="custom-shelf-badge">Playlist → 📑 New Course Tab</span>
          </div>
        </div>
        <form onsubmit="App.handleAddCustomVideo(event, '${trackKey}')" class="grid grid-cols-1 sm:grid-cols-12 gap-2">
          <div class="relative sm:col-span-7 w-full">
            <input 
              type="url" 
              id="${trackKey}-custom-url-input" 
              required 
              placeholder="Paste YouTube URL (e.g. https://www.youtube.com/watch?v=... or playlist?list=...)" 
              class="w-full pl-8 pr-3 py-2 rounded-xl bg-slate-950/90 border border-slate-800 text-xs text-slate-100 placeholder-slate-500 focus:border-emerald-500 focus:outline-none transition">
            <span class="absolute left-2.5 top-2.5 text-slate-500 text-xs">🔗</span>
          </div>
          <div class="relative sm:col-span-3 w-full">
            <input 
              type="text" 
              id="${trackKey}-custom-title-input" 
              placeholder="Custom Name / Title (optional)" 
              class="w-full pl-8 pr-3 py-2 rounded-xl bg-slate-950/90 border border-slate-800 text-xs text-slate-100 placeholder-slate-500 focus:border-emerald-500 focus:outline-none transition">
            <span class="absolute left-2.5 top-2.5 text-slate-500 text-xs">🏷️</span>
          </div>
          <button 
            type="submit" 
            id="${trackKey}-custom-submit-btn"
            class="sm:col-span-2 w-full px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 font-bold text-xs hover:brightness-110 flex items-center justify-center gap-1.5 transition flex-shrink-0 cursor-pointer shadow-md shadow-emerald-500/20">
            <span>Add to Track</span>
            <span>→</span>
          </button>
        </form>
        <div id="${trackKey}-custom-status" class="hidden text-[11px] font-mono"></div>
      </div>

      <!-- COURSE SHELF / TAB SELECTOR (YouTube Style Series Tabs) -->
      <div class="space-y-2">
        <div class="flex items-center justify-between">
          <div class="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <span>📺</span> <span>Select Course Series to Watch:</span>
          </div>
          <span class="text-[10px] font-mono text-slate-500">
            Click any course to load its full video playlist
          </span>
        </div>
        <div class="flex items-center gap-2.5 overflow-x-auto pb-2 scrollbar-none">
          ${courseTabsHtml}
        </div>
      </div>

      <!-- YOUTUBE THEATER WATCH VIEW (Main Player + Full Interactive Playlist Queue) -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        
        <!-- Left: Main Video Player & Video Info (7 cols on lg) -->
        <div class="lg:col-span-7 xl:col-span-8 space-y-4">
          
          <!-- Big 16:9 Theater Player Screen -->
          <div class="aspect-video w-full rounded-2xl overflow-hidden border border-slate-700/80 shadow-2xl bg-black relative">
            <iframe 
              id="${trackKey}-theater-iframe"
              class="w-full h-full"
              src="${this.getYoutubeEmbedUrl(activeVideo.id, false)}" 
              title="${activeVideo.title}" 
              frameborder="0" 
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
              allowfullscreen>
            </iframe>
          </div>

          <!-- Video Details & Player Controls -->
          <div class="glass-panel p-4 md:p-5 space-y-3.5 border border-slate-800/80 shadow-xl">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div class="space-y-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="px-2 py-0.5 rounded-full ${tTheme.badge} text-[10px] font-mono font-bold">
                    ${activeCourse.institution || activeCourse.instructor || 'Instructor'}
                  </span>
                  <span id="${trackKey}-video-dur" class="text-[11px] font-mono text-slate-400">
                    ⏱️ ${activeVideo.duration || activeCourse.runtime || ''}
                  </span>
                </div>
                <h3 id="${trackKey}-video-title" class="text-base md:text-lg font-bold text-white tracking-tight leading-snug">
                  ${activeVideo.title}
                </h3>
              </div>

              <!-- Quick Next / Previous Navigation Controls -->
              <div class="flex items-center gap-2 flex-shrink-0">
                <button 
                  id="${trackKey}-prev-btn"
                  onclick="App.prevCourseVideo('${trackKey}')"
                  ${currentVideoIdx === 0 ? 'disabled style="opacity:0.35;cursor:not-allowed;"' : 'style="cursor:pointer;"'}
                  class="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-xs font-bold text-slate-200 hover:text-white flex items-center gap-1.5 transition-all">
                  <span>⏮</span> <span>Prev</span>
                </button>
                <button 
                  id="${trackKey}-next-btn"
                  onclick="App.nextCourseVideo('${trackKey}')"
                  ${currentVideoIdx >= videos.length - 1 ? 'disabled style="opacity:0.35;cursor:not-allowed;"' : 'style="cursor:pointer;"'}
                  class="px-3.5 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 font-bold text-xs hover:brightness-110 flex items-center gap-1.5 transition-all">
                  <span>Next</span> <span>⏭</span>
                </button>
              </div>
            </div>

            <!-- Description & External Action Links -->
            <p class="text-xs text-slate-400 leading-relaxed pt-1 border-t border-slate-800/60">
              ${activeCourse.description}
            </p>

            <div class="flex flex-wrap items-center gap-2 pt-1">
              <a 
                id="${trackKey}-yt-direct-link"
                href="${activeVideo.id.startsWith('videoseries') ? `https://www.youtube.com/playlist?list=${(activeVideo.id.match(/list=([a-zA-Z0-9_-]+)/) || [])[1] || ''}` : `https://www.youtube.com/watch?v=${activeVideo.id}`}" 
                target="_blank" 
                class="px-3 py-1.5 rounded-lg bg-red-500/15 border border-red-500/30 text-red-300 hover:bg-red-500/25 text-xs font-semibold flex items-center gap-1.5 transition-all">
                <span>▶</span> <span>Watch on YouTube ↗</span>
              </a>
              ${courseLinksHtml}
            </div>
          </div>
        </div>

        <!-- Right: YouTube Full Video Playlist Drawer (5 cols on lg) -->
        <div class="lg:col-span-5 xl:col-span-4 space-y-2">
          
          <!-- Playlist Header & Telemetry -->
          <div class="glass-panel p-3.5 rounded-xl border border-slate-800/80 bg-slate-900/90 space-y-2">
            <div class="flex items-center justify-between gap-2">
              <div class="min-w-0">
                <div class="text-[10px] font-mono text-emerald-400 font-bold uppercase tracking-wider">
                  Full Playlist (${videos.length} Videos)
                </div>
                <h4 class="text-xs font-bold text-white truncate">
                  ${activeCourse.title}
                </h4>
              </div>
              <span id="${trackKey}-playlist-counter" class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700/60 flex-shrink-0">
                Video ${currentVideoIdx + 1} of ${videos.length}
              </span>
            </div>

            <!-- Visual Playlist Progress Bar -->
            <div class="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden border border-slate-800/60">
              <div 
                id="${trackKey}-playlist-progress-bar"
                class="h-1.5 rounded-full bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-400 transition-all duration-300" 
                style="width: ${((currentVideoIdx + 1) / videos.length) * 100}%">
              </div>
            </div>
          </div>

          <!-- Scrollable Full Video Queue (Like YouTube Playlist Sidebar) -->
          <div 
            id="${trackKey}-playlist-queue" 
            class="space-y-2 max-h-[300px] lg:max-h-[560px] overflow-y-auto pr-1"
            style="scrollbar-width: thin; scrollbar-color: #334155 #0b1120;">
            ${playlistItemsHtml}
          </div>
        </div>

      </div>

      <!-- SECTION 3: INTERMEDIATE TECHNICAL NOTES & FORMULATIONS -->
      <div class="space-y-4 pt-4 border-t border-slate-800/80">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-lg">📝</span>
            <div>
              <h3 class="text-sm font-bold text-white uppercase tracking-wider">Intermediate Systems Notes & Mathematical Derivations</h3>
              <p class="text-[11px] text-slate-400">Core theoretical principles, asymptotic rules, and equations to master alongside the video courses.</p>
            </div>
          </div>
          <span class="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-bold">
            Theory & Formulas
          </span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          ${intermediateNotesHtml}
        </div>
      </div>
    `;
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

    if (this.state.currentUser) {
      const storageKey = `vault_u${this.state.currentUser.id}_solved_challenges`;
      localStorage.setItem(storageKey, JSON.stringify(Array.from(this.state.solvedChallenges)));
    }

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
      headers: this.getAuthHeaders(),
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
        headers: this.getAuthHeaders(),
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
        if (this.state.currentUser) {
          const storageKey = `vault_u${this.state.currentUser.id}_solved_challenges`;
          localStorage.setItem(storageKey, JSON.stringify(Array.from(this.state.solvedChallenges)));
        }
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

  // ── Mobile Sidebar Toggle ─────────────────────────────────────────────────
  toggleMobileSidebar() {
    const sidebar = document.querySelector('.vault-sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const btn = document.getElementById('mobile-menu-btn');
    if (!sidebar || !overlay) return;
    const isOpen = sidebar.classList.contains('sidebar-open');
    sidebar.classList.toggle('sidebar-open', !isOpen);
    overlay.classList.toggle('sidebar-open', !isOpen);
    if (btn) btn.textContent = isOpen ? '☰' : '✕';
  },

  closeMobileSidebar() {
    const sidebar = document.querySelector('.vault-sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const btn = document.getElementById('mobile-menu-btn');
    if (sidebar) sidebar.classList.remove('sidebar-open');
    if (overlay) overlay.classList.remove('sidebar-open');
    if (btn) btn.textContent = '☰';
  },

  // ── Universal Single-Video Playback Engine (pause all others) ─────────────
  pauseAllVideos(exceptIframeId = null) {
    document.querySelectorAll('iframe').forEach(iframe => {
      if (exceptIframeId && (iframe.id === exceptIframeId || iframe === exceptIframeId)) return;
      if (iframe.contentWindow) {
        try {
          iframe.contentWindow.postMessage(
            JSON.stringify({ event: 'command', func: 'pauseVideo', args: [] }),
            '*'
          );
          iframe.contentWindow.postMessage(
            JSON.stringify({ event: 'command', func: 'pauseVideo', args: '' }),
            '*'
          );
        } catch (e) { /* cross-origin, safe to ignore */ }
      }
    });
  },

  // ── Admin Control Panel Methods ───────────────────────────────────────────
  async loadAdminUsers() {
    if (!this.state.currentUser || this.state.currentUser.role !== 'admin') return;
    try {
      const res = await fetch('/api/admin/users', { headers: this.getAuthHeaders() });
      if (!res.ok) return;
      const data = await res.json();
      this.state.adminUsers = data.users || [];
      this.renderAdminUsersTable(this.state.adminUsers);
      this.renderAdminStats(this.state.adminUsers);
    } catch (e) {
      console.warn('Failed to load admin users:', e);
    }
  },

  renderAdminStats(users) {
    const total = users.length;
    const activeStudents = users.filter(u => u.role === 'student' && u.is_active).length;
    const totalSec = users.reduce((acc, u) => acc + (u.focus_seconds || 0), 0);
    const totalHours = (totalSec / 3600).toFixed(1);
    const totalSolves = users.reduce((acc, u) => acc + (u.solved_count || 0), 0);

    const tEl = document.getElementById('admin-stat-total-users');
    if (tEl) tEl.textContent = total;
    const aEl = document.getElementById('admin-stat-active-users');
    if (aEl) aEl.textContent = activeStudents;
    const hEl = document.getElementById('admin-stat-total-hours');
    if (hEl) hEl.textContent = `${totalHours}h`;
    const sEl = document.getElementById('admin-stat-total-solves');
    if (sEl) sEl.textContent = totalSolves;
    const badgeEl = document.getElementById('admin-user-count-badge');
    if (badgeEl) badgeEl.textContent = `${total} Users`;
  },

  renderAdminUsersTable(users) {
    const tbody = document.getElementById('admin-user-table-body');
    if (!tbody) return;

    if (users.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="py-6 text-center text-slate-500 font-mono">No provisioned users found.</td></tr>';
      return;
    }

    tbody.innerHTML = users.map(u => {
      const isSelf = this.state.currentUser && this.state.currentUser.id === u.id;
      const roleBadge = u.role === 'admin'
        ? '<span class="px-2 py-0.5 rounded-full bg-rose-500/15 text-rose-300 font-mono text-[10px] font-bold border border-rose-500/30">👑 Admin</span>'
        : '<span class="px-2 py-0.5 rounded-full bg-cyan-500/15 text-cyan-300 font-mono text-[10px] font-bold border border-cyan-500/30">🎓 Student</span>';
      
      const statusBadge = u.is_active
        ? '<span class="px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 font-mono text-[10px] font-bold border border-emerald-500/30">✓ Active</span>'
        : '<span class="px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono text-[10px] font-bold border border-slate-700">✕ Disabled</span>';

      const hours = ((u.focus_seconds || 0) / 3600).toFixed(1);
      const createdStr = (u.created_at || '').slice(0, 10);

      return `
        <tr class="hover:bg-slate-900/40 transition-colors">
          <td class="py-3 px-3">
            <div class="flex items-center gap-2.5">
              <div class="w-7 h-7 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-[11px] text-white">
                ${(u.full_name || u.username).slice(0, 2).toUpperCase()}
              </div>
              <div>
                <div class="font-bold text-white leading-tight">${u.full_name || u.username} ${isSelf ? '<span class="text-[10px] text-emerald-400 font-mono">(You)</span>' : ''}</div>
                <div class="text-[11px] text-slate-400 font-mono">@${u.username}</div>
              </div>
            </div>
          </td>
          <td class="py-3 px-3">${roleBadge}</td>
          <td class="py-3 px-3">${statusBadge}</td>
          <td class="py-3 px-3 font-mono font-bold ${u.solved_count > 0 ? 'text-emerald-400' : 'text-slate-500'}">
            ${u.solved_count || 0} / 312
          </td>
          <td class="py-3 px-3 font-mono text-slate-300">${hours} hrs</td>
          <td class="py-3 px-3 font-mono text-[11px] text-slate-500">${createdStr}</td>
          <td class="py-3 px-3 text-right">
            <div class="flex items-center justify-end gap-1.5">
              <button 
                onclick="App.openResetPasswordModal(${u.id}, '${u.username}')" 
                class="px-2 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-[11px] font-semibold transition-all cursor-pointer" 
                title="Reset Password">
                🔑 Reset
              </button>
              ${!isSelf ? `
                <button 
                  onclick="App.toggleUserStatus(${u.id}, ${u.is_active ? 1 : 0})" 
                  class="px-2 py-1 rounded-lg ${u.is_active ? 'bg-amber-500/15 text-amber-300 border-amber-500/30 hover:bg-amber-500/25' : 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/25'} border text-[11px] font-semibold transition-all cursor-pointer">
                  ${u.is_active ? 'Disable' : 'Enable'}
                </button>
                <button 
                  onclick="App.deleteUser(${u.id}, '${u.username}')" 
                  class="px-2 py-1 rounded-lg bg-rose-500/15 text-rose-300 border border-rose-500/30 hover:bg-rose-500/25 text-[11px] font-semibold transition-all cursor-pointer" 
                  title="Delete User">
                  🗑️
                </button>
              ` : ''}
            </div>
          </td>
        </tr>
      `;
    }).join('');
  },

  filterAdminUsers(q) {
    const query = (q || '').toLowerCase().trim();
    if (!query) {
      this.renderAdminUsersTable(this.state.adminUsers);
      return;
    }
    const filtered = this.state.adminUsers.filter(u => 
      (u.username || '').toLowerCase().includes(query) ||
      (u.full_name || '').toLowerCase().includes(query) ||
      (u.role || '').toLowerCase().includes(query)
    );
    this.renderAdminUsersTable(filtered);
  },

  openCreateUserModal() {
    const m = document.getElementById('modal-create-user');
    const err = document.getElementById('create-user-error');
    const uInput = document.getElementById('create-username');
    const fInput = document.getElementById('create-fullname');
    const pInput = document.getElementById('create-password');
    if (uInput) uInput.value = '';
    if (fInput) fInput.value = '';
    if (pInput) pInput.value = '';
    if (err) err.classList.add('hidden');
    if (m) m.classList.remove('hidden');
    if (uInput) setTimeout(() => uInput.focus(), 80);
  },

  closeCreateUserModal() {
    const m = document.getElementById('modal-create-user');
    if (m) m.classList.add('hidden');
  },

  async handleCreateUser(e) {
    if (e) e.preventDefault();
    const unameInput = document.getElementById('create-username');
    const fnameInput = document.getElementById('create-fullname');
    const pwdInput = document.getElementById('create-password');
    const roleInput = document.getElementById('create-role');
    const err = document.getElementById('create-user-error');
    const submitBtn = document.getElementById('create-user-submit-btn');

    if (!unameInput || !pwdInput) return;
    const uname = unameInput.value.trim().toLowerCase();
    const fname = fnameInput ? fnameInput.value.trim() : '';
    const pwd = pwdInput.value;
    const role = roleInput ? roleInput.value : 'student';

    if (!uname || !pwd) {
      if (err) {
        err.classList.remove('hidden');
        err.textContent = 'Please fill out username and password.';
      }
      return;
    }

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span>Provisioning...</span>';
    }
    if (err) err.classList.add('hidden');

    try {
      const res = await fetch('/api/admin/users/create', {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ username: uname, full_name: fname, password: pwd, role: role })
      });
      const data = await res.json();
      if (res.ok && data.status === 'ok') {
        unameInput.value = '';
        if (fnameInput) fnameInput.value = '';
        pwdInput.value = '';
        this.closeCreateUserModal();
        await this.loadAdminUsers();
        alert(`✓ Account @${uname} has been successfully provisioned into the vault!`);
      } else {
        if (res.status === 401) {
          this.closeCreateUserModal();
          this.handleSessionExpired('Your administrator session has expired. Please sign in again.');
          return;
        }
        if (err) {
          err.classList.remove('hidden');
          err.textContent = data.detail || 'Failed to create user.';
        }
      }
    } catch (e) {
      if (err) {
        err.classList.remove('hidden');
        err.textContent = 'Network error provisioning user.';
      }
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span>Provision Account</span>';
      }
    }
  },

  openResetPasswordModal(userId, username) {
    const m = document.getElementById('modal-reset-password');
    const uTarget = document.getElementById('reset-target-username');
    const idInput = document.getElementById('reset-target-user-id');
    const pwdInput = document.getElementById('reset-new-password');
    const err = document.getElementById('reset-password-error');

    if (uTarget) uTarget.textContent = `@${username}`;
    if (idInput) idInput.value = userId;
    if (pwdInput) pwdInput.value = '';
    if (err) err.classList.add('hidden');
    if (m) m.classList.remove('hidden');
  },

  closeResetPasswordModal() {
    const m = document.getElementById('modal-reset-password');
    if (m) m.classList.add('hidden');
  },

  async handleResetPassword(e) {
    if (e) e.preventDefault();
    const userId = document.getElementById('reset-target-user-id').value;
    const newPassword = document.getElementById('reset-new-password').value;
    const err = document.getElementById('reset-password-error');

    try {
      const res = await fetch(`/api/admin/users/${userId}/reset-password`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ new_password: newPassword })
      });
      const data = await res.json();
      if (res.ok && data.status === 'ok') {
        this.closeResetPasswordModal();
        alert('Password reset successfully. Active sessions revoked.');
      } else {
        if (err) {
          err.classList.remove('hidden');
          err.textContent = data.detail || 'Failed to reset password.';
        }
      }
    } catch (e) {
      if (err) {
        err.classList.remove('hidden');
        err.textContent = 'Network error resetting password.';
      }
    }
  },

  async toggleUserStatus(userId, currentStatus) {
    try {
      const res = await fetch(`/api/admin/users/${userId}/status`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ is_active: !currentStatus })
      });
      if (res.ok) {
        this.loadAdminUsers();
      }
    } catch (e) {
      console.warn('Toggle status error:', e);
    }
  },

  async deleteUser(userId, username) {
    if (!confirm(`Are you sure you want to delete user @${username}? This action cannot be undone.`)) return;
    try {
      const res = await fetch(`/api/admin/users/${userId}`, {
        method: 'DELETE',
        headers: this.getAuthHeaders()
      });
      if (res.ok) {
        this.loadAdminUsers();
      }
    } catch (e) {
      console.warn('Delete user error:', e);
    }
  },

  openChangePasswordModal() {
    const m = document.getElementById('modal-change-password');
    const err = document.getElementById('change-password-error');
    if (err) err.classList.add('hidden');
    if (m) m.classList.remove('hidden');
  },

  closeChangePasswordModal() {
    const m = document.getElementById('modal-change-password');
    if (m) m.classList.add('hidden');
  },

  async handleChangePassword(e) {
    if (e) e.preventDefault();
    const oldPwd = document.getElementById('change-old-password').value;
    const newPwd = document.getElementById('change-new-password').value;
    const err = document.getElementById('change-password-error');

    try {
      const res = await fetch('/api/auth/change-password', {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ old_password: oldPwd, new_password: newPwd })
      });
      const data = await res.json();
      if (res.ok && data.status === 'ok') {
        this.closeChangePasswordModal();
        alert('Your password has been changed successfully.');
      } else {
        if (err) {
          err.classList.remove('hidden');
          err.textContent = data.detail || 'Password change failed.';
        }
      }
    } catch (e) {
      if (err) {
        err.classList.remove('hidden');
        err.textContent = 'Network error changing password.';
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

  // ── Global YouTube Cross-Player Audio Isolation Engine ─────────────────────
  // Listens for YouTube iframe state changes and automatically pauses all other videos
  window.addEventListener('message', (event) => {
    try {
      let data = event.data;
      if (typeof data === 'string') {
        try {
          data = JSON.parse(data);
        } catch (e) {
          return;
        }
      }
      if (!data || typeof data !== 'object') return;

      // Check for YouTube playerState = 1 (PLAYING) or 3 (BUFFERING)
      const isPlaying = 
        (data.event === 'onStateChange' && (data.info === 1 || data.info === '1' || data.info === 3)) ||
        (data.event === 'infoDelivery' && data.info && (data.info.playerState === 1 || data.info.playerState === '1'));

      if (isPlaying && event.source) {
        document.querySelectorAll('iframe').forEach(iframe => {
          if (iframe.contentWindow && iframe.contentWindow !== event.source) {
            try {
              iframe.contentWindow.postMessage(JSON.stringify({ event: 'command', func: 'pauseVideo', args: [] }), '*');
              iframe.contentWindow.postMessage(JSON.stringify({ event: 'command', func: 'pauseVideo', args: '' }), '*');
            } catch (err) {}
          }
        });
      }
    } catch (err) {
      // Cross-origin safe
    }
  });
