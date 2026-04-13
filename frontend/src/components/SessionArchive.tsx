import React, { useEffect, useState } from 'react';
import { Archive, Download, Loader, Calendar, Tag } from 'lucide-react';

interface SessionInfo {
  session_id: number;
  stream_date: string;
  stream_name: string;
  event_type: string;
  status: string;
  created_at: string;
  completed_at: string | null;
}

export const SessionArchive: React.FC = () => {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState<number | null>(null);
  const [selectedSession, setSelectedSession] = useState<number | null>(null);

  const eventTypeLabels: Record<string, string> = {
    'card': '🃏 Гонка карт',
    'ac': '💰 AC Фарминг',
    'both': '🎯 Оба события'
  };

  const eventTypeColors: Record<string, string> = {
    'card': 'bg-yellow-100 text-yellow-800 border-yellow-300',
    'ac': 'bg-green-100 text-green-800 border-green-300',
    'both': 'bg-purple-100 text-purple-800 border-purple-300'
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8001/api/stream/sessions');
      if (response.ok) {
        const data = await response.json();
        setSessions(data);
      }
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const exportCSV = async (sessionId: number) => {
    try {
      setExporting(sessionId);
      const response = await fetch(`http://localhost:8001/api/stream/sessions/${sessionId}/export-csv`);
      if (response.ok) {
        const data = await response.json();
        
        // Создаем Blob и скачиваем
        const blob = new Blob([data.content], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', data.filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch (error) {
      console.error('Failed to export CSV:', error);
    } finally {
      setExporting(null);
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
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
          <Archive size={32} className="text-blue-600" />
          📚 Архив Сессий
        </h1>
        <button
          onClick={fetchSessions}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          🔄 Обновить
        </button>
      </div>

      {sessions.length === 0 ? (
        <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
          <Archive size={48} className="text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 text-lg">Нет завершенных сессий</p>
          <p className="text-gray-500">Создайте первую сессию в разделе "События стрима"</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {sessions.map((session) => (
            <div
              key={session.session_id}
              className="bg-white rounded-lg shadow-md border border-gray-200 hover:shadow-lg transition p-6"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    {session.stream_name}
                  </h3>
                  <div className="flex flex-wrap gap-3 items-center">
                    <span className={`inline-block px-3 py-1 rounded-full text-sm font-bold border ${eventTypeColors[session.event_type] || eventTypeColors['both']}`}>
                      {eventTypeLabels[session.event_type] || session.event_type}
                    </span>
                    <span className="text-gray-600 flex items-center gap-1">
                      <Calendar size={16} />
                      {formatDate(session.stream_date)}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-sm text-gray-600">Session ID:</span>
                  <p className="text-lg font-mono font-bold text-gray-900">{session.session_id}</p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 mb-4 py-4 border-y border-gray-200">
                <div>
                  <p className="text-xs text-gray-600 uppercase tracking-wider">Статус</p>
                  <p className={`text-sm font-bold ${session.status === 'active' ? 'text-orange-600' : 'text-green-600'}`}>
                    {session.status === 'active' ? '🔴 Активна' : '✅ Завершена'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-600 uppercase tracking-wider">Начало</p>
                  <p className="text-sm text-gray-900">{formatDate(session.created_at)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600 uppercase tracking-wider">Завершение</p>
                  <p className="text-sm text-gray-900">
                    {session.completed_at ? formatDate(session.completed_at) : '—'}
                  </p>
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setSelectedSession(selectedSession === session.session_id ? null : session.session_id)}
                  className="flex-1 px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition font-bold"
                >
                  {selectedSession === session.session_id ? '👁️ Скрыть результаты' : '👁️ Просмотреть результаты'}
                </button>
                <button
                  onClick={() => exportCSV(session.session_id)}
                  disabled={exporting === session.session_id}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 transition font-bold flex items-center gap-2"
                >
                  {exporting === session.session_id ? (
                    <Loader size={18} className="animate-spin" />
                  ) : (
                    <Download size={18} />
                  )}
                  {exporting === session.session_id ? 'Загрузка...' : 'CSV'}
                </button>
              </div>

              {selectedSession === session.session_id && (
                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600 mb-2">Результаты для {eventTypeLabels[session.event_type]}:</p>
                  <p className="text-xs text-gray-500 italic">
                    Детальные результаты загружаются при экспорте CSV
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="mt-8 bg-blue-50 border border-blue-300 rounded-lg p-4">
        <p className="text-sm text-gray-700">
          📊 <strong>Информация:</strong> Архив хранит все завершенные потоковые сессии. 
          Используйте кнопку CSV для экспорта результатов для дальнейшего анализа.
        </p>
      </div>
    </div>
  );
};
