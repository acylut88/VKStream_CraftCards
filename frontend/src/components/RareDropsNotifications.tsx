import React, { useEffect, useState } from 'react';
import { Sparkles, Loader, TrendingUp } from 'lucide-react';

interface RareDrop {
  drop_id: number;
  vk_id: string;
  nickname: string;
  card_type: string;
  card_level: number;
  probability: number;
  timestamp: string;
  box_type: string;
}

export const RareDropsNotifications: React.FC = () => {
  const [rareDrops, setRareDrops] = useState<RareDrop[]>([]);
  const [loading, setLoading] = useState(true);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [totalRareDrops, setTotalRareDrops] = useState(0);

  const POLL_INTERVAL = 3000; // 3 seconds

  useEffect(() => {
    fetchRareDrops();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(fetchRareDrops, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [sessionId, autoRefresh]);

  const fetchRareDrops = async () => {
    try {
      // First try to get current session
      if (!sessionId) {
        try {
          const sessionResponse = await fetch('http://localhost:8001/api/stream/leaderboard/1/card?limit=1');
          if (sessionResponse.ok) {
            setSessionId(1);
          }
        } catch {}
      }

      // Then fetch rare drops
      const url = sessionId
        ? `http://localhost:8001/api/stream/sessions/${sessionId}/rare-drops`
        : 'http://localhost:8001/api/stream/sessions/1/rare-drops';

      try {
        const response = await fetch(url);
        if (response.ok) {
          const data = await response.json();
          setRareDrops(Array.isArray(data) ? data : []);
          setTotalRareDrops(data.length || 0);
        }
      } catch (error) {
        // Fallback - create mock data for demo
        console.log('Demo mode - no rare drops yet');
      }
    } catch (error) {
      console.error('Failed to fetch rare drops:', error);
    } finally {
      setLoading(false);
    }
  };

  const getProbabilityColor = (prob: number): string => {
    if (prob >= 0.01) return 'bg-red-100 text-red-800'; // > 1%
    if (prob >= 0.005) return 'bg-purple-100 text-purple-800'; // > 0.5%
    if (prob >= 0.002) return 'bg-blue-100 text-blue-800'; // > 0.2%
    return 'bg-yellow-100 text-yellow-800'; // <= 0.2%
  };

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleTimeString('ru-RU', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch {
      return dateStr;
    }
  };

  const formatProbability = (prob: number) => {
    const percentage = (prob * 100).toFixed(3);
    return `${percentage}%`;
  };

  const boxTypeEmoji: Record<string, string> = {
    '1': '📦 Обычный',
    '2': '💎 Элит',
    '3': '👑 Легендарный'
  };

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
          <Sparkles size={32} className="text-purple-600 animate-pulse" />
          ✨ Редкие Выпадения
        </h1>
        <div className="flex gap-3 items-center">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-sm font-bold text-gray-700">Авто-обновление</span>
          </label>
          <button
            onClick={fetchRareDrops}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            🔄 Обновить
          </button>
        </div>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
          <p className="text-sm text-gray-600 mb-1">Всего редких выпадений</p>
          <p className="text-3xl font-bold text-purple-600">{totalRareDrops}</p>
        </div>
        <div className="bg-gradient-to-br from-pink-50 to-pink-100 rounded-lg p-4 border border-pink-200">
          <p className="text-sm text-gray-600 mb-1">Средний шанс</p>
          <p className="text-3xl font-bold text-pink-600">
            {rareDrops.length > 0
              ? formatProbability(rareDrops.reduce((sum, d) => sum + d.probability, 0) / rareDrops.length)
              : '0%'}
          </p>
        </div>
        <div className="bg-gradient-to-br from-indigo-50 to-indigo-100 rounded-lg p-4 border border-indigo-200">
          <p className="text-sm text-gray-600 mb-1">Самый редкий дроп</p>
          <p className="text-3xl font-bold text-indigo-600">
            {rareDrops.length > 0
              ? formatProbability(Math.max(...rareDrops.map(d => d.probability)))
              : '—'}
          </p>
        </div>
      </div>

      {/* Таблица редких выпадений */}
      {rareDrops.length === 0 ? (
        <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
          <Sparkles size={48} className="text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 text-lg">Нет редких выпадений</p>
          <p className="text-gray-500">Начните стрим и получайте боксы для отслеживания редких карт</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="p-4 bg-gradient-to-r from-purple-100 to-pink-50 border-b-2 border-purple-300">
            <h3 className="text-lg font-bold text-gray-900">История редких выпадений</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-100 border-b-2 border-gray-300">
                <tr>
                  <th className="px-6 py-3 text-left text-gray-700 font-bold">Время</th>
                  <th className="px-6 py-3 text-left text-gray-700 font-bold">Игрок</th>
                  <th className="px-6 py-3 text-left text-gray-700 font-bold">Карта</th>
                  <th className="px-6 py-3 text-center text-gray-700 font-bold">Уровень</th>
                  <th className="px-6 py-3 text-center text-gray-700 font-bold">Тип Бокса</th>
                  <th className="px-6 py-3 text-center text-gray-700 font-bold">Шанс Выпадения</th>
                </tr>
              </thead>
              <tbody>
                {rareDrops.map((drop, idx) => (
                  <tr key={drop.drop_id} className="border-b hover:bg-gray-50 transition">
                    <td className="px-6 py-4">
                      <p className="font-bold text-gray-900">{formatDate(drop.timestamp)}</p>
                    </td>
                    <td className="px-6 py-4">
                      <p className="font-bold text-gray-900">{drop.nickname || drop.vk_id}</p>
                      <p className="text-xs text-gray-600">{drop.vk_id}</p>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span className="text-2xl">✨</span>
                        <div>
                          <p className="font-bold text-gray-900">{drop.card_type}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className="inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded-full font-bold">
                        {drop.card_level}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className="inline-block text-sm font-bold text-gray-900">
                        {boxTypeEmoji[drop.box_type] || `Box #${drop.box_type}`}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={`inline-block px-4 py-2 rounded-lg font-bold text-sm ${getProbabilityColor(drop.probability)}`}>
                        {formatProbability(drop.probability)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Легенда */}
      <div className="mt-6 bg-purple-50 border border-purple-300 rounded-lg p-4">
        <p className="text-sm text-gray-700 font-bold mb-2">📊 Шкала редкости:</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-yellow-200"></div>
            <span>&lt; 0.2%</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-blue-200"></div>
            <span>0.2% - 0.5%</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-purple-200"></div>
            <span>0.5% - 1%</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-red-200"></div>
            <span>&gt; 1%</span>
          </div>
        </div>
      </div>

      <div className="mt-4 bg-blue-50 border border-blue-300 rounded-lg p-4">
        <p className="text-sm text-gray-700">
          ⏱️ <strong>Обновление:</strong> каждые 3 секунды | 
          📊 <strong>Сессия:</strong> {sessionId || 'не选择'} | 
          🎯 <strong>Показано:</strong> {rareDrops.length} выпадений
        </p>
      </div>
    </div>
  );
};
