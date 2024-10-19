import time
from fastapi.responses import StreamingResponse
from app.session_manager_init import session_manager


def handle_range_request(video_path: str, file_size: int, range_header: str, session_id: str) -> StreamingResponse:
    # Parse the Range header
    range_val = range_header.strip().split("=")[-1]
    range_start, range_end = range_val.split("-")
    range_start = int(range_start) if range_start else 0
    range_end = int(range_end) if range_end else file_size - 1
    content_length = range_end - range_start + 1


    headers = {
        "Content-Range": f"bytes {range_start}-{range_end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Type": "video/mp4",
    }
    
    # Define an iterator to stream the requested byte range
    def iter_file():
        # print("audio player handle_range_request: ", audio_player.is_playing())
        with open(video_path, 'rb') as video_file:
            video_file.seek(range_start)
            yield video_file.read(content_length)

    # Return the streaming response with partial content status code
    return StreamingResponse(iter_file(), status_code=206, headers=headers)


def handle_full_request(video_path: str, file_size: int, session_id: str) -> StreamingResponse:
    # Set the response headers
    headers = {
        "Content-Length": str(file_size),
        "Content-Type": "video/mp4",
        "Accept-Ranges": "bytes",
    }

    print("handle_full_request: ", session_id)

    def iter_file():
        # print("audio player handle_full_request: ", audio_player.is_playing())
        with open(video_path, 'rb') as video_file:
            yield from video_file

    # Return the streaming response
    return StreamingResponse(iter_file(), headers=headers)
