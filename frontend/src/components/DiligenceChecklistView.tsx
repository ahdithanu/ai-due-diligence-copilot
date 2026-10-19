import React, { useState, useEffect } from 'react';
import {
  DiligenceChecklistResponse,
  ChecklistTask,
  WorkstreamCategory,
  TaskStatus,
  TaskPriority,
} from '../types';

interface DiligenceChecklistViewProps {
  investmentId: string;
}

export const DiligenceChecklistView: React.FC<DiligenceChecklistViewProps> = ({ investmentId }) => {
  const [data, setData] = useState<DiligenceChecklistResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedWorkstream, setSelectedWorkstream] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [showAddModal, setShowAddModal] = useState(false);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [newTaskWorkstream, setNewTaskWorkstream] = useState<WorkstreamCategory>('FINANCIAL_QOE');
  const [newTaskPriority, setNewTaskPriority] = useState<TaskPriority>('MEDIUM');
  const [newTaskAssignee, setNewTaskAssignee] = useState('Deal Lead');
  const [submitting, setSubmitting] = useState(false);

  const fetchChecklist = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/investments/${investmentId}/checklist`);
      if (res.ok) {
        const json: DiligenceChecklistResponse = await res.json();
        setData(json);
      }
    } catch (err) {
      console.error('Failed to load diligence checklist', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChecklist();
  }, [investmentId]);

  const handleUpdateStatus = async (taskId: string, newStatus: TaskStatus) => {
    try {
      const res = await fetch(`/api/v1/investments/${investmentId}/checklist/tasks/${taskId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        await fetchChecklist();
      }
    } catch (err) {
      console.error('Failed to update task status', err);
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    if (!window.confirm('Are you sure you want to remove this diligence task?')) return;
    try {
      const res = await fetch(`/api/v1/investments/${investmentId}/checklist/tasks/${taskId}`, {
        method: 'DELETE',
      });
      if (res.ok) {
        await fetchChecklist();
      }
    } catch (err) {
      console.error('Failed to delete task', err);
    }
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTaskTitle.trim()) return;
    setSubmitting(true);
    try {
      const res = await fetch(`/api/v1/investments/${investmentId}/checklist/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: newTaskTitle,
          workstream: newTaskWorkstream,
          priority: newTaskPriority,
          assigned_to: newTaskAssignee,
        }),
      });
      if (res.ok) {
        setNewTaskTitle('');
        setShowAddModal(false);
        await fetchChecklist();
      }
    } catch (err) {
      console.error('Failed to create task', err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  const tasks = data?.tasks || [];
  const filteredTasks = tasks.filter((t) => {
    const matchesWs = selectedWorkstream === 'ALL' || t.workstream === selectedWorkstream;
    const matchesStatus = statusFilter === 'ALL' || t.status === statusFilter;
    return matchesWs && matchesStatus;
  });

  const completedCount = tasks.filter((t) => t.status === 'COMPLETED').length;
  const inProgressCount = tasks.filter((t) => t.status === 'IN_PROGRESS').length;
  const blockedCount = tasks.filter((t) => t.status === 'BLOCKED').length;

  return (
    <div className="space-y-6">
      {/* Top Banner & Overall Progress */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-5">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-2xl">📋</span>
              <h2 className="text-xl font-bold text-slate-100">
                Institutional Diligence Workstream Tracker
              </h2>
              <span className="bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-xs px-2.5 py-1 rounded-full font-semibold">
                PE Standards (QoE / Legal / Tech)
              </span>
            </div>
            <p className="text-slate-400 text-sm mt-1">
              Tracks 6 parallel diligence workstreams, team assignments, blocker resolution, and audit evidence trails.
            </p>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium text-sm transition-colors shadow-lg shadow-indigo-600/20"
          >
            <span>+</span> Add Diligence Task
          </button>
        </div>

        {/* Progress Bar & KPI Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-4 border-t border-slate-800/80">
          <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800">
            <div className="text-xs text-slate-400 uppercase font-semibold">Overall Completion</div>
            <div className="text-2xl font-black text-indigo-400 mt-1">
              {data?.overall_progress_pct || 0}%
            </div>
            <div className="w-full bg-slate-800 h-2 rounded-full mt-2 overflow-hidden">
              <div
                className="bg-indigo-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${data?.overall_progress_pct || 0}%` }}
              ></div>
            </div>
          </div>
          <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800">
            <div className="text-xs text-slate-400 uppercase font-semibold">Completed Tasks</div>
            <div className="text-2xl font-bold text-emerald-400 mt-1">
              {completedCount} <span className="text-sm font-normal text-slate-500">/ {tasks.length}</span>
            </div>
            <div className="text-xs text-slate-500 mt-2">Verified with data room evidence</div>
          </div>
          <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800">
            <div className="text-xs text-slate-400 uppercase font-semibold">In Progress</div>
            <div className="text-2xl font-bold text-amber-400 mt-1">{inProgressCount}</div>
            <div className="text-xs text-slate-500 mt-2">Under active investigation</div>
          </div>
          <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800">
            <div className="text-xs text-slate-400 uppercase font-semibold">Blocked / Attention</div>
            <div className="text-2xl font-bold text-rose-400 mt-1">{blockedCount}</div>
            <div className="text-xs text-slate-500 mt-2">Requires target company follow-up</div>
          </div>
        </div>
      </div>

      {/* 6 Workstreams Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {data?.workstreams.map((ws) => {
          const isSelected = selectedWorkstream === ws.workstream;
          return (
            <button
              key={ws.workstream}
              onClick={() => setSelectedWorkstream(isSelected ? 'ALL' : ws.workstream)}
              className={`text-left p-3.5 rounded-xl border transition-all ${
                isSelected
                  ? 'bg-indigo-950/40 border-indigo-500 shadow-md shadow-indigo-950'
                  : 'bg-slate-900 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-slate-300 truncate">{ws.display_name}</span>
                {ws.blocked_tasks > 0 && (
                  <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping"></span>
                )}
              </div>
              <div className="flex items-baseline justify-between mt-2">
                <span className="text-lg font-black text-slate-100">{ws.completion_pct}%</span>
                <span className="text-xs text-slate-400">
                  {ws.completed_tasks}/{ws.total_tasks}
                </span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
                <div
                  className={`h-1.5 rounded-full ${
                    ws.blocked_tasks > 0
                      ? 'bg-rose-500'
                      : ws.completion_pct === 100
                      ? 'bg-emerald-500'
                      : 'bg-indigo-500'
                  }`}
                  style={{ width: `${ws.completion_pct}%` }}
                ></div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Task Filters & Interactive List */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3 bg-slate-900/50">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-slate-300">Workstream:</span>
            <select
              value={selectedWorkstream}
              onChange={(e) => setSelectedWorkstream(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-lg px-3 py-1.5 focus:border-indigo-500 focus:outline-none"
            >
              <option value="ALL">All Workstreams ({tasks.length})</option>
              {data?.workstreams.map((ws) => (
                <option key={ws.workstream} value={ws.workstream}>
                  {ws.display_name} ({ws.total_tasks})
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-slate-300">Status:</span>
            <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
              {['ALL', 'NOT_STARTED', 'IN_PROGRESS', 'BLOCKED', 'COMPLETED'].map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-3 py-1 rounded-md font-medium transition-colors ${
                    statusFilter === st
                      ? 'bg-indigo-600 text-white'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {st.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Task Rows */}
        <div className="divide-y divide-slate-800/80">
          {filteredTasks.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-sm">
              No diligence tasks found matching the selected filter.
            </div>
          ) : (
            filteredTasks.map((task) => (
              <div
                key={task.id}
                className="p-4 hover:bg-slate-850 transition-colors flex flex-col md:flex-row md:items-start justify-between gap-4"
              >
                <div className="space-y-1.5 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                        task.priority === 'HIGH'
                          ? 'bg-rose-950 text-rose-300 border border-rose-800/60'
                          : task.priority === 'MEDIUM'
                          ? 'bg-amber-950 text-amber-300 border border-amber-800/60'
                          : 'bg-slate-800 text-slate-300'
                      }`}
                    >
                      {task.priority} Priority
                    </span>
                    <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono">
                      {task.workstream.replace('_', ' ')}
                    </span>
                    <span className="text-xs text-slate-400">
                      👤 {task.assigned_to}
                    </span>
                  </div>

                  <h4 className="text-base font-semibold text-slate-100">{task.title}</h4>

                  {task.findings_summary && (
                    <p className="text-sm text-slate-300 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/70">
                      <span className="font-semibold text-slate-400">Findings: </span>
                      {task.findings_summary}
                    </p>
                  )}

                  {task.evidence_chunk_ids && task.evidence_chunk_ids.length > 0 && (
                    <div className="flex items-center gap-1.5 pt-1">
                      <span className="text-xs text-slate-500">Evidence Citations:</span>
                      {task.evidence_chunk_ids.map((cid) => (
                        <span
                          key={cid}
                          className="text-xs bg-indigo-950/50 text-indigo-400 border border-indigo-800/50 px-2 py-0.5 rounded font-mono"
                        >
                          {cid}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Right Action & Status Dropdown */}
                <div className="flex items-center gap-2 self-start md:self-center">
                  <select
                    value={task.status}
                    onChange={(e) => handleUpdateStatus(task.id, e.target.value as TaskStatus)}
                    className={`text-xs font-bold rounded-lg px-3 py-1.5 border focus:outline-none transition-colors ${
                      task.status === 'COMPLETED'
                        ? 'bg-emerald-950/80 text-emerald-300 border-emerald-700'
                        : task.status === 'BLOCKED'
                        ? 'bg-rose-950/80 text-rose-300 border-rose-700'
                        : task.status === 'IN_PROGRESS'
                        ? 'bg-amber-950/80 text-amber-300 border-amber-700'
                        : 'bg-slate-800 text-slate-300 border-slate-700'
                    }`}
                  >
                    <option value="NOT_STARTED">Not Started</option>
                    <option value="IN_PROGRESS">In Progress</option>
                    <option value="BLOCKED">Blocked</option>
                    <option value="COMPLETED">Completed</option>
                  </select>

                  <button
                    onClick={() => handleDeleteTask(task.id)}
                    title="Delete Task"
                    className="text-slate-500 hover:text-rose-400 p-1.5 rounded hover:bg-slate-800 transition-colors"
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Add Task Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-lg w-full shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-slate-100">Add Diligence Workstream Task</h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleCreateTask} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Task Title / Investigation Scope
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Audit Sales Tax Nexus in 5 Key States"
                  value={newTaskTitle}
                  onChange={(e) => setNewTaskTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Workstream
                  </label>
                  <select
                    value={newTaskWorkstream}
                    onChange={(e) => setNewTaskWorkstream(e.target.value as WorkstreamCategory)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="FINANCIAL_QOE">Financial QoE</option>
                    <option value="COMMERCIAL_GTM">Commercial GTM</option>
                    <option value="TECHNICAL_PRODUCT">Technical Product</option>
                    <option value="LEGAL_REGULATORY">Legal & IP</option>
                    <option value="MANAGEMENT_HR">Management HR</option>
                    <option value="TAX_STRUCTURE">Tax Structure</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Priority
                  </label>
                  <select
                    value={newTaskPriority}
                    onChange={(e) => setNewTaskPriority(e.target.value as TaskPriority)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="HIGH">High (Deal-Critical)</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="LOW">Low</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Assigned Team Member / Lead
                </label>
                <input
                  type="text"
                  value={newTaskAssignee}
                  onChange={(e) => setNewTaskAssignee(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-lg shadow-md"
                >
                  {submitting ? 'Creating...' : 'Create Task'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
