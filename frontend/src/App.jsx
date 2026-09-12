import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import VideoPlayer from './components/VideoPlayer';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

function App() {
  const [commentaryQuips, setCommentaryQuips] = useState([]);
  const [videoUrl, setVideoUrl] = useState(null);
  const [processingStatus, setProcessingStatus] = useState('idle');
  const [progress, setProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');
  const [pipelineStage, setPipelineStage] = useState('');
  const socketRef = useRef(null);

  useEffect(() => {
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, []);

  const connectSocket = () => {
    if (socketRef.current) {
      socketRef.current.close();
    }

    const socket = new WebSocket('ws://localhost:8000/ws/analyze');
    socketRef.current = socket;

    socket.onopen = () => {
      setProcessingStatus('connected');
      setErrorMessage('');
    };

    socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      const status = msg.status;
      const progressVal = msg.progress ?? 0;

      if (['uploading', 'extracting', 'analyzing', 'synthesizing'].includes(status)) {
        setProcessingStatus(status);
        setProgress(progressVal);
        setPipelineStage(status);
        return;
      }

      if (status === 'completed') {
        setProcessingStatus('completed');
        setProgress(100);
        setCommentaryQuips(Array.isArray(msg.quips) ? msg.quips : []);
        setPipelineStage('completed');
        return;
      }

      if (status === 'error') {
        setProcessingStatus('error');
        setProgress(100);
        setErrorMessage(msg.message || 'Video analysis failed.');
        setPipelineStage('error');
        toast.error(msg.message || 'Video analysis failed.', {
          position: "top-right",
        });
      }
    };

    socket.onerror = () => {
      setProcessingStatus('error');
      setErrorMessage('Unable to connect to the analysis WebSocket.');
      setPipelineStage('error');
      toast.error('Unable to connect to the analysis WebSocket.', {
        position: "top-right",
      });
    };

    socket.onclose = () => {
      if (processingStatus !== 'completed' && processingStatus !== 'error') {
        setProcessingStatus('idle');
        setPipelineStage('');
        // Auto-reconnect after a short delay if not manually closed
        setTimeout(() => {
          if (socketRef.current?.readyState !== WebSocket.OPEN) {
            connectSocket();
          }
        }, 2000);
      }
    };
  };

  const handleVideoUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://127.0.0.1:8000/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.status !== 200) {
        throw new Error(response.statusText || 'Upload failed');
      }

      const { video_path, video_id } = response.data;
      setProcessingStatus('uploading');
      setCommentaryQuips([]);
      setErrorMessage('');
      setVideoUrl(URL.createObjectURL(file));
      connectSocket();

      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({ video_path }));
      } else {
        socketRef.current.addEventListener('open', () => {
          socketRef.current.send(JSON.stringify({ video_path }));
        }, { once: true });
      }

      if (video_id) {
        console.log('Video uploaded:', video_id);
      }
    } catch (error) {
      console.error('Error uploading video:', error);
      setProcessingStatus('error');
      setErrorMessage(error.response?.data?.detail || 'Failed to upload video.');
      toast.error(error.response?.data?.detail || 'Failed to upload video.', {
        position: "top-right",
      });
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Video Commentary App</h1>
        <input type="file" accept="video/*" onChange={handleVideoUpload} />

        {processingStatus !== 'idle' && (
          <div style={{ margin: '1rem 0' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <div style={{
                width: '16px', height: '16px',
                border: '2px solid #f3f3f3', borderTop: '2px solid #4caf50',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }} />
              <strong>Status:</strong> {processingStatus}
            </div>
            <div style={{ width: '100%', maxWidth: '360px', background: '#eee', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ width: `${progress}%`, background: '#4caf50', height: '8px' }} />
            </div>
            {progress > 0 && <small>{progress}%</small>}
            <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
          </div>
        )}

        {pipelineStage && (
          <div style={{ margin: '1rem 0', padding: '0.5rem 1rem', background: '#f0f9ff', borderRadius: '4px', border: '1px solid #bae6fd', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>📊</span>
            <strong>Phase:</strong> {pipelineStage.charAt(0).toUpperCase() + pipelineStage.slice(1)}
          </div>
        )}


        {videoUrl && (
          <div>
            <VideoPlayer videoUrl={videoUrl} commentaryQuips={commentaryQuips} processingStatus={processingStatus} />
          </div>
        )}
      </header>
      <ToastContainer />
    </div>
  );
}

export default App;
