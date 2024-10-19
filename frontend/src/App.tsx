import React, { useState, useEffect } from 'react';
import './App.css';
import VideoPlayerComponent from './component/VideoPlayerComponent';
import VideoPlaylistComponent from './component/VideoPlaylistComponent';

interface Video {
  url: string;
  name: string;
}

interface StreamingData {
  clip_start_time: number;
  clip_end_time: number;
  diarize_bank: Array<{
    speaker: string;
    start: number;
    end: number;
    text: string;
  }>;
}

function App() {
  const [video, setVideo] = useState<Video | null>(null);
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [streamingData, setStreamingData] = useState<StreamingData | null>(null);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws");

    ws.onopen = function (event) {
      // console.log("WebSocket connection established.");
      setSocket(ws);
    };

    ws.onmessage = function (event) {
      if (event.data.startsWith("session_id:")) {
        const receivedSessionId = event.data.split(":")[1];
        document.cookie = `session_id=${receivedSessionId}; path=/; max-age=86400`;
        // console.log("Session ID received and stored in cookie:", receivedSessionId);
        setSessionId(receivedSessionId);
      } else {
        const parsedData = JSON.parse(event.data); // Parse the data as StreamingData
        setStreamingData(parsedData); // Save streaming data to state
      }
    };

    ws.onclose = function (event) {
      console.log("WebSocket connection closed.");
    };

    return () => {
      ws.close();
    };
  }, []);

  // Function to send data to the server
  const sendMessageToServer = (message: string) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(message); // Send the message to the WebSocket server
      // console.log("Sent message to server:", message);
    } else {
      console.log("WebSocket connection is not open.");
    }
  };

  // Send session ID to the server after it is set
  useEffect(() => {
    if (sessionId) {
      sendMessageToServer("session_id:" + sessionId); // Send session ID only after it's set in state
    }
  }, [sessionId, socket]); // Ensure socket is ready and session ID is set

  // Render only if the session ID is available
  if (!sessionId) {
    return (
      <div className="App">
        <div className="loading-section">
          <h2>Initializing session, please wait...</h2>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <div className="grid-container">
        <div className="video-playlist-section">
          <VideoPlaylistComponent
            url="http://localhost:8000/videos"
            video={video}
            setVideo={setVideo}
          />
        </div>
        <div className="video-player-section">
          <div className="video-player-box">
            <VideoPlayerComponent
              videoName={video ? video.name : ""}
              url={video ? video.url : ""}
              audioControlUrl="http://localhost:8000/audio-control"
              streamingData={streamingData}
              sessionId={sessionId}
            />
          </div>
        </div>
        <div className="llm-section">
          <div className="prompt-generation-box">Prompt generations</div>
          <div className="response-box">LLM response generations</div>
        </div>
      </div>
    </div>
  );
}

export default App;
