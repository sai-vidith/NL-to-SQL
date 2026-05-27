import React, { useState, useEffect } from 'react';
import { 
  Database, 
  Send, 
  History as HistoryIcon, 
  Bookmark, 
  LogOut, 
  Menu, 

  X, 
  Play, 
  Download, 
  Lock, 
  Mail, 
  User as UserIcon, 
  Check, 
  Copy, 
  Sparkles, 
  AlertCircle,
  HelpCircle
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  LineChart as ReChartsLineChart, 
  Line, 
  PieChart as ReChartsPieChart, 
  Pie, 
  Cell 
} from 'recharts';


const API_BASE = '/api/v1';

// Types
interface UserProfile {
  id: string;
  username: string;
  email: string;
  role: string;
  created_at: string;
}

interface QueryResponse {
  id: string;
  question: string;
  intent: string;
  generated_sql: string;
  columns: string[];
  rows: any[][];
  row_count: number;
  execution_time_ms: number;
  summary: string;
  chart_config: {
    chart_type: 'bar' | 'line' | 'pie' | 'doughnut' | 'horizontalBar' | 'none';
    labels: string[];
    datasets: Array<{ label: string; data: number[] }>;
    title: string;
    x_label?: string;
    y_label?: string;
  } | null;
  session_id: string;
  created_at: string;
}

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [activePage, setActivePage] = useState<string>('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Form states
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');

  // Query Workspace States
  const [question, setQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState<QueryResponse[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [copiedQueryId, setCopiedQueryId] = useState<string | null>(null);
  const [activeChartType, setActiveChartType] = useState<string>('bar');
  
  // Bookmarking state
  const [saveName, setSaveName] = useState('');
  const [saveDesc, setSaveDesc] = useState('');
  const [activeBookmarkId, setActiveBookmarkId] = useState<string | null>(null);

  // History & Saved list states
  const [historyItems, setHistoryItems] = useState<any[]>([]);
  const [savedQueries, setSavedQueries] = useState<any[]>([]);

  // Check login state at startup
  useEffect(() => {
    fetchUserProfile();
  }, [isAuthenticated]);

  const fetchUserProfile = async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/me`);
      if (res.ok) {
        const data = await res.json();
        setUser(data);
        setIsAuthenticated(true);
      } else {
        setUser(null);
        setIsAuthenticated(false);
      }
    } catch {
      setUser(null);
      setIsAuthenticated(false);
    }
  };


  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {

        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      
      const data = await res.json();
      if (res.ok) {
        setIsAuthenticated(true);
        setActivePage('dashboard');
      } else {
        setError(data.error || data.detail || 'Login failed');
      }
    } catch (err) {
      setError('Connection failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password })
      });
      
      const data = await res.json();
      if (res.ok) {
        // Automatically log in
        const loginRes = await fetch(`${API_BASE}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        if (loginRes.ok) {
          setIsAuthenticated(true);
          setActivePage('dashboard');
        }
      } else {
        setError(data.error || data.detail || 'Registration failed');
      }
    } catch (err) {
      setError('Connection failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    // Clear cookies by calling logout or simply setting state
    try {
      await fetch(`${API_BASE}/auth/logout`, { method: 'POST' });
    } catch {}
    
    // Clear the client cookie locally by setting expiry
    document.cookie = "nexus_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    setIsAuthenticated(false);
    setUser(null);
  };


  // Submit Natural Language Query
  const submitQuestion = async (e?: React.FormEvent, customQuestion?: string) => {
    if (e) e.preventDefault();
    const queryText = customQuestion || question;
    if (!queryText.trim()) return;

    setLoading(true);
    setError(null);
    if (!customQuestion) setQuestion('');
    
    // Switch to query console view to present output conversational flow
    setActivePage('query');

    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          question: queryText,
          session_id: currentSessionId
        })
      });
      
      const data = await res.json();
      if (res.ok) {
        setChatHistory(prev => [data, ...prev]);
        setCurrentSessionId(data.session_id);
        if (data.chart_config) {
          setActiveChartType(data.chart_config.chart_type === 'none' ? 'bar' : data.chart_config.chart_type);
        }
      } else {
        setError(data.error || data.detail || 'Failed to process question');
      }
    } catch {
      setError('Network request timed out or was rejected.');
    } finally {
      setLoading(false);
    }
  };

  // Load history list
  const loadHistory = async () => {
    try {
      const res = await fetch(`${API_BASE}/query/history`);
      if (res.ok) {
        const data = await res.json();
        setHistoryItems(data.items || []);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Load bookmarked queries
  const loadSavedQueries = async () => {
    try {
      const res = await fetch(`${API_BASE}/saved-queries`);
      if (res.ok) {
        const data = await res.json();
        setSavedQueries(data || []);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Trigger loads on page change
  useEffect(() => {

    if (!isAuthenticated) return;
    if (activePage === 'history') loadHistory();
    if (activePage === 'saved') loadSavedQueries();
  }, [activePage, isAuthenticated]);

  const saveQuery = async (queryId: string) => {
    if (!saveName.trim()) return;
    try {
      const res = await fetch(`${API_BASE}/saved-queries`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: saveName,
          description: saveDesc,
          query_id: queryId
        })
      });
      if (res.ok) {
        setSaveName('');
        setSaveDesc('');
        setActiveBookmarkId(null);
        alert('Query successfully bookmarked!');
      }
    } catch {
      alert('Error bookmarking query.');
    }
  };


  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedQueryId(id);
    setTimeout(() => setCopiedQueryId(null), 2000);
  };

  // Direct suggestion queries
  const suggestions = [
    { text: "Show total revenue this month", category: "Sales", icon: "💰" },
    { text: "Top 10 customers by order value", category: "Customers", icon: "👥" },
    { text: "Monthly sales trend for 2025", category: "Sales", icon: "📈" },
    { text: "Revenue breakdown by payment method", category: "Finance", icon: "💳" }
  ];

  if (!isAuthenticated) {

    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="glass-panel w-full max-w-md rounded-2xl overflow-hidden shadow-glass border border-white/10">
          <div className="p-8 text-center bg-gradient-to-r from-primary/10 to-secondary/10 border-b border-white/5">
            <div className="inline-flex p-3 bg-primary/20 rounded-2xl mb-4 border border-primary/30">
              <Database className="w-8 h-8 text-primary animate-pulse" />
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white">NEXUS</h1>
            <p className="text-sm text-slate-400 mt-1">Enterprise NL-to-SQL Analytics</p>
          </div>

          <div className="p-8">
            <div className="flex gap-2 p-1 bg-background-deep/60 rounded-xl mb-6 border border-white/5">
              <button 
                onClick={() => setAuthMode('login')}
                className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all ${authMode === 'login' ? 'bg-primary text-white shadow-lg' : 'text-slate-400 hover:text-white'}`}
              >
                Log In
              </button>
              <button 
                onClick={() => setAuthMode('register')}
                className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all ${authMode === 'register' ? 'bg-primary text-white shadow-lg' : 'text-slate-400 hover:text-white'}`}
              >
                Register
              </button>
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-950/40 border border-red-500/30 rounded-xl flex items-center gap-2 text-red-300 text-sm">
                <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={authMode === 'login' ? handleLogin : handleRegister} className="space-y-4">
              {authMode === 'register' && (
                <div className="relative">
                  <span className="absolute inset-y-0 left-3 flex items-center text-slate-400">
                    <UserIcon className="w-4 h-4" />
                  </span>
                  <input 
                    type="text" 
                    placeholder="Username" 
                    value={username} 
                    onChange={e => setUsername(e.target.value)}
                    className="w-full glass-input pl-10 pr-4 py-3 rounded-xl text-sm" 
                    required 
                  />
                </div>
              )}

              <div className="relative">
                <span className="absolute inset-y-0 left-3 flex items-center text-slate-400">
                  <Mail className="w-4 h-4" />
                </span>
                <input 
                  type="email" 
                  placeholder="Corporate Email" 
                  value={email} 
                  onChange={e => setEmail(e.target.value)}
                  className="w-full glass-input pl-10 pr-4 py-3 rounded-xl text-sm" 
                  required 
                />
              </div>

              <div className="relative">
                <span className="absolute inset-y-0 left-3 flex items-center text-slate-400">
                  <Lock className="w-4 h-4" />
                </span>
                <input 
                  type="password" 
                  placeholder="Password" 
                  value={password} 
                  onChange={e => setPassword(e.target.value)}
                  className="w-full glass-input pl-10 pr-4 py-3 rounded-xl text-sm" 
                  required 
                />
              </div>

              <button 
                type="submit" 
                disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-primary to-secondary hover:brightness-110 active:scale-95 transition-all text-white font-semibold rounded-xl text-sm mt-6 shadow-lg shadow-primary/20 flex justify-center items-center gap-2"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <span>{authMode === 'login' ? 'Access Nexus Console' : 'Initialize Account'}</span>
                    <Sparkles className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-background-deep text-slate-100 overflow-hidden">
      {/* Sidebar Navigation */}
      <aside 
        className={`glass-panel border-y-0 border-l-0 border-r border-white/5 transition-all duration-300 z-30 flex flex-col shrink-0 ${
          sidebarOpen ? 'w-64' : 'w-0 -translate-x-full md:w-20 md:translate-x-0'
        }`}
      >
        {/* Brand */}
        <div className="p-6 flex items-center gap-3 border-b border-white/5 bg-background-sidebar/30">
          <div className="p-2 bg-gradient-to-r from-primary to-secondary rounded-xl">
            <Database className="w-5 h-5 text-white" />
          </div>
          {sidebarOpen && (
            <div>
              <span className="font-extrabold tracking-wider text-white">NEXUS</span>
              <div className="text-[10px] text-slate-400 font-semibold tracking-widest uppercase">Analytics Console</div>
            </div>
          )}
        </div>

        {/* Navigation list */}
        <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
          {[
            { id: 'dashboard', label: 'Dashboard', icon: Sparkles },
            { id: 'query', label: 'NL Console', icon: Send },
            { id: 'history', label: 'Search History', icon: HistoryIcon },
            { id: 'saved', label: 'Saved Queries', icon: Bookmark },
          ].map(item => {

            const Icon = item.icon;
            const active = activePage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActivePage(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all text-sm font-semibold ${
                  active 
                    ? 'bg-gradient-to-r from-primary to-secondary text-white shadow-lg shadow-primary/10' 
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                {sidebarOpen && <span>{item.label}</span>}
              </button>
            );
          })}
        </nav>

        {/* User profile drawer footer */}
        <div className="p-4 border-t border-white/5 bg-background-sidebar/35 flex flex-col gap-2">
          {sidebarOpen && user && (
            <div className="px-2 py-1 mb-2">
              <div className="text-sm font-bold text-white leading-tight truncate">{user.username}</div>
              <div className="text-xs text-slate-400 truncate">{user.email}</div>
            </div>
          )}
          <button 
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border border-red-500/20 text-red-400 hover:bg-red-500/10 transition-all text-xs font-bold"
          >
            <LogOut className="w-4 h-4" />
            {sidebarOpen && <span>Exit Console</span>}
          </button>
        </div>
      </aside>

      {/* Main Container */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* Top Header */}
        <header className="h-16 border-b border-white/5 px-6 flex items-center justify-between shrink-0 bg-background-deep/40 backdrop-blur-md sticky top-0 z-20">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-white/5"
            >
              {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
            <h2 className="text-lg font-bold text-white capitalize">{activePage.replace('-', ' ')}</h2>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="text-xs text-slate-400 bg-white/5 px-3 py-1.5 rounded-full border border-white/5 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
              <span>Operational API</span>
            </div>
          </div>
        </header>

        {/* Content Body */}
        <div className="flex-1 p-6 md:p-8 space-y-8">
          
          {/* DASHBOARD PAGE */}
          {activePage === 'dashboard' && (
            <div className="space-y-8 animate-fadeIn">
              {/* Header Widget */}
              <div className="p-8 rounded-2xl glass-panel relative overflow-hidden flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                <div className="space-y-2 relative z-10">
                  <h1 className="text-3xl font-extrabold text-white">Ask anything. Analyze instantly.</h1>
                  <p className="text-slate-400 max-w-xl text-sm">
                    Access our secure warehouse using plain conversational queries. Nexus parses intent, creates optimized query scripts, and structures graphics.
                  </p>
                </div>
                <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-primary/10 to-transparent pointer-events-none" />
              </div>

              {/* Suggestions Grid */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold tracking-widest text-slate-400 uppercase">Suggested Prompts</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {suggestions.map((item, idx) => (
                    <button
                      key={idx}
                      onClick={(e) => submitQuestion(e, item.text)}
                      className="text-left p-5 rounded-xl glass-card flex flex-col justify-between h-36"
                    >
                      <span className="text-3xl">{item.icon}</span>
                      <div className="space-y-1">
                        <div className="text-sm text-slate-200 font-semibold leading-snug line-clamp-2">{item.text}</div>
                        <span className="text-[10px] font-bold text-primary tracking-wider uppercase">{item.category}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Direct query input bar */}
              <form onSubmit={submitQuestion} className="space-y-2">
                <h3 className="text-sm font-bold tracking-widest text-slate-400 uppercase">Enter custom question</h3>
                <div className="relative flex items-center">
                  <input
                    type="text"
                    placeholder="e.g. List top 5 sellers by revenue last month..."
                    value={question}
                    onChange={e => setQuestion(e.target.value)}
                    className="w-full glass-input pl-6 pr-24 py-4 rounded-2xl text-base shadow-lg"
                  />
                  <button
                    type="submit"
                    disabled={loading}
                    className="absolute right-3 px-5 py-2.5 bg-gradient-to-r from-primary to-secondary rounded-xl hover:brightness-110 active:scale-95 text-white text-sm font-bold transition-all shadow-md flex items-center gap-2"
                  >
                    <span>Analyze</span>
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* QUERY WORKSPACE CONSOLE */}
          {activePage === 'query' && (
            <div className="space-y-8 animate-fadeIn">
              {/* Floating entry input */}
              <form onSubmit={submitQuestion} className="relative flex items-center">
                <input
                  type="text"
                  placeholder="Ask a follow-up or new analytics query..."
                  value={question}
                  onChange={e => setQuestion(e.target.value)}
                  className="w-full glass-input pl-6 pr-24 py-4 rounded-2xl text-base shadow-lg"
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="absolute right-3 px-5 py-2.5 bg-gradient-to-r from-primary to-secondary rounded-xl hover:brightness-110 text-white text-sm font-bold transition-all flex items-center gap-2"
                >
                  {loading ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <>
                      <span>Ask</span>
                      <Send className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>

              {chatHistory.length === 0 ? (
                <div className="p-12 text-center glass-panel rounded-2xl border border-white/5">
                  <HelpCircle className="w-12 h-12 text-slate-500 mx-auto mb-4 animate-bounce" />
                  <h3 className="text-lg font-bold text-white">Console Idle</h3>
                  <p className="text-slate-400 text-sm mt-1">Submit a question above to start the analytics engine.</p>
                </div>
              ) : (
                <div className="space-y-8">
                  {chatHistory.map((item) => (
                    <div key={item.id} className="glass-panel p-6 md:p-8 rounded-2xl border border-white/5 space-y-6">
                      
                      {/* NL Question bubble */}
                      <div className="flex items-start gap-4">
                        <div className="p-2.5 bg-primary/20 border border-primary/30 rounded-xl text-primary shrink-0">
                          <UserIcon className="w-5 h-5" />
                        </div>
                        <div className="space-y-1">
                          <div className="text-xs text-slate-400 font-bold uppercase tracking-wider">User Query</div>
                          <div className="text-lg font-semibold text-white leading-tight">{item.question}</div>
                        </div>
                      </div>

                      <hr className="border-white/5" />

                      {/* Engine Output */}
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                        
                        {/* Summary & SQL block */}
                        <div className="space-y-6">
                          <div className="space-y-2">
                            <div className="text-xs text-slate-400 font-bold uppercase tracking-wider">Executive Summary</div>
                            <div className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">{item.summary}</div>
                          </div>

                          {/* SQL code block */}
                          <div className="space-y-2">
                            <div className="flex justify-between items-center">
                              <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">Generated Query Script</span>
                              <button 
                                onClick={() => copyToClipboard(item.generated_sql, item.id)}
                                className="text-xs text-primary hover:text-white transition-colors flex items-center gap-1.5"
                              >
                                {copiedQueryId === item.id ? (
                                  <>
                                    <Check className="w-3.5 h-3.5" />
                                    <span>Copied</span>
                                  </>
                                ) : (
                                  <>
                                    <Copy className="w-3.5 h-3.5" />
                                    <span>Copy SQL</span>
                                  </>
                                )}
                              </button>
                            </div>
                            <pre className="p-4 bg-slate-950/65 rounded-xl border border-white/5 text-xs text-cyan-400 overflow-x-auto font-mono">
                              {item.generated_sql}
                            </pre>
                          </div>

                          {/* Quick export / Bookmark actions */}
                          <div className="flex items-center gap-3">
                            <a
                              href={`${API_BASE}/export/${item.id}/csv`}
                              target="_blank"
                              rel="noreferrer"
                              className="px-4 py-2 bg-white/5 border border-white/10 hover:bg-white/10 rounded-xl text-xs font-semibold flex items-center gap-2"
                            >
                              <Download className="w-3.5 h-3.5" />
                              <span>CSV</span>
                            </a>
                            <a
                              href={`${API_BASE}/export/${item.id}/excel`}
                              target="_blank"
                              rel="noreferrer"
                              className="px-4 py-2 bg-white/5 border border-white/10 hover:bg-white/10 rounded-xl text-xs font-semibold flex items-center gap-2"
                            >
                              <Download className="w-3.5 h-3.5" />
                              <span>Excel</span>
                            </a>

                            <button
                              onClick={() => {
                                setActiveBookmarkId(activeBookmarkId === item.id ? null : item.id);
                                setSaveName(`Query ${item.intent}`);
                              }}
                              className="px-4 py-2 bg-white/5 border border-white/10 hover:bg-white/10 rounded-xl text-xs font-semibold flex items-center gap-2 text-secondary"
                            >
                              <Bookmark className="w-3.5 h-3.5" />
                              <span>Bookmark</span>
                            </button>
                          </div>

                          {/* Bookmark form block */}
                          {activeBookmarkId === item.id && (
                            <div className="p-4 bg-white/5 border border-white/10 rounded-xl space-y-3 animate-fadeIn">
                              <div className="text-xs font-bold text-slate-300">Bookmark configurations</div>
                              <input
                                type="text"
                                placeholder="Query Name"
                                value={saveName}
                                onChange={e => setSaveName(e.target.value)}
                                className="w-full glass-input px-3 py-2 rounded-lg text-xs"
                              />
                              <input
                                type="text"
                                placeholder="Description (optional)"
                                value={saveDesc}
                                onChange={e => setSaveDesc(e.target.value)}
                                className="w-full glass-input px-3 py-2 rounded-lg text-xs"
                              />
                              <div className="flex gap-2">
                                <button
                                  onClick={() => saveQuery(item.id)}
                                  className="px-3 py-1.5 bg-secondary text-white text-xs font-bold rounded-lg"
                                >
                                  Save Bookmark
                                </button>
                                <button
                                  onClick={() => setActiveBookmarkId(null)}
                                  className="px-3 py-1.5 bg-white/5 text-slate-300 text-xs rounded-lg"
                                >
                                  Cancel
                                </button>
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Visual graphic chart display */}
                        <div className="space-y-6">
                          <div className="flex justify-between items-center">
                            <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">Visual Graphic representation</span>
                            {item.chart_config && (
                              <div className="flex bg-white/5 border border-white/10 p-0.5 rounded-lg">
                                {['bar', 'line', 'pie'].map(t => (
                                  <button
                                    key={t}
                                    onClick={() => setActiveChartType(t)}
                                    className={`px-2 py-1 rounded text-[10px] font-bold uppercase transition-all ${
                                      activeChartType === t ? 'bg-primary text-white' : 'text-slate-400 hover:text-white'
                                    }`}
                                  >
                                    {t}
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>

                          <div className="h-64 bg-slate-950/45 rounded-2xl border border-white/5 p-4 flex items-center justify-center">
                            {item.chart_config && item.row_count > 0 ? (
                              <ResponsiveContainer width="100%" height="100%">
                                {activeChartType === 'bar' ? (
                                  <BarChart data={item.chart_config.labels.map((l, idx) => ({
                                    label: l,
                                    value: item.chart_config?.datasets[0].data[idx] || 0
                                  }))}>
                                    <XAxis dataKey="label" stroke="#cbd5e1" fontSize={10} tickLine={false} />
                                    <YAxis stroke="#cbd5e1" fontSize={10} tickLine={false} />
                                    <Tooltip contentStyle={{ background: '#0c0f2b', border: '1px solid rgba(255,255,255,0.1)' }} />
                                    <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
                                  </BarChart>
                                ) : activeChartType === 'line' ? (
                                  <ReChartsLineChart data={item.chart_config.labels.map((l, idx) => ({
                                    label: l,
                                    value: item.chart_config?.datasets[0].data[idx] || 0
                                  }))}>
                                    <XAxis dataKey="label" stroke="#cbd5e1" fontSize={10} tickLine={false} />
                                    <YAxis stroke="#cbd5e1" fontSize={10} tickLine={false} />
                                    <Tooltip contentStyle={{ background: '#0c0f2b', border: '1px solid rgba(255,255,255,0.1)' }} />
                                    <Line type="monotone" dataKey="value" stroke="#ec4899" strokeWidth={2.5} activeDot={{ r: 6 }} />
                                  </ReChartsLineChart>
                                ) : (
                                  <ReChartsPieChart>
                                    <Pie
                                      data={item.chart_config.labels.map((l, idx) => ({
                                        name: l,
                                        value: item.chart_config?.datasets[0].data[idx] || 0
                                      }))}
                                      cx="50%"
                                      cy="50%"
                                      outerRadius={80}
                                      fill="#8884d8"
                                      dataKey="value"
                                      label={({ name }) => (name || '').substring(0, 10)}
                                    >
                                      {item.chart_config.labels.map((_, idx) => (
                                        <Cell key={`cell-${idx}`} fill={['#6366f1', '#a855f7', '#ec4899', '#06b6d4'][idx % 4]} />
                                      ))}
                                    </Pie>
                                    <Tooltip contentStyle={{ background: '#0c0f2b', border: '1px solid rgba(255,255,255,0.1)' }} />
                                  </ReChartsPieChart>
                                )}
                              </ResponsiveContainer>
                            ) : (
                              <div className="text-slate-500 text-sm flex flex-col items-center gap-2">
                                <HelpCircle className="w-8 h-8 opacity-40" />
                                <span>No chart configuration recommended for this query schema.</span>
                              </div>
                            )}
                          </div>
                        </div>

                      </div>

                      {/* Raw query output table */}
                      <div className="space-y-2">
                        <div className="text-xs text-slate-400 font-bold uppercase tracking-wider">Raw Output Records ({item.row_count})</div>
                        <div className="overflow-x-auto rounded-xl border border-white/5 bg-slate-950/20 max-h-64">
                          <table className="w-full text-left text-xs border-collapse">
                            <thead>
                              <tr className="bg-slate-900/50 border-b border-white/5 text-slate-300">
                                {item.columns.map(col => (
                                  <th key={col} className="p-3.5 font-bold capitalize">{col.replace('_', ' ')}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {item.rows.slice(0, 50).map((row, rIdx) => (
                                <tr key={rIdx} className="border-b border-white/5 hover:bg-white/[0.02] text-slate-300 transition-colors">
                                  {row.map((val, cIdx) => (
                                    <td key={cIdx} className="p-3.5 font-mono">{val !== null ? String(val) : 'NULL'}</td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          {item.row_count > 50 && (
                            <div className="p-3 text-center text-[10px] text-slate-500 font-semibold uppercase tracking-wider bg-slate-900/30">
                              Displaying first 50 records. Download full Excel/CSV file to view remaining {item.row_count - 50} outputs.
                            </div>
                          )}
                        </div>
                      </div>

                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* SEARCH HISTORY PAGE */}
          {activePage === 'history' && (
            <div className="space-y-6 animate-fadeIn">
              <div className="overflow-x-auto rounded-2xl border border-white/5 glass-panel">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="bg-slate-950/25 border-b border-white/5 text-slate-300">
                      <th className="p-4 font-bold">Time</th>
                      <th className="p-4 font-bold">NL Question</th>
                      <th className="p-4 font-bold">Category</th>
                      <th className="p-4 font-bold">Out Rows</th>
                      <th className="p-4 font-bold">Metrics</th>
                      <th className="p-4 font-bold">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historyItems.map((item) => (
                      <tr key={item.id} className="border-b border-white/5 hover:bg-white/[0.01] transition-all">
                        <td className="p-4 text-xs text-slate-400">
                          {new Date(item.created_at).toLocaleString()}
                        </td>
                        <td className="p-4 font-semibold text-slate-200">
                          {item.question}
                        </td>
                        <td className="p-4">
                          <span className="px-2.5 py-1 bg-primary/10 border border-primary/20 text-primary text-[10px] rounded-full font-bold uppercase tracking-wider">
                            {item.intent}
                          </span>
                        </td>
                        <td className="p-4 font-mono text-xs">{item.row_count}</td>
                        <td className="p-4 text-xs text-slate-400 font-mono">
                          {item.execution_time_ms.toFixed(1)}ms
                        </td>
                        <td className="p-4">
                          <button
                            onClick={() => submitQuestion(undefined, item.question)}
                            className="p-1.5 hover:bg-primary/20 border border-transparent hover:border-primary/30 rounded-lg text-primary transition-all"
                          >
                            <Play className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                    {historyItems.length === 0 && (
                      <tr>
                        <td colSpan={6} className="p-12 text-center text-slate-500">
                          No history items found.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* SAVED BOOKMARKS PAGE */}
          {activePage === 'saved' && (
            <div className="space-y-6 animate-fadeIn">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {savedQueries.map((item) => (
                  <div key={item.id} className="glass-panel p-6 rounded-2xl border border-white/5 flex flex-col justify-between h-52">
                    <div className="space-y-2">
                      <div className="flex justify-between items-start">
                        <h4 className="text-base font-bold text-white truncate pr-4">{item.name}</h4>
                        <span className="px-2 py-0.5 bg-secondary/20 border border-secondary/30 text-secondary text-[9px] rounded font-bold uppercase tracking-wider">
                          Bookmark
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 line-clamp-2">{item.description || 'No description provided.'}</p>
                      <pre className="p-3 bg-slate-950/50 rounded-lg text-[10px] text-cyan-400 font-mono truncate">
                        {item.sql_query}
                      </pre>
                    </div>

                    <div className="flex justify-between items-center mt-4">
                      <button
                        onClick={() => submitQuestion(undefined, item.nl_question)}
                        className="px-4 py-2 bg-gradient-to-r from-primary to-secondary text-white text-xs font-bold rounded-xl flex items-center gap-1.5"
                      >
                        <Play className="w-3 h-3" />
                        <span>Run Query</span>
                      </button>
                    </div>
                  </div>
                ))}
                {savedQueries.length === 0 && (
                  <div className="col-span-full p-12 text-center text-slate-500">
                    No bookmarked queries found.
                  </div>
                )}
              </div>
            </div>
          )}



        </div>
      </main>
    </div>
  );
}
