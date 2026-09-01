import React, { useState, useEffect } from 'react';
import { GiVideo, MessageSquare } from 'lucide-react';
import axios from 'axios';

function App() {
  const [count, setCount] = useState(0);
  const [commentaryQuips, setCommentaryQuips] = useState([]);

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

  return (
    <>
      <section id="center">
        <div className="hero">
          <img src={heroImg} className="base" width="170" height="179" alt="" />
          <img src={reactLogo} className="framework" alt="React logo" />
          <img src={viteLogo} className="vite" alt="Vite logo" />
        </div>
        <div className="dashboard">
          <div className="video-upload-card">
            <GiVideo size={48} />
            <h3>Upload Video</h3>
            <input type="file" />
          </div>
          <div className="commentary-timeline">
            <h3>Commentary Timeline</h3>
            <ul>
              {commentaryQuips.map((quip, index) => (
                <li key={index}>
                  <MessageSquare size={24} />
                  {quip.text}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>
    </>
  );
}

export default App;
