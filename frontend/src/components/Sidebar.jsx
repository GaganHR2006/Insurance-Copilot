import { NavLink } from 'react-router-dom';
import {
  Upload, MessageSquare, BarChart2, MapPin, CheckCircle, ShieldCheck
} from 'lucide-react';

const navItems = [
  { label: 'Upload Policy',  to: '/upload',      icon: Upload       },
  { label: 'AI Assistant',   to: '/chat',         icon: MessageSquare },
  { label: 'Risk Score',     to: '/risk',         icon: BarChart2    },
  { label: 'Hospital Finder',to: '/hospitals',    icon: MapPin       },
  { label: 'Eligibility',    to: '/eligibility',  icon: CheckCircle  },
];

export default function Sidebar() {
  return (
    <aside
      className="flex flex-col shrink-0 h-screen overflow-y-auto"
      style={{ width: 240, background: '#0D1322', borderRight: '1px solid rgba(255,255,255,0.06)' }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 pt-7 pb-8">
        <div
          className="flex items-center justify-center rounded-xl"
          style={{ width: 40, height: 40, background: 'rgba(0,212,170,0.15)', color: '#00D4AA' }}
        >
          <ShieldCheck size={22} strokeWidth={2} />
        </div>
        <span
          className="font-syne font-bold text-base leading-tight"
          style={{ color: '#F0F4FF' }}
        >
          Insurance<br />Copilot
        </span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 space-y-1">
        {navItems.map(({ label, to, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-150 group ${
                isActive
                  ? 'border-l-[3px] text-[#00D4AA]'
                  : 'border-l-[3px] border-transparent text-[#8892A4] hover:text-[#F0F4FF] hover:bg-white/5'
              }`
            }
            style={({ isActive }) =>
              isActive
                ? { borderColor: '#00D4AA', background: 'rgba(0,212,170,0.12)' }
                : {}
            }
          >
            {({ isActive }) => (
              <>
                <Icon
                  size={18}
                  strokeWidth={2}
                  style={{ color: isActive ? '#00D4AA' : undefined }}
                  className={!isActive ? 'group-hover:text-[#F0F4FF]' : ''}
                />
                <span className="font-dm">{label}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-5 py-5 flex items-center gap-2">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" style={{ background: '#00D4AA' }} />
          <span className="relative inline-flex h-2 w-2 rounded-full" style={{ background: '#00D4AA' }} />
        </span>
        <span className="text-xs font-dm" style={{ color: '#8892A4' }}>Powered by AI</span>
      </div>
    </aside>
  );
}
