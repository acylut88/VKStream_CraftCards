import React, { useEffect, useState } from 'react';
import { getLogs, LogEntry } from '../services/api';
import { Clock, Package, Zap } from 'lucide-react';

export const Logs: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'standard' | 'elite'>('all');

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const { data } = await getLogs(500);
        setLogs(data);
      } catch (error) {
        console.error('Failed to fetch logs:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 5000); // Обновление каждые 5 сек
    return () => clearInterval(interval);
  }, []);

  const filteredLogs = logs.filter(log => {
    if (filter === 'all') return true;
    if (filter === 'standard') return log.box_type === 'Стандарт';
    if (filter === 'elite') return log.box_type.includes('Элитный');
    return true;
  });

  if (loading) return <div className="p-8">Загрузка логов...</div>;

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 rounded ${
            filter === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-200'
          }`}
        >
          Все события
        </button>
        <button
          onClick={() => setFilter('standard')}
          className={`px-4 py-2 rounded ${
            filter === 'standard' ? 'bg-blue-600 text-white' : 'bg-gray-200'
          }`}
        >
          Стандартные
        </button>
        <button
          onClick={() => setFilter('elite')}
          className={`px-4 py-2 rounded ${
            filter === 'elite' ? 'bg-blue-600 text-white' : 'bg-gray-200'
          }`}
        >
          Элитные
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        {filteredLogs.length === 0 ? (
          <div className="p-8 text-center text-gray-500">Нет логов</div>
        ) : (
          <div className="divide-y">
            {filteredLogs.map((log, idx) => {
              const isElite = log.box_type.includes('Элитный');
              return (
                <div
                  key={idx}
                  className="p-4 hover:bg-gray-50 transition-colors border-l-4"
                  style={{
                    borderColor: isElite ? '#a855f7' : '#3b82f6'
                  }}
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2">
                      <Package
                        size={20}
                        color={isElite ? '#a855f7' : '#3b82f6'}
                      />
                      <div>
                        <p className="font-semibold">{log.nickname}</p>
                        <p className="text-sm text-gray-600">{log.box_type}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-yellow-600">{log.ac_won} AC</p>
                      <p className="text-sm text-gray-600 flex items-center justify-end gap-1">
                        <Clock size={14} />
                        {log.timestamp}
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-4 text-sm">
                    <div className="flex items-center gap-1">
                      <span className="text-gray-600">Карты:</span>
                      <span className="font-medium">{log.count}</span>
                    </div>
                    {log.rare_drops && (
                      <div className="flex items-center gap-1">
                        <span className="text-gray-600">🔥 Редкие:</span>
                        <span className="font-medium text-red-600">{log.rare_drops}</span>
                      </div>
                    )}
                    {log.merges && (
                      <div className="flex items-center gap-1">
                        <span className="text-gray-600">🛠 Мержи:</span>
                        <span className="font-medium text-purple-600">{log.merges}</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
