import React, { useState, useEffect } from 'react';
import axios from 'axios';
import VideoPlayer from './components/VideoPlayer';

function App() {
  const [count, setCount] = useState(0);
  const [commentaryQuips, setCommentaryQuips] = useState([]);
  const [videoUrl, setVideoUrl] = useState(null);
  const [videoId, setVideoId] = useState(null);

  useEffect(() => {
    const fetchCommentary = async () => {
      try {
        const response = await axios.get('http://127.0.0.1:8000/api/commentary/mock');
        setCommentaryQuips(response.data.quips);
      } catch (error) {
        console.error('Error fetching commentary:', error);
      }
    };

    fetchCommentary();
  }, []);

  const handleVideoUpload = async (event) => {
    const file = event.target.files[0];
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://127.0.0.1:8000/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setVideoId(response.data.video_id);
      setVideoUrl(URL.createObjectURL(file));
    } catch (error) {
      console.error('Error uploading video:', error);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Video Commentary App</h1>
        <input type="file" accept="video/*" onChange={handleVideoUpload} />
        {videoUrl && (
          <div>
            <VideoPlayer videoUrl={videoUrl} commentaryQuips={commentaryQuips} />
          </div>
        )}
        <div className="commentary-sidebar">
          <h2>Commentary</h2>
          <ul>
            {commentaryQuips.map((quip, index) => (
              <li key={index}>
                <strong>{quip.timestamp}s:</strong> {quip.text}
              </li>
            ))}
          </ul>
        </div>
      </header>
    </div>
  );
}

export default App;
