import React, { useEffect, useState } from 'react';
import { Trophy, Loader } from 'lucide-react';

interface LeaderboardEntry {
  vk_id: string;
  nickname: string;
  rank: number;
  current_value: number;
  card_distribution: string;
}

export const EventCardRace: React.FC = () => {
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [eventStatus, setEventStatus] = useState<'active' | 'completed' | 'no-session'>('no-session');

  useEffect(() => {
    // Try to get current session
    const checkSession = async () => {
      try {
        const response = await fetch('http://localhost:8001/api/stream/leaderboard/1/card');
        if (response.ok) {
          const data = await response.json();
          setSessionId(1);
          setEventStatus('active');
          setLeaderboard(data);
        } else {
          setEventStatus('no-session');
        }
      } catch (error) {
        console.log('No active session yet');
        setEventStatus('no-session');
      } finally {
        setLoading(false);
      }
    };

    checkSession();
  }, []);

  useEffect(() => {
    if (!sessionId || eventStatus === 'no-session') return;

    // Auto-refresh every 2 seconds
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8001/api/stream/leaderboard/${sessionId}/card?limit=20`);
        if (response.ok) {
          const data = await response.json();
          setLeaderboard(data);
        }
      } catch (error) {
        console.error('Failed to fetch leaderboard:', error);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [sessionId, eventStatus]);

  if (eventStatus === 'no-session') {
    return (
      <div className="p-8">
        <div className="text-center py-16">
          <Trophy size={64} className="mx-auto text-gray-400 mb-4" />
          <h2 className="text-2xl font-bold text-gray-700 mb-2">Нет активной гонки</h2>
          <p className="text-gray-600">Создай сессию события в панели управления событиями</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <Trophy size={32} className="text-yellow-500" />
          🏁 Гонка на Level 10
        </h1>
        <div>
          {eventStatus === 'active' && (
            <span className="bg-green-100 text-green-800 px-4 py-2 rounded-full font-bold">
              ✓ АКТИВНА
            </span>
          )}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center py-16">
          <Loader className="animate-spin text-blue-600" size={32} />
        </div>
      ) : leaderboard.length === 0 ? (
        <div className="text-center py-16 bg-gray-50 rounded-lg">
          <p className="text-gray-600 text-lg">Пока нет участников. Дай боксы игрокам!</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full bg-white rounded-lg shadow-lg">
            <thead>
              <tr className="bg-gradient-to-r from-yellow-100 to-yellow-50 border-b-2 border-yellow-300">
                <th className="px-6 py-4 text-left text-gray-900 font-bold">Место</th>
                <th className="px-6 py-4 text-left text-gray-900 font-bold">Никнейм</th>
                <th className="px-6 py-4 text-center text-gray-900 font-bold">Уровень</th>
                <th className="px-6 py-4 text-left text-gray-900 font-bold">Распределение карт</th>
              </tr>
            </thead>
            <tbody>
              {leaderboard.map((entry, idx) => (
                <tr
                  key={entry.vk_id}
                  className={`border-b transition-colors ${
                    idx === 0
                      ? 'bg-yellow-50 hover:bg-yellow-100'
                      : idx === 1
                      ? 'bg-gray-50 hover:bg-gray-100'
                      : 'hover:bg-gray-50'
                  }`}
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      {idx === 0 && <span className="text-3xl">🥇</span>}
                      {idx === 1 && <span className="text-3xl">🥈</span>}
                      {idx === 2 && <span className="text-3xl">🥉</span>}
                      {idx >= 3 && (
                        <span className="text-lg font-bold text-gray-600 w-6">{idx + 1}.</span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <p className="font-bold text-gray-900">{entry.vk_id}</p>
                    <p className="text-sm text-gray-600">{entry.nickname}</p>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <div className="flex justify-center">
                      <div
                        className={`text-2xl font-bold px-4 py-2 rounded-lg ${
                          entry.current_value === 10
                            ? 'bg-green-100 text-green-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}
                      >
                        {entry.current_value}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-700">
                      {entry.card_distribution ? (
                        <div className="space-y-1">
                          {JSON.parse(entry.card_distribution || '[]').map((card: any, i: number) => (
                            <span
                              key={i}
                              className="inline-block bg-purple-100 text-purple-800 px-2 py-1 rounded mr-1 mb-1 text-xs"
                            >
                              {card.card_type}-{card.card_level} ×{card.quantity}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-gray-500">-</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-6 bg-blue-50 border border-blue-300 rounded-lg p-4">
        <p className="text-sm text-gray-700">
          ⏱️ <strong>Обновление:</strong> каждые 2 секунды | 
          📊 <strong>Сессия ID:</strong> {sessionId || 'N/A'} | 
          👥 <strong>Участников:</strong> {leaderboard.length}
        </p>
      </div>
    </div>
  );
};
