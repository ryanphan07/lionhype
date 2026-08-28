import React, { useState, useEffect, useRef } from 'react';

export default function App() {
  const [logs, setLogs] = useState([]);
  const audioCtxRef = useRef(null);
  const audioBuffers = useRef({});

  useEffect(() => {
    // Initialize Web Audio Context
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    audioCtxRef.current = new AudioContextClass();

    // Preload sound effects
    const sfxTypes = ['gong', 'cymbals', 'airhorn', 'drumroll'];
    sfxTypes.forEach(sfx => {
      fetch(`/audio/${sfx}.wav`)
        .then(res => res.arrayBuffer())
        .then(data => audioCtxRef.current.decodeAudioData(data))
        .then(buf => {
          audioBuffers.current[sfx] = buf;
          console.log(`Loaded: ${sfx}`);
        })
        .catch(err => console.error(`Failed to load ${sfx}:`, err));
    });

    // WebSocket Connection
    const ws = new WebSocket('ws://localhost:8000/ws/analyze');
    ws.onmessage = (evt) => {
      const data = JSON.parse(evt.data);
      setLogs(prev => [data, ...prev]);

      if (data.sfx && audioBuffers.current[data.sfx]) {
        const src = audioCtxRef.current.createBufferSource();
        src.buffer = audioBuffers.current[data.sfx];
        src.connect(audioCtxRef.current.destination);
        src.start(0);
      }
    };

    ws.onopen = () => console.log("Connected to backend");
    ws.onerror = (err) => console.error("WS Error:", err);

    return () => {
      ws.close();
      if (audioCtxRef.current) {
        audioCtxRef.current.close();
      }
    };
  }, []);

  return (
    <div className="bg-slate-950 text-white min-h-screen p-6">
      <h1 className="text-2xl font-bold text-amber-400">🦁 LionHype AI Dashboard</h1>
      <div className="grid grid-cols-3 gap-6 mt-4">
        <div className="col-span-2">
          <video
            controls
            className="w-full rounded-lg bg-black border border-slate-700"
            src="/lion_dance.mp4"
          />
        </div>
        <div className="bg-slate-900 p-4 rounded-lg h-[400px] overflow-y-auto border border-slate-800">
          <h2 className="text-lg font-bold mb-4 text-amber-200">Live Roast Log</h2>
          {logs.map((l, i) => (
            <div key={i} className="mb-4 p-3 bg-slate-800 rounded border border-slate-700">
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs text-amber-400">{l.timestamp}</span>
                {l.sfx !== 'none' && (
                  <span className="text-xs px-2 py-1 bg-amber-900 text-amber-100 rounded">
                    [{l.sfx.toUpperCase()}]
                  </span>
                )}
              </div>
              <p className="text-sm italic">"{l.commentary}"</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
