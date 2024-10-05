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

  useEffect(() => {
    
      const socket = new WebSocket("ws://localhost:8000/ws");

      socket.onopen = function(event) {
          console.log("WebSocket connection established.");
      };

      socket.onmessage = function(event) {
          // Extract the session ID from the message
          if (event.data.startsWith("session_id:")) {
              const sessionId = event.data.split(":")[1];

              // Set the session ID as a cookie (expires in 1 day)
              document.cookie = `session_id=${sessionId}; path=/; max-age=86400`; // 86400 seconds = 1 day
              console.log("Session ID received and stored in cookie:", sessionId);
          }
      };

      socket.onclose = function(event) {
          console.log("WebSocket connection closed.");
          // You can also handle session cleanup if needed
      };

      return () => {
          socket.close();  // Cleanup WebSocket when the component unmounts
      };
  }, []);


  
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
