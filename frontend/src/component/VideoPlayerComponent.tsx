
import React, { useRef, useState, useEffect } from 'react';
import ReactPlayer from 'react-player';



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

interface SubtitleEntry {
  speaker: string;
  start: number;
  end: number;
  text: string;
  clip_start_time: number;
  clip_end_time: number;
}


type VideoPlayerComponentProps = {
  videoName: string;
  url: string;
  audioControlUrl: string;
  streamingData: StreamingData | null;
  sessionId: string | null;
};

function VideoPlayerComponent({ videoName, url, audioControlUrl, streamingData, sessionId }: VideoPlayerComponentProps) {
  const playerRef = useRef<ReactPlayer | null>(null);
  const [playing, setPlaying] = useState(false);
  const [awaitingPlayCommand, setAwaitingPlayCommand] = useState(false)
  const [playheadTime, setPlayheadTime] = useState<number>(0);
  const [sliderValue, setSliderValue] = useState<number>(0);
  const [duration, setDuration] = useState<number>(0);
  const [isSeeking, setIsSeeking] = useState(false); // Flag to check if the user is seeking
  const [subtitlesReady, setSubtitlesReady] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);


  const [streamingDataArray, setStreamingDataArray] = useState<SubtitleEntry[]>([]);


  const sendPlayCommand = async (time: number) => {
    try {
      console.log('sendPlayCommand', time);
      await fetch(audioControlUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ action: 'play', time, videoName }),
      });
      console.log('Play command sent successfully');
    } catch (error) {
      console.error('Error sending play command:', error);
    }
  };
  
  const sendStopCommand = async (time: number) => {
    try {
      console.log('sendStopCommand', time);
      await fetch(audioControlUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ action: 'stop', time, videoName }),
      });
      console.log('Stop command sent successfully');
    } catch (error) {
      console.error('Error sending stop command:', error);
    }
  };
  

  // Check if there's at least one subtitle near the current playhead time
  useEffect(() => {
    let subtitlesInProximity: SubtitleEntry[] = [];
    const proximityThreshold = .5;

    if (streamingDataArray.length > 0) {
      console.log('StreamingDataArray:', streamingDataArray);
      subtitlesInProximity = streamingDataArray.filter(
        (entry) =>
          entry.clip_start_time <= playheadTime + proximityThreshold &&
          entry.clip_end_time >= playheadTime - proximityThreshold
      );
    }

    if (subtitlesInProximity.length > 0) {
      console.log('Subtitles in proximity: ', subtitlesInProximity);
      setSubtitlesReady(true);

      if ((!isProcessing && videoName.length > 0) && !isSeeking) {
        console.log('searching for closest segment end time');
        let closestClipEndTime = subtitlesInProximity[0].clip_end_time;
        for (let i = 1; i < streamingDataArray.length; i++) {
          // console.log('streamingDataArray start', streamingDataArray[i].clip_start_time, 'streamingDataArray end', streamingDataArray[i].clip_end_time, 'closestClipEndTime','closestClipEndTime', closestClipEndTime);
          if (streamingDataArray[i].clip_start_time <= closestClipEndTime + proximityThreshold && streamingDataArray[i].clip_end_time >= closestClipEndTime - proximityThreshold) {
            // console.log('streamingDataArray', streamingDataArray[i].clip_start_time);
            closestClipEndTime = streamingDataArray[i].clip_end_time;
          }
        }
        if (closestClipEndTime > subtitlesInProximity[0].clip_end_time) {
          console.log('found closest segment end time', closestClipEndTime);
          setIsProcessing(true);
          sendPlayCommand(closestClipEndTime);
        }
      }
    } 
    else {
      setSubtitlesReady(false);
      if (!isProcessing && videoName.length > 0) {
        setIsProcessing(true);
        sendPlayCommand(playheadTime);
        console.log('start processing: ', playheadTime);
      } else {
        console.log('processing...');
      }
    }
    
    console.log('playheadTime', playheadTime,'playing', playing, 'awaitingPlayCommand', awaitingPlayCommand, 'subtitlesReady', subtitlesReady);
  }, [playheadTime, streamingDataArray, isProcessing, videoName]);

  useEffect(() => {
    if (streamingData) {
      const overlapThreshold = 0.5; // Set an overlap threshold in seconds

      // Looping through diarize_bank to build new objects
      streamingData.diarize_bank.forEach((entry) => {
        const newEntry: SubtitleEntry = {
          speaker: entry.speaker,
          start: streamingData.clip_start_time + entry.start,
          end: streamingData.clip_start_time + entry.end,
          text: entry.text,
          clip_start_time: streamingData.clip_start_time,
          clip_end_time: streamingData.clip_end_time,
        };

        // Check if this entry already exists in the array
        const isAlreadyInArray = streamingDataArray.some(
          (existingEntry) =>
            Math.abs(existingEntry.clip_start_time - newEntry.clip_start_time) <= overlapThreshold &&
            Math.abs(existingEntry.clip_end_time - newEntry.clip_end_time) <= overlapThreshold &&
            existingEntry.speaker === newEntry.speaker &&
            existingEntry.start === newEntry.start &&
            existingEntry.end === newEntry.end
        );

        // If it's not already in the array, add it
        if (!isAlreadyInArray) {
          setStreamingDataArray((prevArray) => [...prevArray, newEntry]);
        }
      });
    }
  }, [streamingData]);
  
  
  useEffect(() => {
    if (!playing) {
      if (awaitingPlayCommand && subtitlesReady) {
        setPlaying(true);
      }
    } else if (playing) {
      if (!awaitingPlayCommand || !subtitlesReady) {
        setPlaying(false);
      }
    }
    // console.log('playheadTime', playheadTime,'playing', playing, 'awaitingPlayCommand', awaitingPlayCommand, 'subtitlesReady', subtitlesReady);
  }, [awaitingPlayCommand, playheadTime, subtitlesReady, playing]);



  const handlePlay = () => {
    setAwaitingPlayCommand(true);
  };

  const handlePause = () => {
    setAwaitingPlayCommand(false);
  };

  const handleProgress = (playedSeconds: number, loadedSeconds: number) => {
    if (!isSeeking) {
      // console.log('playedSeconds: ', playedSeconds, 'loadedSeconds: ', loadedSeconds, "subtitlesReady: ", subtitlesReady);
      setPlayheadTime(playedSeconds);
      setSliderValue(playedSeconds);
    }
  };

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = parseFloat(e.target.value);
    setSliderValue(newValue); // Update sliderValue while dragging
  };

  const handleSliderMouseDown = () => {
    setIsSeeking(true); // User is actively seeking
    setIsProcessing(false);
    sendStopCommand(playheadTime);
  };

  const handleSliderMouseUp = () => {
    if (playerRef.current) {
      playerRef.current.seekTo(sliderValue, 'seconds'); // Seek to the new value
      setIsSeeking(false); // User has finished seeking
    }
  };

  return (
    <div>
      <div className="video-player">
        <ReactPlayer
          ref={playerRef}
          url={url}
          playing={playing}
          onDuration={(duration) => setDuration(duration)}
          onProgress={({ playedSeconds, loadedSeconds }) => handleProgress(playedSeconds, loadedSeconds)}
          width="100%"
          height="100%"
          config={{
            file: {
              attributes: {
                controlsList: 'nodownload noplaybackrate',
                disablePictureInPicture: true,
              },
            },
          }}
        />

        {/* Overlay spinner when subtitles are not ready */}
        {!subtitlesReady && (
          <div className="spinner-overlay">
            <div className="spinner"></div>
          </div>
        )}
      </div>

      <div style={{ marginTop: '10px' }}>
        <button onClick={handlePlay}>Play</button>
        <button onClick={handlePause}>Pause</button>
        <div style={{ marginTop: '10px', width: '100%' }}>
          <input
            type="range"
            min={0}
            max={duration}
            step="0.1"
            value={sliderValue}
            onChange={handleSliderChange}
            onMouseDown={handleSliderMouseDown}
            onMouseUp={handleSliderMouseUp}
            style={{ width: '100%' }}
          />
        </div>
      </div>
    </div>
  );
}

export default VideoPlayerComponent;