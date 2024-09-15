import React, { useRef, useState } from 'react';
import ReactPlayer from 'react-player';

type VideoPlayerComponentProps = {
  videoName: string;
  url: string;
  audioControlUrl: string; // Specifying the correct type
};

function VideoPlayerComponent({ videoName, url, audioControlUrl }: VideoPlayerComponentProps) {
  const playerRef = useRef<ReactPlayer | null>(null);
  const [playing, setPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);

  const handlePlay = () => {
    if (isPaused) {
      setIsPaused(false);
    }
    if (playerRef.current) {
      const currentTime = playerRef.current.getCurrentTime();
      setPlaying(true);
      sendControlToServer('play', currentTime, videoName);
    }
  };

  const handlePause = () => {
    if (playerRef.current) {
      console.log('handlePause');
      setPlaying(false);
      setIsPaused(true);
      const currentTime = playerRef.current.getCurrentTime();
      sendControlToServer('pause', currentTime, videoName);
    }
  };


  const sendControlToServer = (action: string, time: number, videoName: string) => {
    fetch(audioControlUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include', 
      body: JSON.stringify({ action, time, videoName }),
    }).catch(console.error);
  };

  return (
    <ReactPlayer
      ref={playerRef}
      url={url}
      controls={true}
      playing={playing}
      // onBufferEnd={handlePlay}
      onPlay={handlePlay}
      onPause={handlePause}
      // onSeek={(seekTime) => handleSeek(seekTime)}
      // onProgress={({ playedSeconds }) => setPlayhead(playedSeconds)}
      width="100%"
      height="100%"
      config={{
        file: {
          attributes: {
            controlsList: 'nodownload noplaybackrate',
            disablePictureInPicture: true,
          }
        },
      }}
    />
  );
}

export default VideoPlayerComponent;
