import { useEffect, useRef } from 'react';

const SCORE = 63;
const FACTORS = [
  { name: 'Waiting Period',          desc: '2-year waiting period for pre-existing diseases',          severity: 'High'   },
  { name: 'Hospital Not In Network', desc: 'Selected hospital is outside insurer\'s network',           severity: 'High'   },
  { name: 'Room Rent Cap',           desc: 'Room rent limited to ₹5,000/day — may cause deductions',  severity: 'Medium' },
  { name: 'Sub-limit on Surgery',    desc: 'Cardiac surgery capped at ₹1.5L regardless of sum insured',severity: 'Medium' },
  { name: 'Copayment Clause',        desc: '10% copay applicable for treatment in Tier-1 cities',      severity: 'Low'    },
];

const SEVERITY_COLOR = { High: '#FF4757', Medium: '#FFB800', Low: '#00D4AA' };
const METRIC_CARDS = [
  { label: 'Coverage Score', value: '71%',      sub: 'Above average' },
  { label: 'Claim Likelihood', value: 'Moderate', sub: 'Review factors' },
  { label: 'Policy Grade',  value: 'B+',         sub: 'Good standing'  },
];

// SVG donut gauge config
const R = 80;
const CIRC = 2 * Math.PI * R;
const ARC_COLOR = SCORE <= 40 ? '#00D4AA' : SCORE <= 70 ? '#FFB800' : '#FF4757';

export default function RiskDashboard() {
  const circleRef = useRef(null);

  useEffect(() => {
    // Animate stroke-dashoffset from full (hidden) to partial
    const offset = CIRC * (1 - SCORE / 100);
    if (circleRef.current) {
      circleRef.current.style.transition = 'stroke-dashoffset 1.2s ease';
      circleRef.current.style.strokeDashoffset = offset;
    }
  }, []);

  return (
    <div className="page-enter space-y-6">
      {/* Main 2-col grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Score card */}
        <div
          className="flex flex-col items-center justify-center gap-6 rounded-2xl p-8 hover:border-white/10 hover:-translate-y-0.5 transition-all duration-200"
          style={{ background: '#1A2235', border: '1px solid rgba(255,255,255,0.05)', boxShadow: '0 25px 50px rgba(0,0,0,0.35)' }}
        >
          <h2 className="font-syne font-bold text-lg w-full" style={{ color: '#F0F4FF' }}>Overall Risk Score</h2>

          {/* SVG Donut Gauge */}
          <div className="relative flex items-center justify-center">
            <svg width="200" height="200" viewBox="0 0 200 200">
              {/* Track */}
              <circle
                cx="100" cy="100" r={R}
                fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="16"
                strokeLinecap="round"
              />
              {/* Arc */}
              <circle
                ref={circleRef}
                cx="100" cy="100" r={R}
                fill="none"
                stroke={ARC_COLOR}
                strokeWidth="16"
                strokeLinecap="round"
                strokeDasharray={CIRC}
                strokeDashoffset={CIRC}         /* starts hidden */
                transform="rotate(-90 100 100)"
                style={{ filter: `drop-shadow(0 0 8px ${ARC_COLOR}60)` }}
              />
            </svg>
            {/* Center text */}
            <div className="absolute flex flex-col items-center">
              <span className="font-syne font-bold text-5xl leading-none" style={{ color: '#F0F4FF' }}>{SCORE}</span>
              <span className="font-dm text-sm mt-1" style={{ color: '#8892A4' }}>/ 100</span>
              <span className="font-dm text-xs mt-2 font-medium" style={{ color: ARC_COLOR }}>Risk Score</span>
            </div>
          </div>

          <p className="text-sm font-dm text-center leading-relaxed" style={{ color: '#8892A4' }}>
            Your policy carries <strong style={{ color: ARC_COLOR }}>moderate risk</strong>. Address the highlighted risk factors to improve your score.
          </p>
        </div>

        {/* Risk factors */}
        <div
          className="rounded-2xl p-6 hover:border-white/10 hover:-translate-y-0.5 transition-all duration-200"
          style={{ background: '#1A2235', border: '1px solid rgba(255,255,255,0.05)', boxShadow: '0 25px 50px rgba(0,0,0,0.35)' }}
        >
          <h2 className="font-syne font-bold text-lg mb-4" style={{ color: '#F0F4FF' }}>Risk Factors Detected</h2>
          <div className="space-y-3">
            {FACTORS.map((f) => (
              <div
                key={f.name}
                className="flex items-start gap-3 p-3 rounded-xl transition-colors hover:bg-white/5"
                style={{ border: '1px solid rgba(255,255,255,0.04)' }}
              >
                <span
                  className="mt-1 shrink-0 rounded-full"
                  style={{ width: 10, height: 10, background: SEVERITY_COLOR[f.severity], boxShadow: `0 0 6px ${SEVERITY_COLOR[f.severity]}` }}
                />
                <div className="flex-1 min-w-0">
                  <p className="font-dm font-semibold text-sm mb-0.5" style={{ color: '#F0F4FF' }}>{f.name}</p>
                  <p className="font-dm text-xs leading-relaxed" style={{ color: '#8892A4' }}>{f.desc}</p>
                </div>
                <span
                  className="shrink-0 text-[11px] font-bold font-dm px-2.5 py-1 rounded-full"
                  style={{
                    background: `${SEVERITY_COLOR[f.severity]}20`,
                    color: SEVERITY_COLOR[f.severity],
                    border: `1px solid ${SEVERITY_COLOR[f.severity]}40`,
                  }}
                >
                  {f.severity}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Summary metrics row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {METRIC_CARDS.map((m) => (
          <div
            key={m.label}
            className="rounded-2xl p-5 hover:border-white/10 hover:-translate-y-0.5 transition-all duration-200"
            style={{ background: '#1A2235', border: '1px solid rgba(255,255,255,0.05)', boxShadow: '0 10px 30px rgba(0,0,0,0.25)' }}
          >
            <p className="font-dm text-xs uppercase tracking-widest mb-2" style={{ color: '#8892A4' }}>{m.label}</p>
            <p className="font-syne font-bold text-3xl mb-1" style={{ color: '#F0F4FF' }}>{m.value}</p>
            <p className="font-dm text-xs" style={{ color: '#00D4AA' }}>{m.sub}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
