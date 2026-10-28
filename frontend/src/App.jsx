import { useCallback, useEffect, useRef, useState } from 'react';
import axios from 'axios';
import VideoPlayer from './components/VideoPlayer';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
const WS_BASE = API_BASE.replace(/^http/, 'ws');

const MAX_RECONNECTS = 5;
const MAX_BACKOFF_MS = 10000;

const PHASE_LABELS = {
  uploading: 'Uploading',
  extracting: 'Extracting frames',
  analyzing: 'Analyzing video',
  synthesizing: 'Generating audio',
  completed: 'Done',
  error: 'Failed',
};

const errorDetail = (error, fallback) => {
  const detail = error?.response?.data?.detail;
  return typeof detail === 'string' && detail ? detail : fallback;
};

function App() {
  const [commentaryQuips, setCommentaryQuips] = useState([]);
  const [videoUrl, setVideoUrl] = useState(null);
  const [processingStatus, setProcessingStatus] = useState('idle');
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const socketRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const attemptsRef = useRef(0);
  const jobIdRef = useRef(null);
  const terminalRef = useRef(false);
  const closedRef = useRef(false);
  const objectUrlRef = useRef(null);

  const teardownSocket = useCallback(() => {
    closedRef.current = true;
    clearTimeout(reconnectTimerRef.current);
    reconnectTimerRef.current = null;
    const socket = socketRef.current;
    socketRef.current = null;
    if (socket) {
      socket.onopen = socket.onmessage = socket.onerror = socket.onclose = null;
      socket.close();
    }
  }, []);

  const fail = useCallback((message) => {
    terminalRef.current = true;
    setProcessingStatus('error');
    setErrorMessage(message);
    toast.error(message, { position: 'top-right' });
  }, []);

  const fetchResult = useCallback(async (jobId) => {
    try {
      const { data } = await axios.get(`${API_BASE}/api/jobs/${jobId}`);
      if (jobIdRef.current !== jobId) return;
      setCommentaryQuips(Array.isArray(data.result?.quips) ? data.result.quips : []);
      setProcessingStatus('completed');
      setProgress(100);
    } catch (error) {
      if (jobIdRef.current !== jobId) return;
      fail(errorDetail(error, 'Failed to fetch the commentary result.'));
    }
  }, [fail]);

  const connectSocket = useCallback((jobId) => {
    const open = () => {
      const socket = new WebSocket(`${WS_BASE}/ws/analyze/${jobId}`);
      socketRef.current = socket;

      socket.onmessage = (event) => {
        attemptsRef.current = 0;
        let msg;
        try {
          msg = JSON.parse(event.data);
        } catch {
          return;
        }

        if (msg.status === 'completed') {
          terminalRef.current = true;
          setStatusMessage(msg.message || '');
          fetchResult(jobId);
        } else if (msg.status === 'error') {
          fail(msg.message || 'Video analysis failed.');
        } else if (msg.status) {
          setProcessingStatus(msg.status);
          setProgress(msg.progress ?? 0);
          setStatusMessage(msg.message || '');
        }
      };

      socket.onclose = () => {
        if (closedRef.current || terminalRef.current || socketRef.current !== socket) return;
        if (attemptsRef.current >= MAX_RECONNECTS) {
          fail('Lost connection to the server.');
          return;
        }
        const delay = Math.min(1000 * 2 ** attemptsRef.current, MAX_BACKOFF_MS);
        attemptsRef.current += 1;
        reconnectTimerRef.current = setTimeout(() => {
          if (!closedRef.current && !terminalRef.current) open();
        }, delay);
      };
    };
    open();
  }, [fail, fetchResult]);

  useEffect(() => {
    return () => {
      teardownSocket();
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = null;
      }
    };
  }, [teardownSocket]);

  const handleVideoUpload = async (event) => {
    const input = event.target;
    const file = input.files[0];
    if (!file) return;

    teardownSocket();
    jobIdRef.current = null;
    terminalRef.current = false;
    attemptsRef.current = 0;
    setCommentaryQuips([]);
    setErrorMessage('');
    setStatusMessage('');
    setProgress(0);
    setProcessingStatus('uploading');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const { data } = await axios.post(`${API_BASE}/api/upload`, formData);
      const jobId = data.job_id;
      jobIdRef.current = jobId;

      const url = URL.createObjectURL(file);
      if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = url;
      setVideoUrl(url);

      closedRef.current = false;
      connectSocket(jobId);
    } catch (error) {
      console.error('Error uploading video:', error);
      fail(errorDetail(error, 'Failed to upload video.'));
    } finally {
      input.value = '';
    }
  };

  const inFlight = processingStatus !== 'idle' && processingStatus !== 'completed' && processingStatus !== 'error';

  return (
    <div className="App">
      <header className="App-header">
        <h1>LionHype</h1>
        <input type="file" accept="video/*" onChange={handleVideoUpload} disabled={inFlight} />

        {processingStatus !== 'idle' && (
          <div style={{ margin: '1rem 0', maxWidth: '360px' }}>
            <div style={{ marginBottom: '0.5rem' }}>
              <strong>{PHASE_LABELS[processingStatus] || processingStatus}</strong>
              {statusMessage && <span> – {statusMessage}</span>}
            </div>
            <div
              role="progressbar"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={progress}
              style={{ background: '#eee', borderRadius: '4px', overflow: 'hidden' }}
            >
              <div
                style={{
                  width: `${progress}%`,
                  background: processingStatus === 'error' ? '#d32f2f' : '#4caf50',
                  height: '8px',
                  transition: 'width 0.3s',
                }}
              />
            </div>
            <small>{progress}%</small>
          </div>
        )}

        {errorMessage && (
          <div role="alert" style={{ margin: '1rem 0', padding: '0.5rem 1rem', background: '#fdecea', border: '1px solid #f5c2c0', borderRadius: '4px', color: '#8a1c17' }}>
            {errorMessage}
          </div>
        )}

        {videoUrl && (
          <div>
            <VideoPlayer
              key={videoUrl}
              videoUrl={videoUrl}
              commentaryQuips={commentaryQuips}
              processingStatus={processingStatus}
            />
          </div>
        )}
      </header>
      <ToastContainer />
    </div>
  );
}

export default App;
