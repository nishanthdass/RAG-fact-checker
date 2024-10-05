import React, { useEffect, useState } from 'react';

interface Video {
  url: string;
  name: string;
}

interface VideoPlaylistComponentProps {
  url: string;
  video: Video | null;
  setVideo: (video: Video) => void; // Accept setVideo as a prop
}

function VideoPlaylistComponent({ url, video,  setVideo }: VideoPlaylistComponentProps) {
  const [playlist, setPlaylist] = useState<Video[]>([]);

  useEffect(() => {
    // Fetch videos from the server link
    const fetchVideos = async () => {
      try {
        // Ensure that credentials (cookies) are sent with the request
        const response = await fetch(url, {
          method: 'GET',
          credentials: 'include', // This ensures cookies (session ID) are sent with the request
        });
        const data = await response.json(); // Assuming the server returns JSON data
        setPlaylist(data); // Set the fetched videos to the playlist
      } catch (error) {
        console.error('Error fetching videos:', error);
      }
    };

    fetchVideos();
  }, [url]);

  useEffect(() => {
    if (!video && playlist.length > 0) {
      setVideo(playlist[0]);
    }
  }, [playlist, video, setVideo]);

  const handleRowClick = (selectedVideo: Video) => {
    setVideo(selectedVideo);
  };

  return (
    <div className="video-playlist-window">
      {playlist.map((videoItem, index) => (
        <div
          key={index}
          className="video-playlist-row"
          onClick={() => handleRowClick(videoItem)}
        >
          <p>{videoItem.name}</p>
        </div>
      ))}
    </div>
  );
}

export default VideoPlaylistComponent;
