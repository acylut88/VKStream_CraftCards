import React, { useEffect, useState } from 'react';
import { getUsers, deleteUser, updateUser, User } from '../services/api';
import { useAppStore } from '../store';
import { Trash2, Edit2, ChevronDown } from 'lucide-react';

export const PlayerManagement: React.FC = () => {
  const { users, setUsers } = useAppStore();
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editData, setEditData] = useState<Partial<User>>({});
  const [searchTerm, setSearchTerm] = useState('');

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
    const interval = setInterval(fetchUsers, 10000); // Обновление каждые 10 сек
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
      alert('Пользователь обновлен');
    } catch (error) {
      alert('Ошибка при обновлении');
    }
  };

  if (loading) return <div className="p-8">Загрузка игроков...</div>;

  return (
    <div className="space-y-4">
      <div>
        <input
          type="text"
          placeholder="Поиск по нику или ID..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-4 py-2 border rounded-lg"
        />
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-semibold">ID / Ник</th>
              <th className="px-6 py-3 text-left text-sm font-semibold">Звезды</th>
              <th className="px-6 py-3 text-left text-sm font-semibold">ПА</th>
              <th className="px-6 py-3 text-left text-sm font-semibold">Боксы (Ст/Эл)</th>
              <th className="px-6 py-3 text-left text-sm font-semibold">AC</th>
              <th className="px-6 py-3 text-left text-sm font-semibold">Действия</th>
            </tr>
          </thead>
          <tbody>
            {filteredUsers.map((user) => (
              <tr key={user.vk_id} className="border-t hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div>
                    <p className="font-medium">{user.nickname}</p>
                    <p className="text-sm text-gray-600">{user.vk_id}</p>
                  </div>
                </td>
                <td className="px-6 py-4">
                  {editingId === user.vk_id ? (
                    <input
                      type="number"
                      value={editData.stars ?? user.stars}
                      onChange={(e) =>
                        setEditData({ ...editData, stars: parseInt(e.target.value) })
                      }
                      className="w-12 px-2 py-1 border rounded"
                    />
                  ) : (
                    <span className="text-lg">{'⭐'.repeat(user.stars)}</span>
                  )}
                </td>
                <td className="px-6 py-4">
                  {editingId === user.vk_id ? (
                    <input
                      type="number"
                      value={editData.pa_charges ?? user.pa_charges}
                      onChange={(e) =>
                        setEditData({ ...editData, pa_charges: parseInt(e.target.value) })
                      }
                      className="w-12 px-2 py-1 border rounded"
                    />
                  ) : (
                    <span>{user.pa_charges} ⚡</span>
                  )}
                </td>
                <td className="px-6 py-4">
                  {user.std_boxes_today} / {user.elite_boxes_today}
                </td>
                <td className="px-6 py-4 font-semibold text-yellow-600">
                  {user.ac_balance} AC
                </td>
                <td className="px-6 py-4 flex gap-2">
                  {editingId === user.vk_id ? (
                    <>
                      <button
                        onClick={() => handleEdit(user)}
                        className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600"
                      >
                        ✓
                      </button>
                      <button
                        onClick={() => setEditingId(null)}
                        className="px-3 py-1 bg-gray-500 text-white rounded hover:bg-gray-600"
                      >
                        ✕
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={() => {
                          setEditingId(user.vk_id);
                          setEditData(user);
                        }}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                      >
                        <Edit2 size={18} />
                      </button>
                      <button
                        onClick={() => handleDelete(user.vk_id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded"
                      >
                        <Trash2 size={18} />
                      </button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
