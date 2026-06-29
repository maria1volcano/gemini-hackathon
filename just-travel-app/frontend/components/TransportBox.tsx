"use client";

interface TransportBoxProps {
  data: {
    originCity?: string;
    destCity?: string;
    flightType?: string;
    maxStopoverTime?: number | string;
    [key: string]: any;  // Allow additional form fields
  };
}

export default function TransportBox({ data }: TransportBoxProps) {
  return (
    <div className="bg-white/[0.03] backdrop-blur-xl p-6 rounded-2xl border border-white/10 mb-6">
      <h3 className="text-pink-400 font-mono font-bold uppercase text-sm mb-4 flex items-center gap-2">
        ✈️ Smart Routing
      </h3>

      {/* Outbound Flight */}
      <div className="flex items-center justify-between bg-white/5 p-4 rounded-xl border border-white/10 mb-3">
        <div>
          <p className="text-xs text-green-400/70 font-bold uppercase">Outbound</p>
          <p className="font-black text-white">{data.originCity || 'N/A'}</p>
        </div>
        <div className="text-green-400 text-xl">✈️ →</div>
        <div>
          <p className="text-xs text-green-400/70 font-bold uppercase">Arrival</p>
          <p className="font-black text-white">{data.destCity || 'N/A'}</p>
        </div>
      </div>

      {/* Return Flight */}
      <div className="flex items-center justify-between bg-white/5 p-4 rounded-xl border border-white/10">
        <div>
          <p className="text-xs text-orange-400/70 font-bold uppercase">Return</p>
          <p className="font-black text-white">{data.destCity || 'N/A'}</p>
        </div>
        <div className="text-orange-400 text-xl">✈️ →</div>
        <div>
          <p className="text-xs text-orange-400/70 font-bold uppercase">Arrival</p>
          <p className="font-black text-white">{data.originCity || 'N/A'}</p>
        </div>
      </div>

      <div className="mt-4 text-sm text-white/60 font-mono">
        Mode: <span className="font-bold text-white/80">{data.flightType === 'direct' ? 'Direct Flight' : `Stops (Max ${data.maxStopoverTime || 2}h)`}</span>
      </div>
    </div>
  );
}
