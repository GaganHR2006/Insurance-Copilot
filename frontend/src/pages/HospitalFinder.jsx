import { useState } from 'react';
import { Search, Star, MapPin, CheckCircle, XCircle, BedDouble, AlertCircle, ShieldCheck, ShieldAlert, Info } from 'lucide-react';

// ── Helpers ──────────────────────────────────────────────

function Stars({ count }) {
  return (
    <div className="flex gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <Star key={i} size={13}
          fill={i < Math.floor(count) ? '#FFB800' : 'none'}
          stroke={i < Math.floor(count) ? '#FFB800' : '#8892A4'} />
      ))}
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="rounded-2xl p-5 space-y-4" style={{ background: '#1A2235', border: '1px solid rgba(255,255,255,0.05)' }}>
      <div className="h-5 w-3/4 rounded-lg skeleton" />
      <div className="h-3 w-1/3 rounded-lg skeleton" />
      <div className="flex gap-2 mt-2">
        {[...Array(3)].map((_, i) => <div key={i} className="h-6 w-24 rounded-full skeleton" />)}
      </div>
      <div className="grid grid-cols-2 gap-3 mt-3">
        <div className="h-20 rounded-xl skeleton" />
        <div className="h-20 rounded-xl skeleton" />
      </div>
    </div>
  );
}

function occupancyMeta(pct) {
  if (pct < 70) return { borderColor: '#00C853', badgeBg: 'rgba(0,200,83,0.15)', badgeText: '#00C853', pill: 'Low Occupancy' };
  if (pct < 90) return { borderColor: '#FFD600', badgeBg: 'rgba(255,214,0,0.15)', badgeText: '#FFD600', pill: 'Moderate Occupancy' };
  return { borderColor: '#FF1744', badgeBg: 'rgba(255,23,68,0.15)', badgeText: '#FF1744', pill: `High Occupancy ${pct}%` };
}

function bedMeta(available, total) {
  const ratio = total > 0 ? available / total : 0;
  const pct = Math.round(ratio * 100);
  if (ratio > 0.5) return { color: '#00C853', status: 'Readily Available', pct };
  if (ratio >= 0.2) return { color: '#FFD600', status: 'Limited Availability', pct };
  return { color: '#FF1744', status: 'Critical — Very Few Beds', pct };
}

function BedCard({ icon, label, available, total }) {
  const { color, status, pct } = bedMeta(available, total);
  return (
    <div className="flex flex-col gap-1.5 p-3 rounded-xl"
      style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}>
      <div className="flex items-center gap-1.5 text-xs font-dm font-semibold" style={{ color: '#8892A4' }}>
        {icon} {label}
      </div>
      <div>
        <span className="font-syne font-bold text-xl" style={{ color: '#F0F4FF' }}>{available}</span>
        <span className="text-xs font-dm ml-1" style={{ color: '#8892A4' }}>available</span>
      </div>
      <p className="text-[11px] font-dm" style={{ color: '#8892A4' }}>out of {total} total</p>
      <div className="w-full rounded-full h-1.5" style={{ background: 'rgba(255,255,255,0.08)' }}>
        <div className="h-1.5 rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color, boxShadow: `0 0 6px ${color}80` }} />
      </div>
      <p className="text-[11px] font-dm font-medium" style={{ color }}>{status}</p>
    </div>
  );
}

const KNOWN_POLICIES = ['Star Health', 'HDFC Ergo', 'Bajaj Allianz', 'Care Health', 'Niva Bupa'];

const inputCls = "w-full rounded-xl px-4 py-3 text-sm font-dm bg-[#0D1322] border border-white/10 text-white focus:border-[#00D4AA] focus:outline-none focus:ring-1 focus:ring-[#00D4AA] placeholder:text-[#8892A4] transition-colors";

