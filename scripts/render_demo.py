"""Mux actual browser recording with scheduled, explicitly synthetic narration."""

import json
import subprocess
import wave
from pathlib import Path

import imageio_ffmpeg

directory = Path(__file__).resolve().parents[1] / "artifacts/demo"
segments = json.loads((directory / "narration.json").read_text(encoding="utf-8-sig"))
command = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-i", str(directory / "demo-raw.webm")]
filters = []
for i, segment in enumerate(segments):
    audio = directory / segment["file"]
    with wave.open(str(audio)) as reader:
        seconds = reader.getnframes() / reader.getframerate()
    limit = segments[i + 1]["start"] if i + 1 < len(segments) else 165
    if segment["start"] + seconds > limit:
        raise ValueError(f"Narration segment {i} overlaps the next shot")
    command += ["-i", str(audio)]
    filters.append(f"[{i + 1}:a]adelay={segment['start'] * 1000}:all=1[a{i}]")
filters.append(
    "".join(f"[a{i}]" for i in range(len(segments)))
    + f"amix=inputs={len(segments)}:normalize=0,apad=whole_dur=165[audio]"
)
command += [
    "-filter_complex",
    ";".join(filters),
    "-map",
    "0:v",
    "-map",
    "[audio]",
    "-c:v",
    "libx264",
    "-preset",
    "fast",
    "-crf",
    "22",
    "-pix_fmt",
    "yuv420p",
    "-c:a",
    "aac",
    "-b:a",
    "160k",
    "-t",
    "165",
    "-movflags",
    "+faststart",
    str(directory / "biocompiler-demo.mp4"),
]
subprocess.run(command, check=True, capture_output=True)
frames = imageio_ffmpeg.read_frames(str(directory / "biocompiler-demo.mp4"))
try:
    metadata = next(frames)
finally:
    frames.close()
if not 160 <= metadata["duration"] < 180:
    raise ValueError("Demo duration is outside the expected range")
(directory / "media-validation.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
print(f"Demo: {metadata['duration']} seconds, {metadata['size']}, synthesized narration included")
