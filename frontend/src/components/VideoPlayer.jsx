import React, { useEffect, useRef, useState } from 'react';

const VideoPlayer = ({ videoUrl, commentaryQuips, processingStatus }) => {
  const videoRef = useRef(null);
  const [currentQuipIndex, setCurrentQuipIndex] = useState(0);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !commentaryQuips.length) return;

    const handleTimeUpdate = () => {
      const currentTime = video.currentTime;
      const nextQuip = commentaryQuips[currentQuipIndex + 1];

      if (nextQuip && currentTime >= nextQuip.timestamp) {
        setCurrentQuipIndex(currentQuipIndex + 1);
        if (nextQuip.audio_url) {
          const audio = new Audio(nextQuip.audio_url);
          audio.play().catch(() => {});
        }
      }
    };

    video.addEventListener('timeupdate', handleTimeUpdate);
    return () => video.removeEventListener('timeupdate', handleTimeUpdate);
  }, [commentaryQuips, currentQuipIndex]);

  const isCompleted = processingStatus === 'completed';

  return (
    <div>
      <video ref={videoRef} src={videoUrl} controls style={{ maxWidth: '100%' }} />

      {isCompleted && (
        <div className="commentary-display" style={{ marginTop: '1rem' }}>
          <h3>Final quips</h3>
          {commentaryQuips.map((quip, index) => (
            <div
              key={index}
              className={index === currentQuipIndex ? 'highlight' : ''}
              style={{ marginBottom: '0.5rem', padding: '0.5rem', borderRadius: '6px', background: index === currentQuipIndex ? '#fff3cd' : '#f5f5f5' }}
            >
              <strong>{quip.timestamp}s:</strong> {quip.text}
              {quip.audio_url && (
                <div>
                  <audio controls src={quip.audio_url} style={{ width: '100%', marginTop: '0.5rem' }} />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default VideoPlayer;
