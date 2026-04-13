import React, { useEffect, useState } from 'react';
import { getUsers, deleteUser, updateUser, createUser, User } from '../services/api';
import { useAppStore } from '../store';
import { Trash2, Edit2, Plus, X } from 'lucide-react';

export const PlayerManagement: React.FC = () => {
  const { users, setUsers } = useAppStore();
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editData, setEditData] = useState<Partial<User>>({});
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createFormData, setCreateFormData] = useState({
    vk_id: '',
    nickname: '',
    stars: 3,
    pa_charges: 0
  });

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const { data } = await getUsers();
        setUsers(data);
      } catch (error) {
        console.error('Failed to fetch users:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
    const interval = setInterval(fetchUsers, 10000);
    return () => clearInterval(interval);
  }, [setUsers]);

  const filteredUsers = users.filter(u =>
    u.nickname.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.vk_id.includes(searchTerm)
  );

  const handleDelete = async (vk_id: string) => {
    if (window.confirm('Удалить пользователя полностью?')) {
      try {
        await deleteUser(vk_id);
        setUsers(users.filter(u => u.vk_id !== vk_id));
        alert('Пользователь удален');
      } catch (error) {
        alert('Ошибка при удалении');
      }
    }
  };

  const handleEdit = async (user: User) => {
    try {
      await updateUser(user.vk_id, editData);
      const updatedUsers = users.map(u =>
        u.vk_id === user.vk_id ? { ...u, ...editData } : u
      );
      setUsers(updatedUsers);
      setEditingId(null);
      setEditData({});
    } catch (error) {
      alert('Ошибка при сохранении');
    }
  };

  const handleCreate = async () => {
    if (!createFormData.vk_id.trim() || !createFormData.nickname.trim()) {
      alert('Заполни VK ID и никнейм!');
      return;
    }

    try {
      const { data } = await createUser(createFormData);
      setUsers([...users, data]);
      setCreateFormData({ vk_id: '', nickname: '', stars: 3, pa_charges: 0 });
      setShowCreateForm(false);
      alert('Пользователь зарегистрирован!');
    } catch (error: any) {
      alert(`Ошибка: ${error.response?.data?.detail || 'Не удалось создать пользователя'}`);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-gray-500">Загрузка...</div>;
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Управление игроками</h1>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition"
        >
          {showCreateForm ? <X size={20} /> : <Plus size={20} />}
          {showCreateForm ? 'Отмена' : 'Новый игрок'}
        </button>
      </div>

      {/* Форма регистрации */}
      {showCreateForm && (
        <div className="bg-green-50 border-2 border-green-300 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-bold text-green-900 mb-4">Регистрация нового игрока</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <input
              type="text"
              placeholder="VK ID (например: 123456789)"
              value={createFormData.vk_id}
              onChange={(e) => setCreateFormData({ ...createFormData, vk_id: e.target.value })}
              className="px-4 py-2 border border-green-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            />
            <input
              type="text"
              placeholder="Никнейм (игровое имя)"
              value={createFormData.nickname}
              onChange={(e) => setCreateFormData({ ...createFormData, nickname: e.target.value })}
              className="px-4 py-2 border border-green-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            />
            <input
              type="number"
              placeholder="Звезды (по умолчанию 3)"
              value={createFormData.stars}
              onChange={(e) => setCreateFormData({ ...createFormData, stars: parseInt(e.target.value) || 0 })}
              className="px-4 py-2 border border-green-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            />
            <input
              type="number"
              placeholder="PA заряды (по умолчанию 0)"
              value={createFormData.pa_charges}
              onChange={(e) => setCreateFormData({ ...createFormData, pa_charges: parseInt(e.target.value) || 0 })}
              className="px-4 py-2 border border-green-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>
          <button
            onClick={handleCreate}
            className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg transition"
          >
            Зарегистрировать игрока
          </button>
        </div>
      )}

      {/* Поиск */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Поиск по нику или ID..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Таблица игроков */}
      <div className="overflow-x-auto">
        <table className="w-full bg-white rounded-lg shadow-lg">
          <thead className="bg-gray-100 border-b-2 border-gray-300">
            <tr>
              <th className="px-6 py-3 text-left text-gray-700 font-bold">VK ID</th>
              <th className="px-6 py-3 text-left text-gray-700 font-bold">Никнейм</th>
              <th className="px-6 py-3 text-left text-gray-700 font-bold">Звезды</th>
              <th className="px-6 py-3 text-left text-gray-700 font-bold">PA Charges</th>
              <th className="px-6 py-3 text-left text-gray-700 font-bold">PA Status</th>
              <th className="px-6 py-3 text-left text-gray-700 font-bold">Баланс AC</th>
              <th className="px-6 py-3 text-left text-gray-700 font-bold">Действия</th>
            </tr>
          </thead>
          <tbody>
            {filteredUsers.map((user) => (
              <tr key={user.vk_id} className="border-b hover:bg-gray-50 transition">
                <td className="px-6 py-4 text-gray-800">{user.vk_id}</td>
                <td className="px-6 py-4">
                  {editingId === user.vk_id ? (
                    <input
                      type="text"
                      value={editData.nickname || user.nickname}
                      onChange={(e) => setEditData({ ...editData, nickname: e.target.value })}
                      className="px-2 py-1 border border-blue-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    user.nickname
                  )}
                </td>
                <td className="px-6 py-4">
                  {editingId === user.vk_id ? (
                    <input
                      type="number"
                      value={editData.stars || user.stars}
                      onChange={(e) => setEditData({ ...editData, stars: parseInt(e.target.value) || 0 })}
                      className="w-16 px-2 py-1 border border-blue-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    user.stars
                  )}
                </td>
                <td className="px-6 py-4">
                  {editingId === user.vk_id ? (
                    <input
                      type="number"
                      value={editData.pa_charges || user.pa_charges}
                      onChange={(e) => setEditData({ ...editData, pa_charges: parseInt(e.target.value) || 0 })}
                      className="w-16 px-2 py-1 border border-blue-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    user.pa_charges
                  )}
                </td>
                <td className="px-6 py-4">
                  {user.pa_active_today === 1 ? (
                    <span className="bg-green-100 text-green-800 px-3 py-1 rounded font-bold text-sm">
                      ✓ АКТИВЕН
                    </span>
                  ) : user.pa_charges > 0 ? (
                    <span className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded font-bold text-sm">
                      ⚡ Готов
                    </span>
                  ) : (
                    <span className="bg-gray-100 text-gray-800 px-3 py-1 rounded font-bold text-sm">
                      ✕ Нет
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 text-blue-600 font-bold">{user.ac_balance}</td>
                <td className="px-6 py-4 flex gap-3">
                  {editingId === user.vk_id ? (
                    <>
                      <button
                        onClick={() => handleEdit(user)}
                        className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded transition text-sm font-bold"
                      >
                        Сохранить
                      </button>
                      <button
                        onClick={() => {
                          setEditingId(null);
                          setEditData({});
                        }}
                        className="bg-gray-500 hover:bg-gray-600 text-white px-3 py-1 rounded transition text-sm font-bold"
                      >
                        Отмена
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={() => {
                          setEditingId(user.vk_id);
                          setEditData(user);
                        }}
                        className="flex items-center gap-2 bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded transition"
                      >
                        <Edit2 size={16} />
                        Редактировать
                      </button>
                      <button
                        onClick={() => handleDelete(user.vk_id)}
                        className="flex items-center gap-2 bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded transition"
                      >
                        <Trash2 size={16} />
                        Удалить
                      </button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredUsers.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          {searchTerm ? 'Игроки не найдены' : 'Нет зарегистрированных игроков'}
        </div>
      )}
    </div>
  );
};
