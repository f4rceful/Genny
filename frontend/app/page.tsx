'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Play,
  Loader2,
  FileText,
  Code2,
  AlertCircle,
  File,
  CheckCircle2,
  Terminal,
  MonitorPlay,
  Upload,
  ChevronRight,
  Folder,
  FolderOpen,
  RotateCcw,
  Wrench,
  X,
  Clock,
  Cpu,
} from 'lucide-react';

type Status = 'idle' | 'running' | 'done' | 'failed';
type Tab = 'code' | 'preview';

interface FormData {
  bt: string;
  bp: string;
  features: string;
}

interface StepInfo {
  name: string;
  started_at: number;
  ended_at: number | null;
  model: string;
}

const STEP_LABELS: Record<string, string> = {
  queued: 'В очереди',
  initializing: 'Инициализация',
  'use-cases': 'Генерация кейсов',
  analyst: 'Анализ требований',
  architect: 'Проектирование архитектуры',
  coder: 'Генерация кода',
  tester: 'Написание тестов',
};

function getStepLabel(name: string): string {
  if (STEP_LABELS[name]) return STEP_LABELS[name];
  return name
    .replace('test-check', 'Проверка тестов')
    .replace('fixing', 'Исправление кода')
    .replace('re-testing', 'Повтор тестов')
    .replace('refine:', 'Доработка:');
}

