import React, { useState } from 'react';
import { startStreamDay, createStreamSession, finishStreamSession } from '../services/api';
import { Play, StopCircle, Settings } from 'lucide-react';

export const EventsControl: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [activeSession, setActiveSession] = useState<any>(null);
  const [showSessionForm, setShowSessionForm] = useState(false);
  const [sessionForm, setSessionForm] = useState({
    event_type: 'both', // 'card' | 'ac_farming' | 'both'
    stream_name: ''
  });

  const handleStartDay = async () => {
    setLoading(true);
    try {
      const response = await startStreamDay();
      alert(`✅ Стрим начат! ${response.data.users_reset} игроков сброшены.`);
      // Update UI or refresh data
    } catch (error: any) {
      alert(`❌ Ошибка: ${error.response?.data?.detail || 'Failed to start day'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSession = async () => {
    if (!sessionForm.stream_name.trim()) {
      alert('Введи название стрима');
      return;
    }

    setLoading(true);
    try {
      const response = await createStreamSession(sessionForm.event_type, sessionForm.stream_name);
      setActiveSession(response.data);
      setShowSessionForm(false);
      alert(`✅ Сессия создана! ID: ${response.data.session_id}`);
    } catch (error: any) {
      alert(`❌ Ошибка: ${error.response?.data?.detail || 'Failed to create session'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleFinishSession = async () => {
    if (!activeSession) {
      alert('Нет активной сессии');
      return;
    }

    if (!window.confirm('Завершить текущую сессию?')) return;

    setLoading(true);
    try {
      await finishStreamSession(activeSession.session_id);
      setActiveSession(null);
      alert('✅ Сессия завершена!');
    } catch (error: any) {
      alert(`❌ Ошибка: ${error.response?.data?.detail || 'Failed to finish session'}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">🎮 Панель управления событиями</h1>

      {/* Старт стрима */}
      <div className="bg-blue-50 border-2 border-blue-300 rounded-lg p-6 mb-6">
        <h2 className="text-xl font-bold text-blue-900 mb-4">1. Начало стрима</h2>
        <p className="text-gray-700 mb-4">
          Нажми кнопку для сброса PA status и подготовки всех игроков к новому дню.
        </p>
        <button
          onClick={handleStartDay}
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition flex items-center justify-center gap-2"
        >
          <Play size={24} />
          🎬 НАЧАТЬ СТРИМ
        </button>
      </div>

      {/* Управление сессиями событий */}
      <div className="bg-purple-50 border-2 border-purple-300 rounded-lg p-6 mb-6">
        <h2 className="text-xl font-bold text-purple-900 mb-4">2. События стрима</h2>
        
        {activeSession ? (
          <div className="bg-white border-2 border-purple-200 rounded-lg p-4 mb-4">
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p className="text-sm text-gray-600">Session ID</p>
                <p className="text-lg font-bold text-purple-600">{activeSession.session_id}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Событие</p>
                <p className="text-lg font-bold">
                  {activeSession.event_type === 'both' ? '🎯 Оба' : 
                   activeSession.event_type === 'card' ? '🃏 Карты' : 
                   '💰 AC'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Название</p>
                <p className="text-lg font-bold">{activeSession.stream_name}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Статус</p>
                <p className="text-lg font-bold text-green-600">✓ АКТИВНА</p>
              </div>
            </div>
            <button
              onClick={handleFinishSession}
              disabled={loading}
              className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-lg transition flex items-center justify-center gap-2"
            >
              <StopCircle size={20} />
              ⏹ ЗАВЕРШИТЬ СЕССИЮ
            </button>
          </div>
        ) : (
          <div>
            {!showSessionForm ? (
              <button
                onClick={() => setShowSessionForm(true)}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-4 rounded-lg transition flex items-center justify-center gap-2"
              >
                <Settings size={24} />
                ⚙️ СОЗДАТЬ СЕССИЮ СОБЫТИЯ
              </button>
            ) : (
              <div className="bg-white border-2 border-purple-200 rounded-lg p-4">
                <div className="mb-4">
                  <label className="block text-sm font-bold text-gray-700 mb-2">Тип события</label>
                  <select
                    value={sessionForm.event_type}
                    onChange={(e) => setSessionForm({ ...sessionForm, event_type: e.target.value })}
                    className="w-full px-4 py-2 border border-purple-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="card">🃏 Гонка на Level 10</option>
                    <option value="ac_farming">💰 AC Фарм</option>
                    <option value="both">🎯 Оба события</option>
                  </select>
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-bold text-gray-700 mb-2">Название стрима</label>
                  <input
                    type="text"
                    placeholder="Например: 'Стрим 13.04 - Гонка'"
                    value={sessionForm.stream_name}
                    onChange={(e) => setSessionForm({ ...sessionForm, stream_name: e.target.value })}
                    className="w-full px-4 py-2 border border-purple-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handleCreateSession}
                    disabled={loading}
                    className="flex-1 bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded-lg transition"
                  >
                    ✓ Создать
                  </button>
                  <button
                    onClick={() => setShowSessionForm(false)}
                    className="flex-1 bg-gray-500 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded-lg transition"
                  >
                    Отмена
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
        <p className="text-xs text-gray-600 mt-4 italic">
          Сессия отслеживает события: гонка на level 10, AC фарм, редкие дропы
        </p>
      </div>

      {/* Справка */}
      <div className="bg-gray-50 border border-gray-300 rounded-lg p-4">
        <h3 className="font-bold text-gray-900 mb-2">📋 Как использовать:</h3>
        <ol className="text-sm text-gray-700 space-y-1 list-decimal list-inside">
          <li>Нажми "НАЧАТЬ СТРИМ" в начале дня (сбрасывает PA статусы)</li>
          <li>Опционально создай сессию события для отслеживания</li>
          <li>Давай боксы игрокам через админку</li>
          <li>События будут автоматически отслеживаться</li>
          <li>Нажми "ЗАВЕРШИТЬ СЕССИЮ" в конце события</li>
        </ol>
      </div>
    </div>
  );
};
