import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp, Loader } from 'lucide-react';

interface ACLeaderboardEntry {
  vk_id: string;
  nickname: string;
  rank: number;
  ac_earned_this_stream: number;
}

export const EventACFarming: React.FC = () => {
  const [leaderboard, setLeaderboard] = useState<ACLeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [totalAC, setTotalAC] = useState(0);

  const COLORS = ['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316', '#6366f1', '#14b8a6'];

  useEffect(() => {
    // Try to get current session
    const checkSession = async () => {
      try {
        const response = await fetch('http://localhost:8001/api/stream/leaderboard/1/ac/top?limit=20');
        if (response.ok) {
          const data = await response.json();
          setSessionId(1);
          setLeaderboard(data);
          
          // Calculate total AC
          const total = data.reduce((sum: number, entry: any) => sum + entry.ac_earned_this_stream, 0);
          setTotalAC(total);
        }
      } catch (error) {
        console.log('No active session yet');
      } finally {
        setLoading(false);
      }
    };

    checkSession();
  }, []);

  useEffect(() => {
    if (!sessionId) return;

    // Auto-refresh every 5 seconds
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8001/api/stream/leaderboard/${sessionId}/ac/top?limit=20`);
        if (response.ok) {
          const data = await response.json();
          setLeaderboard(data);
          
          const total = data.reduce((sum: number, entry: any) => sum + entry.ac_earned_this_stream, 0);
          setTotalAC(total);
        }
      } catch (error) {
        console.error('Failed to fetch leaderboard:', error);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [sessionId]);

  const chartData = leaderboard.slice(0, 10).map(entry => ({
    nickname: entry.nickname || entry.vk_id.substring(0, 6),
    AC: entry.ac_earned_this_stream
  }));

  const pieData = leaderboard.slice(0, 5).map(entry => ({
    name: entry.nickname || entry.vk_id.substring(0, 6),
    value: entry.ac_earned_this_stream
  }));

  if (loading) {
    return (
      <div className="flex justify-center items-center py-16">
        <Loader className="animate-spin text-blue-600" size={32} />
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <TrendingUp size={32} className="text-green-500" />
          💰 AC Фарминг
        </h1>
        <div className="text-right">
          <p className="text-sm text-gray-600">Всего AC за стрим</p>
          <p className="text-3xl font-bold text-green-600">{totalAC}</p>
        </div>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
          <p className="text-sm text-gray-600 mb-1">Средний AC на игрока</p>
          <p className="text-2xl font-bold text-blue-600">
            {leaderboard.length > 0 ? Math.round(totalAC / leaderboard.length) : 0}
          </p>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
          <p className="text-sm text-gray-600 mb-1">Максимум одного игрока</p>
          <p className="text-2xl font-bold text-green-600">
            {leaderboard.length > 0 ? Math.max(...leaderboard.map(e => e.ac_earned_this_stream)) : 0}
          </p>
        </div>
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
          <p className="text-sm text-gray-600 mb-1">Активных игроков</p>
          <p className="text-2xl font-bold text-purple-600">{leaderboard.length}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Столбчатая диаграмма */}
        <div className="bg-white rounded-lg shadow-lg p-4">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Топ-10 по AC</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="nickname" angle={-45} textAnchor="end" height={80} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="AC" fill="#10b981" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Круговая диаграмма */}
        <div className="bg-white rounded-lg shadow-lg p-4">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Распределение AC (Топ-5)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Таблица лидерборда */}
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="p-4 bg-gradient-to-r from-green-100 to-green-50 border-b-2 border-green-300">
          <h3 className="text-lg font-bold text-gray-900">Полный лидерборд</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-100 border-b-2 border-gray-300">
              <tr>
                <th className="px-6 py-3 text-left text-gray-700 font-bold">Место</th>
                <th className="px-6 py-3 text-left text-gray-700 font-bold">Никнейм</th>
                <th className="px-6 py-3 text-center text-gray-700 font-bold">AC Заработано</th>
                <th className="px-6 py-3 text-center text-gray-700 font-bold">% от всего</th>
              </tr>
            </thead>
            <tbody>
              {leaderboard.map((entry, idx) => (
                <tr key={entry.vk_id} className="border-b hover:bg-gray-50 transition">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2 text-lg font-bold">
                      {idx === 0 && <span>🥇</span>}
                      {idx === 1 && <span>🥈</span>}
                      {idx === 2 && <span>🥉</span>}
                      {idx >= 3 && <span className="text-gray-600">{idx + 1}.</span>}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <p className="font-bold text-gray-900">{entry.nickname || entry.vk_id}</p>
                    <p className="text-xs text-gray-600">{entry.vk_id}</p>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="inline-block bg-green-100 text-green-800 px-4 py-2 rounded-lg font-bold">
                      {entry.ac_earned_this_stream} AC
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <div className="flex justify-center">
                      <div
                        className="bg-blue-600 text-white px-3 py-1 rounded-full font-bold text-sm"
                        style={{ minWidth: '60px' }}
                      >
                        {totalAC > 0 ? Math.round((entry.ac_earned_this_stream / totalAC) * 100) : 0}%
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="mt-6 bg-green-50 border border-green-300 rounded-lg p-4">
        <p className="text-sm text-gray-700">
          ⏱️ <strong>Обновление:</strong> каждые 5 секунд | 
          📊 <strong>Сессия ID:</strong> {sessionId || 'N/A'} | 
          👥 <strong>Участников:</strong> {leaderboard.length}
        </p>
      </div>
    </div>
  );
};