export default function HospitalFinder() {
  const [city, setCity] = useState('');
  const [treatment, setTreatment] = useState('');
  const [status, setStatus] = useState('idle');
  const [hospitals, setHospitals] = useState([]);
  const [policyCtx, setPolicyCtx] = useState(null);
  const [error, setError] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    setStatus('loading');
    setError('');
    setHospitals([]);
    setPolicyCtx(null);
    try {
      const storedPdf = localStorage.getItem('insurance_pdf_data');
      let pdfPolicyData = storedPdf ? JSON.parse(storedPdf) : null;
      if (pdfPolicyData && pdfPolicyData.extracted) {
        pdfPolicyData = pdfPolicyData.extracted;
      }

      const res = await fetch('/api/hospitals/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          city: city.trim(),
          treatment: treatment.trim(),
          pdf_policy: pdfPolicyData,
        }),
      });
      if (!res.ok) throw new Error(`Error ${res.status}`);
      const data = await res.json();
      // Each hospital already has bed_availability embedded by the backend
      setHospitals(data.hospitals);
      setPolicyCtx(data.policy_context || null);
      setStatus('results');
    } catch {
      setError('Could not reach backend. Make sure FastAPI server is running on port 8000.');
      setStatus('idle');
    }
  };

  return (
    <div className="page-enter flex gap-6 h-full">

      {/* ── Left Panel ─────────────────────────────── */}
      <div
        className="shrink-0 rounded-2xl p-5 flex flex-col gap-4"
        style={{ width: 280, background: '#1A2235', border: '1px solid rgba(255,255,255,0.05)', alignSelf: 'start' }}
      >
        <h2 className="font-syne font-bold text-lg" style={{ color: '#F0F4FF' }}>Find Hospitals</h2>
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-dm mb-1.5 font-medium" style={{ color: '#8892A4' }}>City</label>
            <input className={inputCls} placeholder="e.g. Mumbai" value={city} onChange={e => setCity(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-dm mb-1.5 font-medium" style={{ color: '#8892A4' }}>Treatment</label>
            <input className={inputCls} placeholder="e.g. cardiac surgery" value={treatment}
              onChange={e => setTreatment(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()} />
          </div>
        </div>
        <button
          onClick={handleSearch}
          className="w-full flex items-center justify-center gap-2 font-bold rounded-xl px-6 py-3 hover:brightness-110 transition font-dm"
          style={{ background: '#00D4AA', color: '#0A0F1E' }}
        >
          <Search size={16} /> Search
        </button>
        {error && <p className="text-xs font-dm" style={{ color: '#FF4757' }}>{error}</p>}

        {/* PDF policy summary in sidebar */}
        {policyCtx?.pdf_uploaded && (
          <div className="space-y-2 pt-2" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
            <p className="text-[10px] font-dm font-semibold uppercase tracking-wider" style={{ color: '#8892A4' }}>Active Policy</p>
            {policyCtx.user_insurer && (
              <div className="flex items-center gap-2 text-xs font-dm" style={{ color: '#00D4AA' }}>
                <ShieldCheck size={13} /> {policyCtx.user_insurer}
              </div>
            )}
            {policyCtx.policy_name && (
              <p className="text-xs font-dm" style={{ color: '#8892A4' }}>{policyCtx.policy_name}</p>
            )}
            {policyCtx.treatments_covered_in_policy?.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1">
                {(policyCtx.treatments_covered_in_policy || []).slice(0, 5).map(t => (
                  <span key={t} className="text-[10px] font-dm px-1.5 py-0.5 rounded-full capitalize"
                    style={{ background: 'rgba(0,212,170,0.1)', color: '#00D4AA' }}>
                    {t}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Results ────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto space-y-5 pb-4">

        {/* Idle */}
        {status === 'idle' && (
          <div className="h-full flex flex-col items-center justify-center gap-3" style={{ color: '#8892A4' }}>
            <MapPin size={48} strokeWidth={1} className="opacity-30" />
            <p className="font-dm text-sm">Enter city or treatment and search</p>
          </div>
        )}

        {/* Loading */}
        {status === 'loading' && (
          <div className="space-y-5"><SkeletonCard /><SkeletonCard /><SkeletonCard /></div>
        )}

        {/* Coverage warning banner */}
        {status === 'results' && policyCtx?.coverage_warning && (
          <div className="flex items-start gap-3 rounded-xl px-4 py-3 text-sm font-dm"
            style={{ background: 'rgba(255,71,87,0.1)', color: '#FF4757', border: '1px solid rgba(255,71,87,0.2)' }}>
            <ShieldAlert size={16} className="shrink-0 mt-0.5" />
            <span>{policyCtx.coverage_warning}</span>
          </div>
        )}

        {/* No results */}
        {status === 'results' && hospitals.length === 0 && (
          <div className="flex flex-col items-center justify-center gap-4 py-16 rounded-2xl"
            style={{ background: '#1A2235', border: '1px solid rgba(255,255,255,0.06)' }}>
            <span className="text-5xl">🏥</span>
            <p className="font-syne font-bold text-base" style={{ color: '#F0F4FF' }}>
              No hospitals found{treatment ? ` for "${treatment}"` : ''}{city ? ` in ${city}` : ''}
            </p>
            <p className="font-dm text-sm" style={{ color: '#8892A4' }}>
              Try searching with a different city or treatment name
            </p>
          </div>
        )}

        {/* Hospital Cards */}
        {status === 'results' && hospitals.map((h) => {
          // bed_availability is already embedded in every hospital by the backend
          const beds = h.bed_availability || null;
          const occ = beds?.occupancy_rate_percent ?? null;
          const meta = occ !== null ? occupancyMeta(occ) : null;
          const searchedTreatment = treatment.trim().toLowerCase();
          const pc = h.policy_context || {};
          const acceptsPolicy = pc.hospital_accepts_user_policy;
          const mentionedInPDF = pc.hospital_mentioned_in_pdf;

          return (
            <div
              key={h.id}
              className="rounded-xl overflow-hidden transition-all duration-200 hover:brightness-110"
              style={{
                background: '#1A2235',
                border: '1px solid rgba(255,255,255,0.08)',
                borderLeft: `4px solid ${meta ? meta.borderColor : 'rgba(0,212,170,0.4)'}`,
                boxShadow: '0 10px 30px rgba(0,0,0,0.25)',
              }}
            >
              {/* ── SECTION 1: HEADER ── */}
              <div className="flex items-start justify-between gap-3 p-5 pb-4">
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="font-syne font-bold text-lg" style={{ color: '#F0F4FF' }}>{h.name}</h3>
                    {/* Policy acceptance badge */}
                    {pc.user_insurer && (
                      acceptsPolicy === true ? (
                        <span className="flex items-center gap-1 text-[10px] font-dm font-bold px-2 py-0.5 rounded-full"
                          style={{ background: 'rgba(0,200,83,0.15)', color: '#00C853' }}>
                          <ShieldCheck size={10} /> Accepts {pc.user_insurer}
                        </span>
                      ) : acceptsPolicy === false ? (
                        <span className="flex items-center gap-1 text-[10px] font-dm font-bold px-2 py-0.5 rounded-full"
                          style={{ background: 'rgba(255,71,87,0.12)', color: '#FF4757' }}>
                          <ShieldAlert size={10} /> Not in {pc.user_insurer} network
                        </span>
                      ) : null
                    )}
                  </div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="flex items-center gap-1 text-xs font-dm px-2 py-0.5 rounded-full"
                      style={{ background: 'rgba(0,212,170,0.1)', color: '#00D4AA', border: '1px solid rgba(0,212,170,0.25)' }}>
                      <MapPin size={10} /> {h.city}
                    </span>
                    {meta && (
                      <span className="text-xs font-dm px-2 py-0.5 rounded-full font-medium"
                        style={{ background: meta.badgeBg, color: meta.badgeText }}>
                        {meta.pill}
                      </span>
                    )}
                    {mentionedInPDF && (
                      <span className="text-[10px] font-dm px-2 py-0.5 rounded-full"
                        style={{ background: 'rgba(0,212,170,0.1)', color: '#00D4AA' }}>
                        📄 In your policy
                      </span>
                    )}
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <Stars count={h.rating} />
                  <p className="text-xs font-dm mt-1" style={{ color: '#8892A4' }}>{h.rating} / 5</p>
                </div>
              </div>

              {/* ── SECTION 2: TREATMENT TAGS ── */}
              <div className="px-5 pb-4 space-y-2" style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 14 }}>
                <p className="text-[10px] font-dm font-semibold uppercase tracking-wider" style={{ color: '#8892A4' }}>
                  Available Treatments
                </p>
                <div className="flex flex-wrap gap-2">
                  {h.treatments.map(t => {
                    const isMatch = searchedTreatment && t.toLowerCase().includes(searchedTreatment);
                    return (
                      <span key={t}
                        className="text-xs font-dm px-2.5 py-1 rounded-full capitalize"
                        style={isMatch
                          ? { background: '#00BFA5', color: '#fff', fontWeight: 700 }
                          : { background: 'rgba(255,255,255,0.07)', color: '#8892A4' }
                        }>
                        {isMatch && '✓ '}{t}
                      </span>
                    );
                  })}
                </div>
                {/* Treatment coverage status from PDF */}
                {pc.treatment_covered_in_policy === false && (
                  <div className="flex items-center gap-1.5 text-xs font-dm mt-1"
                    style={{ color: '#FF4757' }}>
                    <Info size={12} />
                    This treatment may not be covered under your uploaded policy
                  </div>
                )}
                {pc.treatment_covered_in_policy === true && (
                  <div className="flex items-center gap-1.5 text-xs font-dm mt-1"
                    style={{ color: '#00D4AA' }}>
                    <CheckCircle size={12} />
                    Covered under your uploaded {pc.user_insurer || 'policy'}
                  </div>
                )}
              </div>

              {/* ── SECTIONS 3 + 4: BED / POLICIES ── */}
              {beds ? (
                <div className="grid grid-cols-2 gap-0" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                  {/* Section 3 — Bed Availability */}
                  <div className="p-5 space-y-3" style={{ borderRight: '1px solid rgba(255,255,255,0.06)' }}>
                    <p className="text-[10px] font-dm font-semibold uppercase tracking-wider" style={{ color: '#8892A4' }}>
                      Bed Availability
                    </p>
                    <BedCard icon="🏥" label="ICU Beds" available={beds.icu.available} total={beds.icu.total} />
                    <BedCard icon="🛏" label="General Beds" available={beds.general.available} total={beds.general.total} />
                  </div>
                  {/* Section 4 — Insurance Network */}
                  <div className="p-5 space-y-3">
                    <p className="text-[10px] font-dm font-semibold uppercase tracking-wider" style={{ color: '#8892A4' }}>
                      Accepted Policies
                    </p>
                    <div className="space-y-1.5">
                      {KNOWN_POLICIES.map(policy => {
                        const accepted = h.network_policies.some(
                          np => np.toLowerCase().includes(policy.toLowerCase())
                        );
                        const isUserPolicy = pc.user_insurer &&
                          pc.user_insurer.toLowerCase().includes(policy.toLowerCase());
                        return (
                          <div key={policy} className="flex items-center gap-2 text-xs font-dm">
                            {accepted
                              ? <CheckCircle size={13} style={{ color: '#00C853', flexShrink: 0 }} />
                              : <XCircle size={13} style={{ color: '#FF4757', flexShrink: 0 }} />
                            }
                            <span style={{
                              color: accepted ? '#F0F4FF' : '#8892A4',
                              textDecoration: accepted ? 'none' : 'line-through',
                            }}>
                              {policy}
                            </span>
                            {accepted && isUserPolicy && (
                              <span className="text-[10px] font-dm px-1.5 py-0.5 rounded-full"
                                style={{ background: 'rgba(0,212,170,0.15)', color: '#00D4AA' }}>
                                Your Policy
                              </span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              ) : (
                /* Policies only (no bed data available) */
                <div className="px-5 pb-4" style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 14 }}>
                  <p className="text-[10px] font-dm font-semibold uppercase tracking-wider mb-2" style={{ color: '#8892A4' }}>
                    Accepted Policies
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {KNOWN_POLICIES.map(policy => {
                      const accepted = h.network_policies.some(
                        np => np.toLowerCase().includes(policy.toLowerCase())
                      );
                      const isUserPolicy = pc.user_insurer &&
                        pc.user_insurer.toLowerCase().includes(policy.toLowerCase());
                      return (
                        <div key={policy} className="flex items-center gap-1.5 text-xs font-dm">
                          {accepted
                            ? <CheckCircle size={13} style={{ color: '#00C853', flexShrink: 0 }} />
                            : <XCircle size={13} style={{ color: '#FF4757', flexShrink: 0 }} />
                          }
                          <span style={{ color: accepted ? '#F0F4FF' : '#8892A4', textDecoration: accepted ? 'none' : 'line-through' }}>
                            {policy}
                          </span>
                          {accepted && isUserPolicy && (
                            <span className="text-[10px] font-dm px-1.5 py-0.5 rounded-full"
                              style={{ background: 'rgba(0,212,170,0.15)', color: '#00D4AA' }}>
                              Your Policy
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
