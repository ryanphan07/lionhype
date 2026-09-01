import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import VideoPlayer from './components/VideoPlayer';

function App() {
  const [commentaryQuips, setCommentaryQuips] = useState([]);
  const [videoUrl, setVideoUrl] = useState(null);
  const [processingStatus, setProcessingStatus] = useState('idle');
  const [progress, setProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');
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

      if (msg.status === 'processing') {
        setProcessingStatus(msg.message);
        setProgress(msg.progress || 0);
        return;
      }

      if (msg.status === 'completed') {
        setProcessingStatus('completed');
        setProgress(100);
        setCommentaryQuips(Array.isArray(msg.quips) ? msg.quips : []);
        return;
      }

      if (msg.status === 'error') {
        setProcessingStatus('error');
        setProgress(100);
        setErrorMessage(msg.message || 'Video analysis failed.');
      }
    };

    socket.onerror = () => {
      setProcessingStatus('error');
      setErrorMessage('Unable to connect to the analysis WebSocket.');
    };

    socket.onclose = () => {
      if (processingStatus !== 'completed' && processingStatus !== 'error') {
        setProcessingStatus('idle');
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
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Video Commentary App</h1>
        <input type="file" accept="video/*" onChange={handleVideoUpload} />

        {processingStatus !== 'idle' && (
          <div style={{ margin: '1rem 0' }}>
            <strong>Status:</strong> {processingStatus}
            <div style={{ width: '100%', maxWidth: '360px', background: '#eee', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ width: `${progress}%`, background: '#4caf50', height: '8px' }} />
            </div>
            {progress > 0 && <small>{progress}%</small>}
          </div>
        )}

        {errorMessage && (
          <div role="alert" style={{ background: '#fff1f0', color: '#a61d24', padding: '0.75rem', borderRadius: '6px', marginBottom: '1rem' }}>
            {errorMessage}
          </div>
        )}

        {videoUrl && (
          <div>
            <VideoPlayer videoUrl={videoUrl} commentaryQuips={commentaryQuips} processingStatus={processingStatus} />
          </div>
        )}
      </header>
    </div>
  );
}

export default App;
