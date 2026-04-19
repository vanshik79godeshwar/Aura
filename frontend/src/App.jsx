import React, { useState, useEffect, useRef } from 'react';
import { 
  Send, 
  Database, 
  Sun, 
  Moon, 
  Upload, 
  Terminal,
  Layers,
  CheckCircle2,
  FileSpreadsheet,
  Cpu,
  PanelRightClose,
  PanelRightOpen,
  Zap,
  FileText,
  X,
  Info,
  User,
  BookOpen
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import * as XLSX from 'xlsx';
import Plotly from 'plotly.js-dist-min';

// ─── Vite-safe Plotly renderer ───────────────────────────────────────────────
function PlotlyChart({ data, layout, isDark }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !data?.length) return;

    const mergedLayout = {
      ...layout,
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      font: { family: 'Inter, sans-serif', color: isDark ? '#a1a1aa' : '#52525b', size: 12 },
      margin: { l: 50, r: 20, t: 50, b: 50 },
      height: 360,
      autosize: true,
      colorway: ['#2563EB', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'],
      xaxis: { ...layout?.xaxis, gridcolor: isDark ? '#27272a' : '#f4f4f5', linecolor: isDark ? '#3f3f46' : '#e4e4e7' },
      yaxis: { ...layout?.yaxis, gridcolor: isDark ? '#27272a' : '#f4f4f5', linecolor: isDark ? '#3f3f46' : '#e4e4e7' },
    };

    Plotly.newPlot(containerRef.current, data, mergedLayout, {
      displayModeBar: false,
      responsive: true,
    });

    return () => {
      if (containerRef.current) Plotly.purge(containerRef.current);
    };
  }, [data, layout, isDark]);

  return <div ref={containerRef} className="w-full" style={{ minHeight: 360 }} />;
}


const API_BASE = 'http://localhost:8000';

