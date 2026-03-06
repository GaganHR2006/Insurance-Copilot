import { useState } from 'react';
import { Search, Star, MapPin, CheckCircle, XCircle } from 'lucide-react';

const HOSPITALS = [
  {
    name: 'Apollo Hospitals Mumbai',
    city: 'Mumbai',
    network: true,
    treatments: ['Cardiac', 'Orthopaedics'],
    rating: 5,
    distance: '2.1 km',
  },
  {
    name: 'Lilavati Hospital',
    city: 'Mumbai',
    network: true,
    treatments: ['Cardiac', 'Neurology'],
    rating: 4,
    distance: '3.8 km',
  },
  {
    name: 'Kokilaben Dhirubhai Ambani Hospital',
    city: 'Mumbai',
    network: false,
    treatments: ['Cardiac'],
    rating: 5,
    distance: '6.2 km',
  },
  {
    name: 'Breach Candy Hospital',
    city: 'Mumbai',
    network: true,
    treatments: ['General Medicine', 'Cardiac'],
    rating: 3,
    distance: '4.5 km',
  },
];

function Stars({ count, total = 5 }) {
  return (
    <div className="flex gap-0.5">
      {Array.from({ length: total }).map((_, i) => (
        <Star
          key={i}
          size={13}
          fill={i < count ? '#FFB800' : 'none'}
          stroke={i < count ? '#FFB800' : '#8892A4'}
        />
      ))}
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="rounded-2xl p-5 space-y-3" style={{ background: '#1A2235', border: '1px solid rgba(255,255,255,0.05)' }}>
      <div className="h-5 w-3/4 rounded-lg skeleton" />
      <div className="h-3 w-1/3 rounded-lg skeleton" />
      <div className="h-3 w-1/2 rounded-lg skeleton" />
      <div className="flex gap-2 mt-2">
        <div className="h-6 w-20 rounded-full skeleton" />
        <div className="h-6 w-20 rounded-full skeleton" />
      </div>
    </div>
  );
}

export default function HospitalFinder() {
  const [city, setCity] = useState('');
  const [treatment, setTreatment] = useState('');
  const [insurer, setInsurer] = useState('');
  const [status, setStatus] = useState('idle'); // idle | loading | results
  const inputCls = "w-full rounded-xl px-4 py-3 text-sm font-dm bg-[#0D1322] border border-white/10 text-white focus:border-[#00D4AA] focus:outline-none focus:ring-1 focus:ring-[#00D4AA] placeholder:text-[#8892A4] transition-colors";

  const handleSearch = () => {
    setStatus('loading');
    setTimeout(() => setStatus('results'), 800);
  };

  return (
    <div className="page-enter flex gap-6 h-full">
      {/* Left panel */}
      <div
        className="shrink-0 rounded-2xl p-5 flex flex-col gap-4"
        style={{ width: 300, background: '#1A2235', border: '1px solid rgba(255,255,255,0.05)', alignSelf: 'start' }}
      >
        <h2 className="font-syne font-bold text-lg" style={{ color: '#F0F4FF' }}>Find Hospitals</h2>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-dm mb-1.5 font-medium" style={{ color: '#8892A4' }}>City</label>
            <input className={inputCls} placeholder="e.g. Mumbai" value={city} onChange={e => setCity(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-dm mb-1.5 font-medium" style={{ color: '#8892A4' }}>Treatment</label>
            <input className={inputCls} placeholder="e.g. Cardiac Surgery" value={treatment} onChange={e => setTreatment(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-dm mb-1.5 font-medium" style={{ color: '#8892A4' }}>Insurer</label>
            <select
              className={inputCls}
              value={insurer}
              onChange={e => setInsurer(e.target.value)}
              style={{ color: insurer ? '#F0F4FF' : '#8892A4' }}
            >
              <option value="" disabled>Select insurer</option>
              {['HDFC ERGO', 'Star Health', 'ICICI Lombard', 'Niva Bupa', 'Bajaj Allianz'].map(opt => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </div>
        </div>

        <button
          onClick={handleSearch}
          className="w-full flex items-center justify-center gap-2 font-bold rounded-xl px-6 py-3 hover:brightness-110 transition font-dm"
          style={{ background: '#00D4AA', color: '#0A0F1E' }}
        >
          <Search size={16} />
          Search Hospitals
        </button>
      </div>

      {/* Results panel */}
      <div className="flex-1 overflow-y-auto">
        {status === 'idle' && (
          <div className="h-full flex flex-col items-center justify-center" style={{ color: '#8892A4' }}>
            <MapPin size={48} strokeWidth={1} className="mb-4 opacity-30" />
            <p className="font-dm text-sm">Enter your details and search for hospitals</p>
          </div>
        )}

        {status === 'loading' && (
          <div className="space-y-4">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
        )}

        {status === 'results' && (
          <div className="space-y-4">
            {HOSPITALS.map((h) => (
              <div
                key={h.name}
                className="rounded-2xl p-5 hover:border-white/10 hover:-translate-y-0.5 transition-all duration-200"
                style={{ background: '#1A2235', border: '1px solid rgba(255,255,255,0.05)', boxShadow: '0 10px 30px rgba(0,0,0,0.25)' }}
              >
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div>
                    <h3 className="font-syne font-bold text-base mb-1" style={{ color: '#F0F4FF' }}>{h.name}</h3>
                    <div className="flex items-center gap-2">
                      <span
                        className="flex items-center gap-1 text-xs font-dm px-2 py-0.5 rounded-full"
                        style={{ background: 'rgba(0,212,170,0.1)', color: '#00D4AA', border: '1px solid rgba(0,212,170,0.25)' }}
                      >
                        <MapPin size={10} /> {h.city}
                      </span>
                      <span
                        className="text-xs font-dm px-2 py-0.5 rounded-full flex items-center gap-1"
                        style={
                          h.network
                            ? { background: 'rgba(0,212,170,0.1)', color: '#00D4AA', border: '1px solid rgba(0,212,170,0.3)' }
                            : { background: 'rgba(255,71,87,0.1)', color: '#FF4757', border: '1px solid rgba(255,71,87,0.3)' }
                        }
                      >
                        {h.network ? <CheckCircle size={10} /> : <XCircle size={10} />}
                        {h.network ? 'In Network' : 'Out of Network'}
                      </span>
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <Stars count={h.rating} />
                    <p className="text-xs font-dm mt-1" style={{ color: '#8892A4' }}>{h.distance}</p>
                  </div>
                </div>

                {/* Treatments */}
                <div className="flex flex-wrap gap-2 mb-3">
                  {h.treatments.map(t => (
                    <span
                      key={t}
                      className="text-xs font-dm px-2.5 py-1 rounded-full"
                      style={{ background: 'rgba(255,255,255,0.06)', color: '#8892A4' }}
                    >
                      {t}
                    </span>
                  ))}
                </div>

                <button
                  className="text-sm font-dm font-semibold px-4 py-2 rounded-xl transition-all hover:bg-[#00D4AA] hover:text-[#0A0F1E]"
                  style={{ border: '1px solid #00D4AA', color: '#00D4AA' }}
                >
                  View Details
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