function shortModel(model: string): string {
  if (!model) return '';
  const name = model.split('/').pop() ?? model;
  // e.g. "qwen3-235b-a22b" → "qwen3-235b"
  const parts = name.split('-');
  return parts.slice(0, 2).join('-');
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}с`;
  return `${Math.floor(seconds / 60)}м ${Math.round(seconds % 60)}с`;
}

function buildTree(files: string[]): Record<string, any> {
  const tree: Record<string, any> = {};
  for (const f of files) {
    const parts = f.split('/');
    let node = tree;
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      if (i === parts.length - 1) {
        node[part] = f;
      } else {
        node[part] = node[part] && typeof node[part] === 'object' ? node[part] : {};
        node = node[part];
      }
    }
  }
  return tree;
}

function FileTreeNode({
  name,
  node,
  depth,
  activeFile,
  onSelect,
}: {
  name: string;
  node: any;
  depth: number;
  activeFile: string | null;
  onSelect: (path: string) => void;
}) {
  const isFile = typeof node === 'string';
  const [open, setOpen] = useState(true);

  const getIcon = (fileName: string) => {
    if (fileName.endsWith('.html')) return <Code2 className="w-3.5 h-3.5 text-orange-400 shrink-0" />;
    if (fileName.endsWith('.css')) return <Code2 className="w-3.5 h-3.5 text-blue-400 shrink-0" />;
    if (fileName.endsWith('.js') || fileName.endsWith('.ts')) return <Code2 className="w-3.5 h-3.5 text-yellow-400 shrink-0" />;
    if (fileName.endsWith('.md')) return <FileText className="w-3.5 h-3.5 text-emerald-400 shrink-0" />;
    if (fileName.endsWith('.json')) return <FileText className="w-3.5 h-3.5 text-amber-400 shrink-0" />;
    if (fileName.endsWith('.py')) return <Code2 className="w-3.5 h-3.5 text-sky-400 shrink-0" />;
    return <File className="w-3.5 h-3.5 text-slate-400 shrink-0" />;
  };

  if (isFile) {
    const isActive = activeFile === node;
    return (
      <div
        onClick={() => onSelect(node)}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
        className={`flex items-center gap-1.5 py-[3px] pr-2 cursor-pointer rounded text-xs transition-colors ${
          isActive
            ? 'bg-[#ef3124]/20 text-white border-l-2 border-[#ef3124]'
            : 'text-white/50 hover:bg-white/5 hover:text-white/80 border-l-2 border-transparent'
        }`}
      >
        {getIcon(name)}
        <span className="truncate">{name}</span>
      </div>
    );
  }

  return (
    <div>
      <div
        onClick={() => setOpen(!open)}
        style={{ paddingLeft: `${depth * 12 + 4}px` }}
        className="flex items-center gap-1 py-[3px] pr-2 cursor-pointer text-white/40 hover:text-white/70 text-xs transition-colors rounded hover:bg-white/5"
      >
        <ChevronRight className={`w-3 h-3 shrink-0 transition-transform ${open ? 'rotate-90' : ''}`} />
        {open
          ? <FolderOpen className="w-3.5 h-3.5 text-sky-400/80 shrink-0" />
          : <Folder className="w-3.5 h-3.5 text-sky-400/80 shrink-0" />}
        <span className="font-medium">{name}</span>
      </div>
      {open && (
        <div>
          {Object.entries(node).map(([childName, childNode]) => (
            <FileTreeNode
              key={childName}
              name={childName}
              node={childNode}
              depth={depth + 1}
              activeFile={activeFile}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function setUrlRun(id: string | null) {
  const url = new URL(window.location.href);
  if (id) {
    url.searchParams.set('run', id);
  } else {
    url.searchParams.delete('run');
  }
  window.history.replaceState(null, '', url.toString());
}

export default function App() {
  const [formData, setFormData] = useState<FormData>({ bt: '', bp: '', features: '' });
  const [runId, setRunId] = useState<string | null>(null);
  const [status, setStatus] = useState<Status>('idle');
  const [steps, setSteps] = useState<StepInfo[]>([]);
  const [files, setFiles] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<Tab>('code');
  const [activeFile, setActiveFile] = useState<string | null>(null);
  const [activeFileContent, setActiveFileContent] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);

  const [openRunId, setOpenRunId] = useState('');
  const [openRunError, setOpenRunError] = useState<string | null>(null);

  interface RunMeta { run_id: string; status: string; created_at: number; file_count: number; step_count: number; }
  const [runsList, setRunsList] = useState<RunMeta[]>([]);
  const [runsLoading, setRunsLoading] = useState(false);

  const [patchInstruction, setPatchInstruction] = useState('');
  const [patching, setPatching] = useState(false);
  const [patchedFiles, setPatchedFiles] = useState<string[]>([]);
  const [patchError, setPatchError] = useState<string | null>(null);

  const fetchRuns = async () => {
    setRunsLoading(true);
    try {
      const res = await fetch('http://localhost:8000/runs');
      if (res.ok) { const d = await res.json(); setRunsList(d.runs || []); }
    } catch {}
    finally { setRunsLoading(false); }
  };

  // Restore run from URL on mount
  useEffect(() => {
    fetchRuns();
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlRunId = params.get('run');
    if (!urlRunId) return;
    fetch(`http://localhost:8000/status/${urlRunId}`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data || data.status === 'not_found') { setUrlRun(null); return; }
        setRunId(urlRunId);
        const s: Status = data.status === 'done' ? 'done' : data.status === 'failed' ? 'failed' : 'running';
        setStatus(s);
        setFiles(data.files || []);
        setSteps(data.steps || []);
        setError(data.error || null);
      })
      .catch(() => setUrlRun(null));
  }, []);

  // Keep URL in sync with runId
  useEffect(() => {
    setUrlRun(runId);
  }, [runId]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>, field: keyof FormData) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      setFormData(prev => ({ ...prev, [field]: event.target?.result as string }));
    };
    reader.readAsText(file);
    e.target.value = '';
  };

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [steps]);

  useEffect(() => {
    let intervalId: NodeJS.Timeout;
    const pollStatus = async () => {
      if (!runId) return;
      try {
        const res = await fetch(`http://localhost:8000/status/${runId}`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.steps?.length > 0) setSteps(data.steps);
        if (data.files?.length > 0) setFiles(data.files);
        if (data.status === 'done' || data.status === 'failed') {
          setStatus(data.status);
          if (data.error) setError(data.error);
          setCancelling(false);
        }
      } catch {}
    };
    if (runId && status === 'running') {
      pollStatus();
      intervalId = setInterval(pollStatus, 2000);
    }
    return () => clearInterval(intervalId);
  }, [runId, status]);

  const handleGenerate = async () => {
    if (!formData.bt || !formData.bp) return;
    setStatus('running');
    setSteps([]);
    setError(null);
    setFiles([]);
    setActiveFile(null);
    setActiveFileContent('');
    setActiveTab('code');
    setPatchInstruction('');
    setPatchedFiles([]);
    setPatchError(null);
    setCancelling(false);
    try {
      const res = await fetch('http://localhost:8000/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      if (!res.ok) throw new Error('Ошибка запуска генерации');
      const data = await res.json();
      setRunId(data.run_id);
    } catch (err: any) {
      setStatus('failed');
      setError(err.message || 'Неизвестная ошибка');
    }
  };

  const handleCancel = async () => {
    if (!runId || cancelling) return;
    setCancelling(true);
    try {
      await fetch(`http://localhost:8000/cancel/${runId}`, { method: 'POST' });
    } catch {}
  };

  const loadFileContent = async (filePath: string, rid?: string) => {
    const id = rid ?? runId;
    if (!id) return;
    setActiveFile(filePath);
    setActiveTab('code');
    setActiveFileContent('Загрузка...');
    try {
      const res = await fetch(`http://localhost:8000/file/${id}/${encodeURIComponent(filePath)}`);
      if (!res.ok) throw new Error();
      const data = await res.json();
      setActiveFileContent(data.content);
    } catch {
      setActiveFileContent('Ошибка загрузки файла.');
    }
  };

  const loadExistingRun = async () => {
    const id = openRunId.trim();
    if (!id) return;
    setOpenRunError(null);
    try {
      const res = await fetch(`http://localhost:8000/status/${id}`);
      if (!res.ok) { setOpenRunError('Сервер недоступен'); return; }
      const data = await res.json();
      if (data.status === 'not_found') { setOpenRunError('Проект не найден'); return; }
      setRunId(id);
      const s: Status = data.status === 'done' ? 'done' : data.status === 'failed' ? 'failed' : 'running';
      setStatus(s);
      setFiles(data.files || []);
      setSteps(data.steps || []);
      setError(data.error || null);
      setOpenRunId('');
      setPatchedFiles([]);
      setPatchError(null);
    } catch {
      setOpenRunError('Ошибка соединения');
    }
  };

  const handlePatch = async () => {
    if (!runId || !patchInstruction.trim() || patching) return;
    setPatching(true);
    setPatchedFiles([]);
    setPatchError(null);
    try {
      const res = await fetch(`http://localhost:8000/patch/${runId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ instruction: patchInstruction }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Ошибка сервера');
      }
      const data = await res.json();
      setPatchedFiles(data.patched_files || []);
      const statusRes = await fetch(`http://localhost:8000/status/${runId}`);
      if (statusRes.ok) {
        const statusData = await statusRes.json();
        setFiles(statusData.files || []);
      }
      if (activeFile && (data.patched_files as string[])?.includes(activeFile)) {
        loadFileContent(activeFile);
      }
      setPreviewKey(k => k + 1);
    } catch (err: any) {
      setPatchError(err.message || 'Неизвестная ошибка');
    } finally {
      setPatching(false);
    }
  };

  const handleNewProject = () => {
    setRunId(null);
    setStatus('idle');
    setSteps([]);
    setFiles([]);
    setActiveFile(null);
    setActiveFileContent('');
    setError(null);
    setPatchInstruction('');
    setPatchedFiles([]);
    setPatchError(null);
    setOpenRunId('');
    setOpenRunError(null);
    setCancelling(false);
  };

  const [previewKey, setPreviewKey] = useState(0);

  const tree = buildTree(files);
  const showForm = !runId || status === 'idle';
  const isDone = status === 'done' || status === 'failed';

  return (
    <div className="flex h-screen w-full bg-slate-50 text-slate-900 overflow-hidden font-sans select-none">

      {/* Left Panel */}
      <aside className="w-[35%] bg-white border-r border-slate-200 flex flex-col h-full shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-[#ef3124] flex items-center justify-center text-white font-extrabold text-2xl">
              G
            </div>
            <div className="flex flex-col">
              <h1 className="font-bold text-base tracking-tight leading-none text-slate-900">GENNY</h1>
              <p className="text-[10px] text-slate-400 font-medium uppercase mt-1 tracking-wider">Генерация AI-агентами</p>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">

          {/* FORM STATE */}
          {showForm && (
            <div className="space-y-6 animate-in fade-in duration-500">
              {(['bt', 'bp', 'features'] as const).map((field) => {
                const labels = { bt: 'Бизнес-требования (БТ)', bp: 'Бизнес-процесс (БП)', features: 'Характеристики (необязательно)' };
                const placeholders = {
                  bt: 'Опишите бизнес-цели и требования...',
                  bp: 'Опишите пошагово взаимодействие пользователя...',
                  features: 'Тема, язык, название, ограничения...',
                };
                return (
                  <div key={field} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-semibold text-slate-800">{labels[field]}</label>
                      <label className="cursor-pointer text-xs font-medium text-[#ef3124] hover:text-red-700 flex items-center gap-1 transition-colors">
                        <Upload className="w-3.5 h-3.5" /> Загрузить .md
                        <input type="file" accept=".md" className="hidden" onChange={(e) => handleFileUpload(e, field)} />
                      </label>
                    </div>
                    <textarea
                      value={formData[field]}
                      onChange={e => setFormData({ ...formData, [field]: e.target.value })}
                      className="w-full h-28 p-4 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-[#ef3124] focus:ring-2 focus:ring-[#ef3124]/20 outline-none resize-none transition-all text-sm text-slate-800 shadow-sm placeholder:text-slate-400"
                      placeholder={placeholders[field]}
                    />
                  </div>
                );
              })}

              {/* Open existing project */}
              <div className="pt-2 border-t border-slate-100">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs text-slate-400 font-medium">Или откройте существующий проект</p>
                  <button
                    onClick={fetchRuns}
                    disabled={runsLoading}
                    title="Обновить список"
                    className="p-1 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors disabled:opacity-40"
                  >
                    <RotateCcw className={`w-3.5 h-3.5 ${runsLoading ? 'animate-spin' : ''}`} />
                  </button>
                </div>

                {runsList.length > 0 ? (
                  <div className="space-y-1.5 max-h-48 overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
                    {runsList.map(r => (
                      <button
                        key={r.run_id}
                        onClick={() => { setOpenRunId(r.run_id); setOpenRunError(null); }}
                        className={`w-full text-left px-3 py-2 rounded-lg border transition-all text-xs ${
                          openRunId === r.run_id
                            ? 'border-[#ef3124] bg-red-50'
                            : 'border-slate-200 bg-slate-50 hover:bg-white hover:border-slate-300'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-mono text-slate-600 truncate">{r.run_id.slice(0, 8)}…</span>
                          <div className="flex items-center gap-2 shrink-0">
                            <span className="text-slate-400">{r.file_count} файлов</span>
                            <span className={`px-1.5 py-0.5 rounded-full font-semibold ${
                              r.status === 'done' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
                            }`}>
                              {r.status === 'done' ? 'Готово' : 'Ошибка'}
                            </span>
                          </div>
                        </div>
                        <p className="text-slate-400 mt-0.5">
                          {new Date(r.created_at * 1000).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 text-center py-3">
                    {runsLoading ? 'Загрузка...' : 'Нет сохранённых проектов'}
                  </p>
                )}

                {openRunId && (
                  <button
                    onClick={loadExistingRun}
                    className="mt-2 w-full px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs transition-colors"
                  >
                    Открыть выбранный проект
                  </button>
                )}
                {openRunError && (
                  <p className="text-xs text-rose-500 mt-2 flex items-center gap-1.5">
                    <AlertCircle className="w-3 h-3 shrink-0" /> {openRunError}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* RUNNING STATE */}
          {!showForm && status === 'running' && (
            <div className="space-y-4 h-full flex flex-col">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-[#ef3124]" />
                  <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Лог выполнения</h2>
                </div>
                <span className="flex items-center gap-2 text-xs font-semibold text-[#ef3124] bg-red-50 px-3 py-1.5 rounded-full border border-red-100">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  {cancelling ? 'Отмена...' : 'Выполнение...'}
                </span>
              </div>
              <div className="flex-1 overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
                <div className="space-y-1 pb-8">
                  {steps.map((step, idx) => {
                    const isLast = idx === steps.length - 1;
                    const isRunning = isLast && step.ended_at === null;
                    const duration = step.ended_at ? step.ended_at - step.started_at : null;
                    const model = shortModel(step.model);
                    return (
                      <div key={idx} className="flex gap-3 animate-in fade-in slide-in-from-left-2 duration-300">
                        <div className="flex flex-col items-center pt-0.5">
                          {isRunning
                            ? <Loader2 className="w-4 h-4 text-[#ef3124] animate-spin shrink-0" />
                            : <div className="w-4 h-4 rounded-full bg-green-100 flex items-center justify-center shrink-0">
                                <CheckCircle2 className="w-2.5 h-2.5 text-green-600" />
                              </div>
                          }
                          {!isLast && (
                            <div className={`w-[1px] flex-1 mt-1 mb-0.5 min-h-[12px] ${isRunning ? 'bg-slate-100' : 'bg-green-200'}`} />
                          )}
                        </div>
                        <div className="pb-3 min-w-0">
                          <p className={`text-sm font-semibold leading-tight ${isRunning ? 'text-[#ef3124]' : 'text-slate-800'}`}>
                            {getStepLabel(step.name)}
                          </p>
                          <div className="flex items-center gap-2 mt-1 flex-wrap">
                            {model && (
                              <span className="flex items-center gap-1 text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded font-mono">
                                <Cpu className="w-2.5 h-2.5" />{model}
                              </span>
                            )}
                            {isRunning && (
                              <span className="text-[11px] text-slate-400 flex items-center gap-1">
                                <Clock className="w-3 h-3" /> Выполняется...
                              </span>
                            )}
                            {duration !== null && (
                              <span className="text-[11px] text-slate-400 flex items-center gap-1">
                                <Clock className="w-3 h-3" /> {formatDuration(duration)}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                  <div ref={logsEndRef} />
                </div>
              </div>
            </div>
          )}

          {/* DONE / FAILED STATE — compact log + patch */}
          {!showForm && isDone && (
            <div className="space-y-6">
              {/* Compact log */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-slate-400" />
                    <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Выполнение</h2>
                  </div>
                  {status === 'done' && (
                    <span className="flex items-center gap-2 text-xs font-semibold text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-full border border-emerald-100">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Завершено
                    </span>
                  )}
                  {status === 'failed' && (
                    <span className="flex items-center gap-2 text-xs font-semibold text-rose-600 bg-rose-50 px-3 py-1.5 rounded-full border border-rose-100">
                      <AlertCircle className="w-3.5 h-3.5" /> Ошибка
                    </span>
                  )}
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {steps.map((step, idx) => {
                    const duration = step.ended_at && step.started_at ? step.ended_at - step.started_at : null;
                    const model = shortModel(step.model);
                    return (
                      <span key={idx} className="flex items-center gap-1 text-[10px] bg-slate-100 text-slate-600 px-2 py-1 rounded-full">
                        <CheckCircle2 className="w-2.5 h-2.5 text-green-500 shrink-0" />
                        {getStepLabel(step.name)}
                        {model && <span className="text-slate-400 font-mono">· {model}</span>}
                        {duration !== null && <span className="text-slate-400">· {formatDuration(duration)}</span>}
                      </span>
                    );
                  })}
                </div>
                {status === 'failed' && error && (
                  <div className="flex gap-2 items-start p-3 bg-rose-50/80 rounded-xl border border-rose-200 mt-3">
                    <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                    <span className="text-rose-800 text-xs font-medium">{error}</span>
                  </div>
                )}
              </div>

              {/* Patch section */}
              <div className="border-t border-slate-100 pt-5">
                <div className="flex items-center gap-2 mb-3">
                  <Wrench className="w-4 h-4 text-[#ef3124]" />
                  <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Доработка</h2>
                </div>
                <textarea
                  value={patchInstruction}
                  onChange={e => setPatchInstruction(e.target.value)}
                  placeholder="Опишите что нужно изменить... Например: добавь валидацию email, измени цвет кнопок на синий, добавь поле поиска"
                  className="w-full h-32 p-4 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-[#ef3124] focus:ring-2 focus:ring-[#ef3124]/20 outline-none resize-none transition-all text-sm text-slate-800 shadow-sm placeholder:text-slate-400"
                />
                <button
                  onClick={handlePatch}
                  disabled={!patchInstruction.trim() || patching}
                  className="mt-3 w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-[#ef3124] hover:bg-[#cc2a1f] disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed text-white font-bold text-sm transition-all"
                >
                  {patching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wrench className="w-4 h-4" />}
                  {patching ? 'Применяем правки...' : 'Применить правки'}
                </button>

                {patchedFiles.length > 0 && (
                  <div className="mt-3 p-3 bg-emerald-50 rounded-xl border border-emerald-200">
                    <p className="text-xs font-bold text-emerald-700 mb-2 flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Обновлено {patchedFiles.length} {patchedFiles.length === 1 ? 'файл' : patchedFiles.length < 5 ? 'файла' : 'файлов'}
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {patchedFiles.map(f => (
                        <span key={f} className="text-[10px] bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded font-mono">
                          {f.split('/').pop()}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {patchError && (
                  <div className="mt-3 p-3 bg-rose-50 rounded-xl border border-rose-200 flex gap-2 items-start">
                    <AlertCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
                    <span className="text-xs text-rose-700 font-medium">{patchError}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-slate-100 bg-slate-50">
          {showForm ? (
            <button
              onClick={handleGenerate}
              disabled={!formData.bt || !formData.bp}
              className="w-full relative overflow-hidden bg-[#ef3124] hover:bg-[#cc2a1f] disabled:bg-slate-300 disabled:text-slate-500 disabled:cursor-not-allowed text-white font-bold py-4 rounded-xl transition-all flex items-center justify-center gap-2"
            >
              <Play className="w-5 h-5 fill-current" />
              Начать разработку
            </button>
          ) : isDone ? (
            <button
              onClick={handleNewProject}
              className="w-full py-4 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-xl flex items-center justify-center gap-2 transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              Новый проект
            </button>
          ) : (
            <div className="flex gap-2">
              <div className="flex-1 py-4 bg-slate-200 text-slate-500 font-bold rounded-xl flex items-center justify-center gap-2 cursor-not-allowed text-sm">
                <Loader2 className="w-4 h-4 animate-spin" />
                {cancelling ? 'Отменяем...' : 'Генерация...'}
              </div>
              <button
                onClick={handleCancel}
                disabled={cancelling}
                title="Отменить генерацию"
                className="px-4 py-4 bg-rose-100 hover:bg-rose-200 disabled:opacity-50 disabled:cursor-not-allowed text-rose-600 font-bold rounded-xl flex items-center justify-center transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* Right Panel — VSCode layout */}
      <main className="w-[65%] bg-zinc-950 flex h-full overflow-hidden">

        {/* File tree sidebar */}
        {runId && (
          <div className="w-52 shrink-0 bg-zinc-900 border-r border-white/5 flex flex-col overflow-hidden">
            <div className="px-3 py-2 border-b border-white/5">
              <p className="text-[10px] font-bold text-white/30 uppercase tracking-widest">Проводник</p>
            </div>
            <div className="flex-1 overflow-y-auto py-1 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
              {files.length === 0 ? (
                <p className="text-zinc-500 text-xs px-3 py-4">
                  {status === 'running' ? 'Генерация...' : 'Нет файлов'}
                </p>
              ) : (
                Object.entries(tree).map(([name, node]) => (
                  <FileTreeNode
                    key={name}
                    name={name}
                    node={node}
                    depth={0}
                    activeFile={activeFile}
                    onSelect={loadFileContent}
                  />
                ))
              )}
            </div>
          </div>
        )}

        {/* Editor area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Tabs */}
          <div className="flex bg-zinc-900 border-b border-white/5 h-10 items-end px-2 justify-between shrink-0">
            <div className="flex gap-1 h-full">
              <button
                onClick={() => setActiveTab('code')}
                className={`flex items-center gap-2 px-4 h-full text-xs font-medium border-b-2 transition-all ${
                  activeTab === 'code'
                    ? 'border-[#ef3124] text-[#ef3124] bg-white/5'
                    : 'border-transparent text-white/40 hover:text-white hover:bg-white/5'
                }`}
              >
                <Code2 className="w-3.5 h-3.5" />
                <span className="truncate max-w-[160px]">{activeFile ? activeFile.split('/').pop() : 'Код'}</span>
              </button>
              <button
                onClick={() => setActiveTab('preview')}
                disabled={status !== 'done'}
                className={`flex items-center gap-2 px-4 h-full text-xs font-medium border-b-2 transition-all disabled:opacity-30 disabled:cursor-not-allowed ${
                  activeTab === 'preview'
                    ? 'border-[#ef3124] text-[#ef3124] bg-white/5'
                    : 'border-transparent text-white/40 hover:text-white hover:bg-white/5'
                }`}
              >
                <MonitorPlay className="w-3.5 h-3.5" />
                Preview
              </button>
            </div>
            {runId && (
              <span className="text-[10px] bg-white/10 text-white/50 px-2 py-0.5 rounded font-mono mb-2 shrink-0">
                {runId}
              </span>
            )}
          </div>

          {/* Content */}
          <div className="flex-1 overflow-hidden relative">
            {/* Empty state */}
            {!runId && (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-zinc-600 gap-4">
                <div className="w-20 h-20 rounded-3xl border border-zinc-800 flex items-center justify-center bg-zinc-900/40">
                  <Terminal className="w-9 h-9 text-zinc-600/80" />
                </div>
                <div className="space-y-1 text-center">
                  <h3 className="text-zinc-400 font-semibold">Рабочая область пуста</h3>
                  <p className="text-sm text-zinc-600">Заполните спецификацию слева и запустите генерацию</p>
                </div>
              </div>
            )}

            {/* Code view */}
            {activeTab === 'code' && runId && (
              <div className="absolute inset-0 overflow-auto p-6 font-mono text-sm leading-relaxed [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
                {!activeFile ? (
                  <div className="flex flex-col items-center justify-center h-full gap-3 text-zinc-500">
                    <Code2 className="w-10 h-10 text-zinc-700" />
                    <span className="text-sm">Выберите файл в проводнике слева</span>
                  </div>
                ) : (
                  <pre className="text-zinc-300 whitespace-pre-wrap break-words">
                    <code>{activeFileContent}</code>
                  </pre>
                )}
              </div>
            )}

            {/* Preview */}
            {activeTab === 'preview' && (
              <div className="absolute inset-0 flex flex-col p-4">
                {status === 'done' ? (
                  <div className="w-full h-full border border-zinc-800 rounded-xl overflow-hidden flex flex-col bg-white shadow-2xl">
                    <div className="h-9 bg-[#f5f5f7] border-b border-zinc-200 flex items-center px-4 gap-4 shrink-0">
                      <div className="flex items-center gap-2">
                        <div className="flex gap-1.5">
                          <div className="w-2.5 h-2.5 rounded-full bg-rose-400" />
                          <div className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                          <div className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                        </div>
                        <button
                          onClick={() => setPreviewKey(k => k + 1)}
                          className="p-0.5 rounded hover:bg-zinc-300/60 text-zinc-500 hover:text-zinc-700 transition-colors"
                          title="Перезагрузить"
                        >
                          <RotateCcw className="w-3 h-3" />
                        </button>
                      </div>
                      <div className="flex-1 max-w-xl mx-auto bg-white border border-zinc-300 rounded h-5 flex items-center justify-center px-3 shadow-inner">
                        <span className="text-[10px] text-zinc-400 truncate font-mono">
                          localhost:8000/output/{runId}/src/index.html
                        </span>
                      </div>
                    </div>
                    <div className="flex-1 relative">
                      <iframe
                        key={previewKey}
                        src={`http://localhost:8000/output/${runId}/src/index.html?_=${previewKey}`}
                        className="absolute inset-0 w-full h-full border-none"
                        title="Preview"
                        sandbox="allow-scripts allow-same-origin allow-forms allow-modals"
                      />
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full text-zinc-500 text-sm">
                    Приложение ещё не готово
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Status bar */}
          <div className="h-6 bg-[#0a0a0b] border-t border-white/5 flex items-center px-4 justify-between shrink-0 text-[10px] text-white/40 font-medium">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full ${
                  status === 'done' ? 'bg-emerald-500' :
                  status === 'running' ? 'bg-amber-500 animate-pulse' :
                  status === 'failed' ? 'bg-rose-500' : 'bg-zinc-600'
                }`} />
                <span className="uppercase tracking-wider">
                  {status === 'idle' ? 'Ожидание' : status === 'running' ? 'Генерация...' : status === 'failed' ? 'Ошибка' : 'Готово'}
                </span>
              </div>
              {files.length > 0 && (
                <span className="border-l border-white/10 pl-4">{files.length} файлов</span>
              )}
              {activeTab === 'code' && activeFile && (
                <span className="border-l border-white/10 pl-4">{activeFileContent.split('\n').length} строк</span>
              )}
            </div>
            <div className="flex items-center gap-3 border-l border-white/10 pl-4">
              {activeTab === 'code' && activeFile && (
                <span className="text-white/30 truncate max-w-[300px]">{activeFile}</span>
              )}
              <span>UTF-8</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
