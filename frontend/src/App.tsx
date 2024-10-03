// App.js
import React, { useState, useEffect } from 'react';
import './App.css';
import VideoPlayerComponent from './component/VideoPlayerComponent';
import VideoPlaylistComponent from './component/VideoPlaylistComponent';

interface Video {
  url: string;
  name: string;
}
function App() {
  const [video, setVideo] = useState<Video | null>(null);

  
  return (
    <div className="App">
      <div className="grid-container">
        <div className="video-playlist-section">
          <VideoPlaylistComponent url="http://localhost:8000/videos" video={video} setVideo={setVideo}/>
        </div>
        <div className="video-player-section">
          <div className="video-player-box">
            <VideoPlayerComponent videoName={video? video.name : ""} url = {video? video.url : ""} audioControlUrl="http://localhost:8000/audio-control" />
          </div>
          <div className="speech-to-text-box">
            Speech to Text
          </div>
        </div>
        <div className="llm-section">
          <div className="prompt-generation-box">
            Prompt generations
          </div>
          <div className="response-box">
            LLM response generations
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