// ─── Info Modal (Docs + Profile combined) ───────────────────────────────────
function InfoModal({ onClose }) {
  const [tab, setTab] = useState('architect');
  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-white/10 rounded-3xl shadow-2xl w-full max-w-2xl mx-6 overflow-hidden"
      >
        <div className="flex items-center justify-between px-8 py-5 border-b border-zinc-100 dark:border-white/5">
          <div className="flex gap-1">
            {[{id:'architect', label:'Architect', icon: User}, {id:'docs', label:'Reference', icon: BookOpen}].map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${tab === t.id ? 'bg-black text-white dark:bg-blue-600' : 'opacity-40 hover:opacity-80'}`}
              >
                <t.icon className="w-3.5 h-3.5" />{t.label}
              </button>
            ))}
          </div>
          <button onClick={onClose} className="p-2 rounded-xl hover:bg-zinc-100 dark:hover:bg-white/5 transition-colors">
            <X className="w-4 h-4 opacity-40" />
          </button>
        </div>

        <div className="p-10 overflow-y-auto max-h-[70vh]">
          {tab === 'architect' ? (
            <div className="space-y-8">
              <div>
                <h1 className="text-4xl font-instrument font-bold tracking-tight dark:text-white">Vanshik Godeshwar</h1>
                <p className="text-blue-500 text-xs font-black mt-2 tracking-[0.25em] uppercase">Enterprise AI Architect</p>
              </div>
              <p className="text-[0.95rem] leading-8 text-zinc-600 dark:text-zinc-400">
                Vanshik Godeshwar is a pre-final year Computer Science undergraduate at <strong className="text-zinc-900 dark:text-white">SVNIT, Surat</strong>. 
                A high-ranking competitive programmer (<strong className="text-zinc-900 dark:text-white">Candidate Master on Codeforces, 5★ on CodeChef</strong>), 
                he specializes in distributed systems and scalable backend architecture. Project Aura is an exploration into the 
                <em> Supervisor-Specialist Agentic Pattern</em>, built to bridge the gap between complex data schemas and 
                human-centric insights.
              </p>
              <div className="grid grid-cols-3 gap-4">
                {[
                  { label: 'Codeforces', value: 'Candidate Master' },
                  { label: 'CodeChef', value: '5★ Rated' },
                  { label: 'Institution', value: 'SVNIT Surat' }
                ].map(item => (
                  <div key={item.label} className="p-5 rounded-2xl bg-zinc-50 dark:bg-white/5 border border-zinc-100 dark:border-white/5">
                    <div className="text-[9px] font-black uppercase tracking-widest opacity-30 mb-1">{item.label}</div>
                    <div className="text-sm font-bold dark:text-white">{item.value}</div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-8">
              <h1 className="text-4xl font-instrument font-bold tracking-tight dark:text-white">Technical Reference</h1>
              <div className="space-y-6 text-[0.95rem] leading-8 text-zinc-600 dark:text-zinc-400">
                <p>Aura Platinum is a zero-latency, multi-agent orchestration engine designed for structural data reasoning. It removes the barrier between complex database schemas and strategic decision-making.</p>
                <div className="grid grid-cols-2 gap-4">
                  {[
                    { label: 'Backend', value: 'Python · FastAPI · LangGraph' },
                    { label: 'Database', value: 'DuckDB (Persistent)' },
                    { label: 'Frontend', value: 'React · Vite · Tailwind v4' },
                    { label: 'Intelligence', value: 'Groq · Llama 3.1 8B' }
                  ].map(item => (
                    <div key={item.label} className="p-5 rounded-2xl bg-zinc-50 dark:bg-white/5 border border-zinc-100 dark:border-white/5">
                      <div className="text-[9px] font-black uppercase tracking-widest opacity-30 mb-1">{item.label}</div>
                      <div className="text-sm font-bold dark:text-white">{item.value}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}

// ─── Main App ────────────────────────────────────────────────────────────────
function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'System online. **AURA Executive Intelligence** is stabilized. How can I assist your strategic analysis today?' }
  ]);
  const [input, setInput] = useState('');
  const [isDark, setIsDark] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]); // [{name, size, status}]
  const [executedSteps, setExecutedSteps] = useState([]);
  const [isPanelOpen, setIsPanelOpen] = useState(true);
  const [lastPlan, setLastPlan] = useState('');
  const [showInfo, setShowInfo] = useState(false);
  
  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, executedSteps]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    setMessages(prev => [...prev, { role: 'user', content: input }]);
    setIsLoading(true);
    setInput('');
    setExecutedSteps([]);
    setLastPlan('');

    try {
      const response = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: input, active_upload: uploadedFiles[uploadedFiles.length - 1]?.name || '' })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // keep incomplete last line
        
        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const payload = JSON.parse(line);
            if (payload.type === 'step') {
              setExecutedSteps(prev => {
                const set = new Set(prev);
                set.add(payload.content);
                return [...set];
              });
            } else if (payload.type === 'final') {
              // viz is already a dict object (not a string) - fixed serialization
              setMessages(prev => [...prev, { 
                role: 'assistant', 
                content: payload.response || 'Analysis complete.',
                data: payload.data,
                viz: payload.viz,   // already parsed dict, no JSON.parse needed
                plan: payload.plan
              }]);
              setLastPlan(payload.plan || '');
              setIsLoading(false);
              setExecutedSteps(prev => [...prev, 'COMPLETE']);
            }
          } catch (e) { /* skip malformed chunks */ }
        }
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: '**Mesh Error:** The intelligence backend is unreachable. Is FastAPI running?' }]);
      setIsLoading(false);
    }
  };

  const exportToExcel = (data, filename = 'Aura_Export') => {
    const ws = XLSX.utils.json_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Data');
    XLSX.writeFile(wb, `${filename}.xlsx`);
  };

  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;
    e.target.value = ''; // reset so same file can be re-uploaded

    for (const file of files) {
      const sizeKB = (file.size / 1024).toFixed(1);
      // Add pending entry
      setUploadedFiles(prev => [...prev, { name: file.name, size: sizeKB, status: 'uploading' }]);

      const formData = new FormData();
      formData.append('file', file);
      
      try {
        const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: formData });
        if (!res.ok) throw new Error('Server rejected upload');
        await res.json();
        setUploadedFiles(prev => prev.map(f => f.name === file.name ? { ...f, status: 'ready' } : f));
      } catch (err) {
        setUploadedFiles(prev => prev.map(f => f.name === file.name ? { ...f, status: 'error' } : f));
      }
    }
  };

  const removeFile = async (name) => {
    setUploadedFiles(prev => prev.filter(f => f.name !== name));
    try {
      await fetch(`${API_BASE}/delete/${encodeURIComponent(name)}`, { method: 'DELETE' });
    } catch (e) {
      console.error("Failed to delete file from backend:", e);
    }
  };

  const AGENT_STEPS = ['STRATEGIC ROUTING', 'LOGIC DECOMPOSITION', 'EXECUTION VALIDATION', 'INSIGHT SYNTHESIS'];

  return (
    <div className={`h-screen overflow-hidden flex ${isDark ? 'dark bg-zinc-950 text-white' : 'bg-white text-zinc-900'} transition-colors duration-300`}>

      {/* ── LEFT SIDEBAR ── */}
      <aside className={`w-64 flex-shrink-0 flex flex-col border-r ${isDark ? 'bg-black border-white/5' : 'bg-zinc-50 border-zinc-200'} z-50`}>
        {/* Logo */}
        <div className="px-8 pt-8 pb-6">
          <h1 className="text-3xl font-instrument font-bold tracking-tighter">AURA</h1>
          <p className="text-[10px] font-bold uppercase tracking-widest opacity-30 mt-1">Intelligence Mesh 3.0</p>
        </div>

        {/* File Upload Zone */}
        <div className="px-6 flex-1 overflow-hidden flex flex-col">
          <div className="mb-3 text-[9px] font-black uppercase tracking-widest opacity-25">Data Room</div>

          <button
            onClick={() => fileInputRef.current?.click()}
            className={`w-full flex items-center justify-between px-4 py-3 rounded-xl border-2 border-dashed ${
              isDark ? 'border-zinc-800 hover:border-blue-500 hover:bg-blue-500/5' : 'border-zinc-200 hover:border-blue-600 hover:bg-blue-50/50'
            } transition-all group mb-4`}
          >
            <span className="text-xs font-semibold">Upload CSV / Excel</span>
            <Upload className="w-4 h-4 opacity-30 group-hover:text-blue-500 group-hover:opacity-100 transition-all" />
          </button>
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            onChange={handleFileUpload}
            accept=".csv, .xlsx, .xls"
            multiple
          />

          {/* File Inventory */}
          <div className="flex-1 overflow-y-auto no-scrollbar space-y-2">
            <AnimatePresence>
              {uploadedFiles.map((file) => (
                <motion.div
                  key={file.name}
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className={`p-3 rounded-xl border ${isDark ? 'bg-white/[0.03] border-white/5' : 'bg-white border-zinc-200'} shadow-sm`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <FileText className="w-3.5 h-3.5 mt-0.5 text-blue-500 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-[11px] font-semibold truncate" title={file.name}>{file.name}</p>
                      <p className="text-[9px] opacity-30 mt-0.5">{file.size} KB</p>
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      {file.status === 'uploading' && (
                        <div className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse" />
                      )}
                      {file.status === 'ready' && (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                      )}
                      {file.status === 'error' && (
                        <div className="w-2 h-2 rounded-full bg-red-500" />
                      )}
                      <button onClick={() => removeFile(file.name)} className="opacity-20 hover:opacity-60 transition-opacity ml-1">
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                  <div className={`mt-2 text-[9px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-md inline-block ${
                    file.status === 'ready' ? 'bg-emerald-500/10 text-emerald-500' :
                    file.status === 'uploading' ? 'bg-yellow-500/10 text-yellow-500' :
                    'bg-red-500/10 text-red-500'
                  }`}>
                    {file.status === 'ready' ? 'Ready' : file.status === 'uploading' ? 'Ingesting…' : 'Failed'}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>

        {/* Bottom Controls */}
        <div className="px-6 pb-8 space-y-2 mt-4">
          <button
            onClick={() => setShowInfo(true)}
            className={`w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border ${isDark ? 'border-zinc-800 hover:bg-white/5' : 'border-zinc-200 hover:bg-zinc-100'} transition-all text-[10px] font-bold uppercase tracking-widest opacity-50 hover:opacity-100`}
          >
            <Info className="w-3.5 h-3.5" />
            About / Docs
          </button>
          <button
            onClick={() => setIsDark(!isDark)}
            className={`w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border ${isDark ? 'border-zinc-800 hover:bg-white/5' : 'border-zinc-200 hover:bg-zinc-100'} transition-all text-[10px] font-bold uppercase tracking-widest`}
          >
            {isDark ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
            {isDark ? 'Light Mode' : 'Dark Mode'}
          </button>
        </div>
      </aside>

      {/* ── MAIN CONTENT ── */}
      <div className="flex-1 flex overflow-hidden relative">

        {/* Chat Column */}
        <main className="flex-1 flex flex-col h-full overflow-hidden">
          <div className="flex-1 w-full max-w-3xl mx-auto px-8 flex flex-col h-full relative">
            
            {/* Header */}
            <div className="h-16 flex items-center justify-between flex-shrink-0">
              <div className="flex items-center gap-3 text-[10px] font-bold tracking-[0.2em] opacity-30 uppercase">
                <Terminal className="w-3 h-3" />
                <span>Aura Matrix 3.0</span>
              </div>
              <button
                onClick={() => setIsPanelOpen(!isPanelOpen)}
                className={`p-2 rounded-lg hover:bg-zinc-100 dark:hover:bg-white/5 transition-colors opacity-40 hover:opacity-100`}
                title="Toggle Intelligence Trail"
              >
                {isPanelOpen ? <PanelRightClose className="w-4 h-4" /> : <PanelRightOpen className="w-4 h-4" />}
              </button>
            </div>

            {/* Message Stream */}
            <div className="flex-1 overflow-y-auto pb-40 no-scrollbar">
              <AnimatePresence>
                {messages.map((msg, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex flex-col mb-10 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
                  >
                    <div className={msg.role === 'user' ? 'max-w-[85%]' : 'w-full'}>

                      {/* Role label */}
                      <div className={`px-2 py-1 mb-2 text-[9px] font-black uppercase tracking-widest opacity-20 ${msg.role === 'user' ? 'text-right' : ''}`}>
                        {msg.role}
                      </div>

                      {/* Bubble */}
                      <div className={`px-7 py-5 rounded-3xl text-[0.93rem] leading-7 prose prose-sm max-w-none ${msg.role === 'user'
                        ? 'bg-zinc-900 text-white dark:bg-blue-600 shadow-2xl prose-invert'
                        : `border ${isDark ? 'border-white/5 bg-white/[0.01] prose-invert' : 'border-zinc-200 bg-zinc-50/80'}`
                      }`}>
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                      </div>

                      {/* Plotly Chart */}
                      {msg.viz && msg.viz.data && (
                        <motion.div
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          className={`mt-6 rounded-3xl border overflow-hidden ${isDark ? 'border-white/5 bg-white/[0.02]' : 'border-zinc-200 bg-white'} shadow-lg p-2`}
                        >
                          <PlotlyChart
                            data={msg.viz.data}
                            layout={msg.viz.layout}
                            isDark={isDark}
                          />
                        </motion.div>
                      )}

                      {/* Data Table */}
                      {msg.data && msg.data.length > 0 && (
                        <motion.div
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          className={`mt-6 rounded-3xl border overflow-hidden ${isDark ? 'bg-zinc-950 border-white/5' : 'bg-white border-zinc-200'} shadow-lg`}
                        >
                          <div className="px-6 py-4 border-b border-inherit flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Database className="w-3.5 h-3.5 text-blue-500" />
                              <span className="text-[10px] font-bold uppercase tracking-widest opacity-30">
                                {msg.data.length} records
                              </span>
                            </div>
                            <button
                              onClick={() => exportToExcel(msg.data)}
                              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/10 text-emerald-600 hover:bg-emerald-500 hover:text-white transition-all text-[10px] font-bold"
                            >
                              <FileSpreadsheet className="w-3 h-3" />
                              Export XLSX
                            </button>
                          </div>
                          <div className="overflow-x-auto max-h-72">
                            <table className="w-full text-xs text-left">
                              <thead className={`sticky top-0 z-10 ${isDark ? 'bg-zinc-900' : 'bg-zinc-50'}`}>
                                <tr className="border-b border-inherit">
                                  {Object.keys(msg.data[0]).map(key => (
                                    <th key={key} className="px-5 py-3.5 font-bold uppercase tracking-tight opacity-40 whitespace-nowrap">{key}</th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {msg.data.map((row, i) => (
                                  <tr key={i} className="border-b last:border-0 border-inherit hover:bg-blue-500/5 transition-colors">
                                    {Object.values(row).map((val, j) => (
                                      <td key={j} className="px-5 py-3.5 opacity-70 truncate max-w-[200px]">{String(val)}</td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </motion.div>
                      )}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
              <div ref={chatEndRef} />
            </div>

            {/* Input Bar */}
            <div className={`absolute bottom-8 left-1/2 -translate-x-1/2 w-full max-w-xl px-5 py-3.5 rounded-2xl border shadow-xl transition-all duration-300 z-20 ${
              isDark ? 'bg-zinc-900/95 border-white/10' : 'bg-white/95 border-zinc-200'
            } flex items-center gap-3 backdrop-blur-2xl`}>
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                placeholder="Talk to your data…"
                className="flex-1 bg-transparent border-none outline-none text-sm placeholder:opacity-30"
              />
              <button
                onClick={handleSend}
                disabled={isLoading || !input.trim()}
                className={`p-2.5 rounded-xl transition-all ${
                  input.trim() && !isLoading ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30 hover:bg-blue-700' : 'opacity-15 grayscale'
                }`}
              >
                {isLoading
                  ? <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}><Layers className="w-4 h-4" /></motion.div>
                  : <Send className="w-4 h-4" />
                }
              </button>
            </div>
          </div>
        </main>

        {/* ── INTELLIGENCE TRAIL PANEL ── */}
        <AnimatePresence>
          {isPanelOpen && (
            <motion.aside
              initial={{ x: 320, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 320, opacity: 0 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className={`w-72 border-l flex-shrink-0 flex flex-col p-6 overflow-y-auto no-scrollbar ${isDark ? 'bg-black border-white/5' : 'bg-zinc-50 border-zinc-200'}`}
            >
              <div className="flex items-center gap-2 mb-8">
                <Cpu className="w-4 h-4 text-blue-500" />
                <span className="text-[10px] font-black uppercase tracking-widest opacity-30">Intelligence Trail</span>
              </div>

              {/* Agent Steps */}
              <div className="space-y-5">
                {AGENT_STEPS.map((step, i) => {
                  const isComplete = executedSteps.includes(step) || executedSteps.includes('COMPLETE');
                  const isActive = isLoading && executedSteps.length === i;
                  const isPending = !isComplete && !isActive;

                  return (
                    <div key={step} className={`flex items-start gap-3 transition-opacity ${isComplete || isActive ? 'opacity-100' : 'opacity-20'}`}>
                      <div className="mt-0.5 flex-shrink-0">
                        {isComplete ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                        ) : isActive ? (
                          <div className="flex gap-0.5 items-center h-4 pt-1">
                            {[0, 0.2, 0.4].map((d, k) => (
                              <motion.div key={k} animate={{ scale: [1, 1.6, 1] }} transition={{ repeat: Infinity, duration: 1, delay: d }} className="w-1 h-1 bg-blue-500 rounded-full" />
                            ))}
                          </div>
                        ) : (
                          <div className="w-4 h-4 flex items-center justify-center">
                            <div className="w-1.5 h-1.5 rounded-full bg-zinc-400" />
                          </div>
                        )}
                      </div>
                      <div>
                        <div className={`text-[10px] font-bold tracking-widest ${isActive ? 'text-blue-500' : ''}`}>{step}</div>
                        {isActive && <div className="text-[9px] opacity-40 mt-0.5 animate-pulse">Working…</div>}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Foreman's Plan */}
              <div className="mt-10 pt-8 border-t border-dashed border-inherit">
                <div className="flex items-center gap-2 mb-4">
                  <Zap className="w-3.5 h-3.5 text-blue-500" />
                  <span className="text-[10px] font-black uppercase tracking-widest opacity-30">Foreman's Plan</span>
                </div>
                {lastPlan
                  ? <p className={`text-[11px] leading-relaxed italic ${isDark ? 'text-zinc-400' : 'text-zinc-500'} border-l-2 border-blue-500/30 pl-3`}>"{lastPlan}"</p>
                  : <p className="text-[10px] opacity-20 italic">No plan yet. Ask a question to begin.</p>
                }
              </div>

              {/* System Health */}
              <div className="mt-8">
                <div className={`p-5 rounded-2xl border border-blue-500/10 bg-blue-500/5`}>
                  <div className="text-[9px] font-black text-blue-500 uppercase tracking-widest mb-3">System Health</div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-[11px] opacity-50 font-medium">DuckDB Active</span>
                  </div>
                  {uploadedFiles.filter(f => f.status === 'ready').length > 0 && (
                    <div className="flex items-center gap-2 mt-1.5">
                      <div className="w-2 h-2 rounded-full bg-emerald-500" />
                      <span className="text-[11px] opacity-50 font-medium">
                        {uploadedFiles.filter(f => f.status === 'ready').length} dataset(s) loaded
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </motion.aside>
          )}
        </AnimatePresence>
      </div>

      {/* ── INFO MODAL ── */}
      <AnimatePresence>
        {showInfo && <InfoModal onClose={() => setShowInfo(false)} />}
      </AnimatePresence>

      {/* Grain */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.025] grayscale mix-blend-overlay z-[999]" style={{ backgroundImage: 'url("https://grainy-gradients.vercel.app/noise.svg")' }} />
    </div>
  );
}

export default App;
