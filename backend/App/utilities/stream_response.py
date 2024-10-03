from fastapi.responses import StreamingResponse

def handle_range_request(video_path: str, file_size: int, range_header: str) -> StreamingResponse:
    # Parse the Range header
    range_val = range_header.strip().split("=")[-1]
    range_start, range_end = range_val.split("-")
    range_start = int(range_start) if range_start else 0
    range_end = int(range_end) if range_end else file_size - 1
    content_length = range_end - range_start + 1

    # Set the response headers
    headers = {
        "Content-Range": f"bytes {range_start}-{range_end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Type": "video/mp4",
    }

    # Define an iterator to stream the requested byte range
    def iter_file():
        with open(video_path, 'rb') as video_file:
            video_file.seek(range_start)
            yield video_file.read(content_length)

    # Return the streaming response with partial content status code
    return StreamingResponse(iter_file(), status_code=206, headers=headers)

def handle_full_request(video_path: str, file_size: int) -> StreamingResponse:
    # Set the response headers
    headers = {
        "Content-Length": str(file_size),
        "Content-Type": "video/mp4",
        "Accept-Ranges": "bytes",
    }

    # Define an iterator to stream the entire file
    def iter_file():
        with open(video_path, 'rb') as video_file:
            yield from video_file

    # Return the streaming response
    return StreamingResponse(iter_file(), headers=headers)