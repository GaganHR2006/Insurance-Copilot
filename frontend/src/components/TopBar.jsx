import NotificationBell from './NotificationBell';

export default function TopBar({ title }) {
  return (
    <header
      className="shrink-0 flex items-center justify-between px-6 z-50 relative"
      style={{
        height: 64,
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        background: 'rgba(10,15,30,0.8)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        position: 'relative',
        zIndex: 50
      }}
    >
      {/* Left: page title */}
      <h1
        className="font-syne font-bold text-lg"
        style={{ color: '#F0F4FF' }}
      >
        {title}
      </h1>

      {/* Right: controls */}
      <div className="flex items-center gap-4">
        {/* Notification bell */}
        <NotificationBell />

        {/* Status pill */}
        <div
          className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium font-dm"
          style={{ background: 'rgba(0,212,170,0.12)', color: '#00D4AA', border: '1px solid rgba(0,212,170,0.25)' }}
        >
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" style={{ background: '#00D4AA' }} />
            <span className="relative inline-flex h-2 w-2 rounded-full" style={{ background: '#00D4AA' }} />
          </span>
          Policy Active
        </div>

        {/* User avatar */}
        <div
          className="flex items-center justify-center rounded-full font-syne font-bold text-sm cursor-pointer"
          style={{ width: 38, height: 38, background: 'linear-gradient(135deg, #00D4AA, #0090FF)', color: '#0A0F1E' }}
          title="Priya Singh"
        >
          SC
        </div>
      </div>
    </header>
  );
}
