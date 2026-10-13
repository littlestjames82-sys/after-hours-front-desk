#!/usr/bin/env python3
"""Assemble demo-evidence/demo-video.mp4 from the capture manifest.

Input:  demo-evidence/video-capture/manifest.json (written by
        scripts/capture_demo.py) - real simulator frames plus the
        exact WAV bytes the desk produced for each reply.
Output: demo-evidence/demo-video.mp4 (captions burned in) and
        demo-evidence/demo-video.srt (the same captions, sidecar).

Each frame is held for exactly as long as its reply's audio plays
(plus a short beat), so what you see on screen is the state of the
call at the moment you hear that line. Title and summary-card frames
hold in silence. No caller is voiced: in the simulator the caller
side is typed, and the video does not pretend otherwise.
"""

import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAP = os.path.join(ROOT, "demo-evidence", "video-capture")
EV = os.path.join(ROOT, "demo-evidence")
W, H = 1000, 1250
PAUSE = 0.6
HOLDS = {"title": 5.0, "card": 7.0}


def run(cmd):
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def ass_time(s):
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f"{h}:{m:02d}:{sec:05.2f}"


def srt_time(s):
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:06.3f}".replace(".", ",")


def wrap(text, width=46):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines


def main():
    with open(os.path.join(CAP, "manifest.json")) as f:
        segments = json.load(f)["segments"]
    work = os.path.join(CAP, "build")
    os.makedirs(work, exist_ok=True)

    timeline = []  # (start, dur, caption)
    parts = []
    t = 0.0
    for i, seg in enumerate(segments):
        frame = os.path.join(CAP, seg["frame"])
        if seg["kind"] in ("greeting", "reply"):
            dur = seg["audio_seconds"] + PAUSE
            audio_in = os.path.join(CAP, seg["audio"])
            caption = seg.get("page_line", "")
            if ":" in caption:  # strip the "Shop name:" prefix
                caption = caption.split(":", 1)[1].strip()
        else:
            dur = HOLDS[seg["kind"]]
            audio_in = None
            caption = seg.get("caption", "")
        part = os.path.join(work, f"part{i:02d}.mp4")
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
              f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0xf6f3ec,"
              "format=yuv420p")
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", frame]
        if audio_in:
            cmd += ["-i", audio_in]
        else:
            cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono"]
        cmd += ["-t", f"{dur:.2f}", "-vf", vf, "-r", "30",
                "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                "-c:a", "aac", "-b:a", "128k", "-ar", "48000", part]
        run(cmd)
        parts.append(part)
        timeline.append((t, dur, caption))
        t += dur

    listfile = os.path.join(work, "concat.txt")
    with open(listfile, "w") as f:
        for p in parts:
            f.write(f"file '{p}'\n")
    joined = os.path.join(work, "joined.mp4")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile,
         "-c", "copy", joined])

    # Captions: ASS for the burn-in, SRT as the sidecar.
    ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}",
           f"PlayResY: {H}", "",
           "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, "
           "SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
           "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
           "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, "
           "MarginV, Encoding",
           "Style: Default,DejaVu Sans,30,&H00FFFFFF,&H000000FF,"
           "&H00000000,&H96000000,0,0,0,0,100,100,0,0,3,1,0,2,40,40,44,1",
           "", "[Events]",
           "Format: Layer, Start, End, Style, Name, MarginL, MarginR, "
           "MarginV, Effect, Text"]
    srt = []
    for n, (start, dur, caption) in enumerate(timeline, 1):
        if not caption:
            continue
        body = "\\N".join(wrap(caption))
        ass.append(f"Dialogue: 0,{ass_time(start)},"
                   f"{ass_time(start + dur)},Default,,0,0,0,,{body}")
        srt.append(f"{n}\n{srt_time(start)} --> "
                   f"{srt_time(start + dur)}\n{caption}\n")
    ass_path = os.path.join(work, "captions.ass")
    with open(ass_path, "w") as f:
        f.write("\n".join(ass) + "\n")
    with open(os.path.join(EV, "demo-video.srt"), "w") as f:
        f.write("\n".join(srt))

    out = os.path.join(EV, "demo-video.mp4")
    run(["ffmpeg", "-y", "-i", joined, "-vf", f"ass={ass_path}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-c:a", "copy", out])

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration,size:stream=codec_type,codec_name,width,height",
         "-of", "json", out], capture_output=True, text=True, check=True)
    info = json.loads(probe.stdout)
    print(json.dumps(info, indent=2))
    print(f"total timeline: {t:.1f}s across {len(segments)} segments")
    return 0


if __name__ == "__main__":
    sys.exit(main())
