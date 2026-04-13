import React, { useState } from 'react';
import { giveBoxes, getUsers, User } from '../services/api';
import { Gift } from 'lucide-react';

export const BoxManager: React.FC = () => {
  const [selectedUserId, setSelectedUserId] = useState('');
  const [selectedNickname, setSelectedNickname] = useState('');
  const [boxCount, setBoxCount] = useState(1);
  const [boxType, setBoxType] = useState<'standard' | 'elite'>('standard');
  const [rarity, setRarity] = useState(1);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  React.useEffect(() => {
    const fetchUsers = async () => {
      try {
        const { data } = await getUsers();
        setUsers(data);
      } catch (error) {
        console.error('Failed to fetch users:', error);
      }
    };

    fetchUsers();
  }, []);

  const handleGiveBox = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUserId) {
      alert('Выберите пользователя');
      return;
    }

    setLoading(true);
    try {
      // Опреде ляем рарность (1-3 для элитных, 0 для стандартных)
      const actualRarity = boxType === 'elite' ? rarity : 0;

      const { data } = await giveBoxes(
        selectedUserId,
        boxCount,
        actualRarity,
        selectedNickname
      );

      setResult(data);
      setBoxCount(1);
      setSelectedUserId('');
      setSelectedNickname('');
      alert(`✅ ${boxCount} ${boxType === 'elite' ? 'элитных' : 'стандартных'} боксов добавлено!`);
    } catch (error: any) {
      alert(`❌ Ошибка: ${error.response?.data?.detail || 'Неизвестная ошибка'}`);
    } finally {
      setLoading(false);
    }
  };

  const selectedUser = users.find(u => u.vk_id === selectedUserId);

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Форма */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-6">Выдать боксы пользователю</h3>
          
          <form onSubmit={handleGiveBox} className="space-y-4">
            {/* Выбор пользователя */}
            <div>
              <label className="block text-sm font-medium mb-2">Выберите пользователя</label>
              <select
                value={selectedUserId}
                onChange={(e) => {
                  const user = users.find(u => u.vk_id === e.target.value);
                  setSelectedUserId(e.target.value);
                  setSelectedNickname(user?.nickname || '');
                }}
                className="w-full px-4 py-2 border rounded-lg"
              >
                <option value="">-- Выберите --</option>
                {users.map(user => (
                  <option key={user.vk_id} value={user.vk_id}>
                    {user.nickname} ({user.vk_id})
                  </option>
                ))}
              </select>
            </div>

            {/* Тип бокса */}
            <div>
              <label className="block text-sm font-medium mb-2">Тип бокса</label>
              <div className="flex gap-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="standard"
                    checked={boxType === 'standard'}
                    onChange={(e) => setBoxType(e.target.value as 'standard')}
                    className="mr-2"
                  />
                  Стандартный
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="elite"
                    checked={boxType === 'elite'}
                    onChange={(e) => setBoxType(e.target.value as 'elite')}
                    className="mr-2"
                  />
                  Элитный
                </label>
              </div>
            </div>

            {/* Рарность для элитных */}
            {boxType === 'elite' && (
              <div>
                <label className="block text-sm font-medium mb-2">Рарность</label>
                <select
                  value={rarity}
                  onChange={(e) => setRarity(parseInt(e.target.value))}
                  className="w-full px-4 py-2 border rounded-lg"
                >
                  <option value={1}>Уровень 1 (1 лвл карты)</option>
                  <option value={2}>Уровень 2 (1-2 лвл карты)</option>
                  <option value={3}>Уровень 3 (1-3 лвл карты)</option>
                </select>
              </div>
            )}

            {/* Количество */}
            <div>
              <label className="block text-sm font-medium mb-2">Количество боксов</label>
              <input
                type="number"
                min="1"
                max="100"
                value={boxCount}
                onChange={(e) => setBoxCount(parseInt(e.target.value))}
                className="w-full px-4 py-2 border rounded-lg"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white py-2 rounded-lg font-medium flex items-center justify-center gap-2"
            >
              <Gift size={20} />
              {loading ? 'Загрузка...' : 'Выдать боксы'}
            </button>
          </form>
        </div>

        {/* Информация об игроке */}
        {selectedUser && (
          <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Информация об игроке</h3>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 bg-white rounded">
                <span className="text-gray-700">Никнейм:</span>
                <span className="font-semibold">{selectedUser.nickname}</span>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-white rounded">
                <span className="text-gray-700">Звезды лояльности:</span>
                <span className="text-lg">{'⭐'.repeat(selectedUser.stars)}</span>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-white rounded">
                <span className="text-gray-700">ПА (заряды):</span>
                <span className="text-lg">{selectedUser.pa_charges} ⚡</span>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-white rounded">
                <span className="text-gray-700">Боксы сегодня:</span>
                <span className="font-semibold">
                  Ст. {selectedUser.std_boxes_today} / Эл. {selectedUser.elite_boxes_today}
                </span>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-white rounded">
                <span className="text-gray-700">AC (всего/сегодня):</span>
                <span className="font-bold text-yellow-600">
                  {selectedUser.ac_balance} / {selectedUser.ac_today}
                </span>
              </div>

              {/* Preview */}
              <div className="mt-6 p-4 bg-yellow-50 border border-yellow-300 rounded">
                <p className="text-sm text-gray-700">
                  📦 <strong>Предпросмотр:</strong> Будет выдано
                </p>
                <p className="text-lg font-bold text-center my-2">
                  {boxCount}x {boxType === 'elite' ? `Элитный (уровень ${rarity})` : 'Стандартный'}
                </p>
                <p className="text-sm text-gray-600 text-center">
                  {boxType === 'elite'
                    ? `Средняя рарность карт: Уровень 1-${rarity}`
                    : 'Прогрессивная сложность в зависимости от номера бокса'}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* История выданных боксов */}
      {result && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Результаты последней операции</h3>
          <div className="space-y-2">
            {result.results?.map((r: any, idx: number) => (
              <div key={idx} className="p-3 bg-gray-50 rounded border-l-4 border-green-500">
                <p className="font-medium">Бокс #{idx + 1}</p>
                <p className="text-sm text-gray-600">
                  Карты: {r.count} | Редкие: {r.rare_drops || 'нет'} | Мержи: {r.merges || 'нет'}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
