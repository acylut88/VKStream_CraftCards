import React, { useEffect, useState } from 'react';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import { getAnalytics } from '../services/api';
import { Users, Zap, Gift, Coins, TrendingUp } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const { data } = await getAnalytics();
        setAnalytics(data);
      } catch (error) {
        console.error('Failed to fetch analytics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 30000); // Обновление каждые 30 сек
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="p-8">Загуска...</div>;
  if (!analytics) return <div className="p-8">Ошибка загрузки данных</div>;

  const StatCard = ({ icon: Icon, label, value, color }: any) => (
    <div className={`bg-${color}-50 border border-${color}-200 rounded-lg p-6`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{label}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
        </div>
        <Icon className={`w-12 h-12 text-${color}-500`} />
      </div>
    </div>
  );

  return (
    <div className="space-y-8">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Users}
          label="Всего игроков"
          value={analytics.total_users}
          color="blue"
        />
        <StatCard
          icon={TrendingUp}
          label="Активных"
          value={analytics.active_users}
          color="green"
        />
        <StatCard
          icon={Gift}
          label="Всего боксов"
          value={analytics.total_boxes}
          color="purple"
        />
        <StatCard
          icon={Coins}
          label="Всего AC"
          value={analytics.total_ac}
          color="yellow"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Box Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Распределение боксов</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={[
                  { name: 'Стандарт', value: analytics.box_stats.std_count },
                  { name: 'Элит', value: analytics.box_stats.elite_count },
                ]}
                cx="50%"
                cy="50%"
                outerRadius={80}
                label
              >
                <Cell fill="#3b82f6" />
                <Cell fill="#8b5cf6" />
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Top Players */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">ТОП 10 игроков</h3>
          <div className="space-y-3">
            {analytics.top_players.map((player: any, idx: number) => (
              <div key={idx} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                <div>
                  <p className="font-medium">{idx + 1}. {player.nickname}</p>
                  <p className="text-sm text-gray-600">{player.boxes} боксов</p>
                </div>
                <span className="font-bold text-lg text-yellow-600">{player.ac} AC</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Statistics */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Средние показатели</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-600">Боксов/игрок</p>
            <p className="text-2xl font-bold">{analytics.avg_boxes_per_user.toFixed(1)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">AC/игрок</p>
            <p className="text-2xl font-bold">{analytics.avg_ac_per_user.toFixed(0)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Всего логов</p>
            <p className="text-2xl font-bold">{analytics.logs_count}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Активность</p>
            <p className="text-2xl font-bold">
              {analytics.total_users > 0
                ? Math.round((analytics.active_users / analytics.total_users) * 100)
                : 0}%
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
