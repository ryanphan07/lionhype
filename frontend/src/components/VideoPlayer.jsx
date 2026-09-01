import React, { useState, useRef, useEffect } from 'react';

const VideoPlayer = ({ videoUrl, commentaryQuips }) => {
  const videoRef = useRef(null);
  const [currentQuipIndex, setCurrentQuipIndex] = useState(0);

  useEffect(() => {
    const video = videoRef.current;

    const handleTimeUpdate = () => {
      const currentTime = video.currentTime;
      const nextQuip = commentaryQuips[currentQuipIndex + 1];

      if (nextQuip && currentTime >= nextQuip.timestamp) {
        setCurrentQuipIndex(currentQuipIndex + 1);
        const audio = new Audio(nextQuip.audio_url);
        audio.play();
      }
    };

    video.addEventListener('timeupdate', handleTimeUpdate);

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
    };
  }, [commentaryQuips, currentQuipIndex]);

  return (
    <div>
      <video ref={videoRef} src={videoUrl} controls />
      <div className="commentary-display">
        {commentaryQuips.map((quip, index) => (
          <div
            key={index}
            className={index === currentQuipIndex ? 'highlight' : ''}
          >
            <strong>{quip.timestamp}s:</strong> {quip.text}
          </div>
        ))}
      </div>
    </div>
  );
};

export default VideoPlayer;
