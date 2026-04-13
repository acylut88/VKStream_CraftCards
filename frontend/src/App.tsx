import React, { useState } from 'react';
import { Dashboard } from './components/Dashboard';
import { PlayerManagement } from './components/PlayerManagement';
import { BoxManager } from './components/BoxManager';
import { Logs } from './components/Logs';
import { EventsControl } from './components/EventsControl';
import { EventCardRace } from './components/EventCardRace';
import { EventACFarming } from './components/EventACFarming';
import { SessionArchive } from './components/SessionArchive';
import { RareDropsNotifications } from './components/RareDropsNotifications';
import {
  LayoutDashboard,
  Users,
  Gift,
  FileText,
  Trophy,
  LogOut,
  Menu,
  X
} from 'lucide-react';

function App() {
  const [currentPage, setCurrentPage] = useState<'dashboard' | 'players' | 'boxes' | 'logs' | 'events' | 'cardrace' | 'acfarm' | 'archive' | 'raredrops'>('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const navigation = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'events', label: '🎯 События стрима', icon: Trophy },
    { id: 'cardrace', label: '🃏 Гонка Карт', icon: Gift },
    { id: 'acfarm', label: '💰 AC Фарминг', icon: FileText },
    { id: 'raredrops', label: '✨ Редкие Карты', icon: FileText },
    { id: 'archive', label: '📚 Архив сессий', icon: FileText },
    { id: 'players', label: 'Управление игроками', icon: Users },
    { id: 'boxes', label: 'Выдать боксы', icon: Gift },
    { id: 'logs', label: 'Логи событий', icon: FileText },
  ];

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard': return <Dashboard />;
      case 'events': return <EventsControl />;
      case 'cardrace': return <EventCardRace />;
      case 'acfarm': return <EventACFarming />;
      case 'raredrops': return <RareDropsNotifications />;
      case 'archive': return <SessionArchive />;
      case 'players': return <PlayerManagement />;
      case 'boxes': return <BoxManager />;
      case 'logs': return <Logs />;
      default: return <Dashboard />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className={`
        ${sidebarOpen ? 'w-64' : 'w-0'} 
        bg-gray-900 text-white transition-all duration-300 overflow-hidden flex flex-col
      `}>
        <div className="p-6 border-b border-gray-800">
          <h1 className="text-2xl font-bold">🎮 VKStream</h1>
          <p className="text-sm text-gray-400">Admin Panel v1.0</p>
        </div>

        <nav className="flex-1 p-4 space-y-2">
          {navigation.map(item => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => {
                  setCurrentPage(item.id as any);
                  if (window.innerWidth < 768) setSidebarOpen(false);
                }}
                className={`
                  w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all
                  ${currentPage === item.id
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                  }
                `}
              >
                <Icon size={20} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="p-4 border-t border-gray-800">
          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-400 hover:bg-gray-800 hover:text-white transition-all">
            <LogOut size={20} />
            <span>Выход</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-gray-100 rounded-lg md:hidden"
          >
            {sidebarOpen ? <X /> : <Menu />}
          </button>
          
          <div className="flex-1 ml-4">
            <h2 className="text-2xl font-bold text-gray-800">
              {navigation.find(n => n.id === currentPage)?.label}
            </h2>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm text-gray-600">Admin User</p>
              <p className="text-xs text-gray-400">Sistema online</p>
            </div>
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full"></div>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-auto p-6">
          {renderPage()}
        </div>
      </div>
    </div>
  );
}

export default App;
