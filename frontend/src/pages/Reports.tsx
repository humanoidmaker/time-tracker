import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line,
} from 'recharts';
import { BarChart3, Loader2, Clock, Users, Briefcase, TrendingUp } from 'lucide-react';
import api from '@/lib/api';
import { formatCurrency, formatDate } from '@/lib/utils';

const COLORS = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#84cc16'];

export default function Reports() {
  const [loading, setLoading] = useState(true);
  const [timesheets, setTimesheets] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [clients, setClients] = useState<any[]>([]);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [dateRange, setDateRange] = useState('30');

  useEffect(() => {
    Promise.all([
      api.get('/timesheets').then(r => r.data.timesheets || r.data.entries || []).catch(() => []),
      api.get('/projects').then(r => r.data.projects || []).catch(() => []),
      api.get('/clients').then(r => r.data.clients || []).catch(() => []),
      api.get('/invoices').then(r => r.data.invoices || []).catch(() => []),
    ]).then(([t, p, c, inv]) => {
      setTimesheets(t);
      setProjects(p);
      setClients(c);
      setInvoices(inv);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-accent" /></div>;

  const daysBack = parseInt(dateRange);
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - daysBack);
  const filtered = timesheets.filter(t => new Date(t.date || t.created_at) >= cutoff);

  // Total hours
  const totalHours = filtered.reduce((s, t) => s + (t.hours || t.duration || 0), 0);
  const totalBillable = filtered.filter(t => t.billable !== false).reduce((s, t) => s + (t.hours || t.duration || 0), 0);
  const totalRevenue = invoices.reduce((s, inv) => s + (inv.total || inv.amount || 0), 0);

  // Hours by day trend
  const dailyMap: Record<string, number> = {};
  const today = new Date();
  for (let i = daysBack - 1; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    dailyMap[d.toISOString().slice(0, 10)] = 0;
  }
  filtered.forEach(t => {
    const day = (t.date || t.created_at || '').slice(0, 10);
    if (dailyMap[day] !== undefined) dailyMap[day] += t.hours || t.duration || 0;
  });
  const trendData = Object.entries(dailyMap).map(([date, hours]) => ({
    date: date.slice(5),
    hours: Math.round(hours * 10) / 10,
  }));

  // Hours by project
  const projectHours: Record<string, { name: string; hours: number; billable: number }> = {};
  filtered.forEach(t => {
    const pName = t.project_name || projects.find(p => p.id === t.project_id)?.name || 'No Project';
    if (!projectHours[pName]) projectHours[pName] = { name: pName, hours: 0, billable: 0 };
    projectHours[pName].hours += t.hours || t.duration || 0;
    if (t.billable !== false) projectHours[pName].billable += t.hours || t.duration || 0;
  });
  const projectData = Object.values(projectHours)
    .sort((a, b) => b.hours - a.hours)
    .slice(0, 8);

  // Hours by client
  const clientHours: Record<string, number> = {};
  filtered.forEach(t => {
    const cName = t.client_name || 'Unassigned';
    clientHours[cName] = (clientHours[cName] || 0) + (t.hours || t.duration || 0);
  });
  const clientData = Object.entries(clientHours)
    .map(([name, value]) => ({ name, value: Math.round(value * 10) / 10 }))
    .sort((a, b) => b.value - a.value);

  // Billable vs Non-billable
  const billableHours = filtered.filter(t => t.billable !== false).reduce((s, t) => s + (t.hours || t.duration || 0), 0);
  const nonBillableHours = totalHours - billableHours;
  const utilizationData = [
    { name: 'Billable', value: Math.round(billableHours * 10) / 10 },
    { name: 'Non-Billable', value: Math.round(nonBillableHours * 10) / 10 },
  ].filter(d => d.value > 0);

  // Weekly pattern
  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const weeklyPattern = dayNames.map((name, dayIdx) => {
    const dayEntries = filtered.filter(t => {
      const d = new Date(t.date || t.created_at);
      return d.getDay() === dayIdx;
    });
    const hours = dayEntries.reduce((s, t) => s + (t.hours || t.duration || 0), 0);
    const count = dayEntries.length || 1;
    return { day: name, avgHours: Math.round((hours / Math.max(count, 1)) * 10) / 10, totalHours: Math.round(hours * 10) / 10 };
  });

  const formatHours = (h: number) => `${Math.floor(h)}h ${Math.round((h % 1) * 60)}m`;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <BarChart3 className="h-6 w-6 text-accent" /> Reports
        </h2>
        <select value={dateRange} onChange={e => setDateRange(e.target.value)}
          className="px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-accent/30">
          <option value="7">Last 7 days</option>
          <option value="14">Last 14 days</option>
          <option value="30">Last 30 days</option>
          <option value="90">Last 90 days</option>
        </select>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-white rounded-xl border p-4">
          <div className="flex items-center gap-2 mb-1">
            <Clock className="h-4 w-4 text-gray-400" />
            <span className="text-sm text-gray-500">Total Hours</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{formatHours(totalHours)}</p>
        </div>
        <div className="bg-white rounded-xl border p-4">
          <span className="text-sm text-gray-500">Billable Hours</span>
          <p className="text-2xl font-bold text-emerald-600">{formatHours(totalBillable)}</p>
        </div>
        <div className="bg-white rounded-xl border p-4">
          <span className="text-sm text-gray-500">Utilization</span>
          <p className="text-2xl font-bold text-indigo-600">
            {totalHours > 0 ? Math.round((billableHours / totalHours) * 100) : 0}%
          </p>
        </div>
        <div className="bg-white rounded-xl border p-4">
          <div className="flex items-center gap-2 mb-1">
            <Briefcase className="h-4 w-4 text-gray-400" />
            <span className="text-sm text-gray-500">Projects</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{projects.length}</p>
        </div>
        <div className="bg-white rounded-xl border p-4">
          <span className="text-sm text-gray-500">Revenue</span>
          <p className="text-2xl font-bold text-gray-900">{formatCurrency(totalRevenue)}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Hours Trend */}
        <div className="bg-white rounded-xl border p-5 lg:col-span-2">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-accent" /> Daily Hours Logged
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" fontSize={11} />
              <YAxis fontSize={11} />
              <Tooltip formatter={(val: number) => `${val}h`} />
              <Bar dataKey="hours" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Hours by Project */}
        <div className="bg-white rounded-xl border p-5">
          <h3 className="font-semibold text-gray-900 mb-4">Hours by Project</h3>
          {projectData.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-8">No time entries.</p>
          ) : (
            <div className="space-y-3">
              {projectData.map((p, i) => (
                <div key={p.name}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-700 truncate max-w-[200px]">{p.name}</span>
                    <span className="text-xs font-medium text-gray-500">{Math.round(p.hours * 10) / 10}h</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full rounded-full" style={{
                      width: `${(p.hours / projectData[0].hours) * 100}%`,
                      backgroundColor: COLORS[i % COLORS.length],
                    }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Billable Utilization Pie */}
        <div className="bg-white rounded-xl border p-5">
          <h3 className="font-semibold text-gray-900 mb-4">Billable Utilization</h3>
          {utilizationData.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-8">No data.</p>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={utilizationData} cx="50%" cy="50%" innerRadius={60} outerRadius={90} dataKey="value" paddingAngle={3}
                  label={({ name, value }) => `${name}: ${value}h`}>
                  <Cell fill="#10b981" />
                  <Cell fill="#94a3b8" />
                </Pie>
                <Tooltip formatter={(val: number) => `${val}h`} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Weekly Pattern */}
        <div className="bg-white rounded-xl border p-5 lg:col-span-2">
          <h3 className="font-semibold text-gray-900 mb-4">Weekly Pattern</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={weeklyPattern}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" fontSize={12} />
              <YAxis fontSize={11} />
              <Tooltip formatter={(val: number) => `${val}h`} />
              <Bar dataKey="totalHours" fill="#06b6d4" radius={[4, 4, 0, 0]} name="Total Hours" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
