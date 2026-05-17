import ffmpeg
import os
import re
import uuid
import tempfile
import logging
import sys
import traceback
import subprocess
from dataclasses import dataclass
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

# --- Setup ---
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("video_captioner")

try:
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    if not os.getenv('OPENAI_API_KEY'):
        raise ValueError("OPENAI_API_KEY is not set in the environment.")
    logger.info("✅ OpenAI client initialized.")
except Exception as e:
    logger.error(f"❌ Failed to initialize OpenAI client: {e}")
    sys.exit(1)
# --- End Setup ---


def extract_audio(video_file: str) -> str:
    """Extracts audio from a video file and saves it as an MP3."""
    output_filename = f"temp_audio_{uuid.uuid4().hex}.mp3"
    logger.info(f"🎵 Extracting audio from {video_file}...")
    try:
        (
            ffmpeg
            .input(video_file)
            .output(output_filename, acodec='mp3', ab='192k', vn=None)
            .run(overwrite_output=True, quiet=True)
        )
        logger.info(f"✅ Audio extracted to {output_filename}")
        return output_filename
    except ffmpeg.Error as e:
        logger.error(f"❌ Failed to extract audio: {e.stderr.decode('utf8')}")
        raise

def get_video_dimensions(video_file: str) -> tuple[int, int]:
    """Gets the width and height of a video file."""
    logger.info(f"🔍 Probing video for dimensions: {video_file}")
    try:
        probe = ffmpeg.probe(video_file)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if video_stream:
            width = int(video_stream['width'])
            height = int(video_stream['height'])
            logger.info(f"✅ Video dimensions found: {width}x{height}")
            return width, height
        else:
            raise ValueError("No video stream found in the file.")
    except ffmpeg.Error as e:
        logger.error(f"❌ Failed to get video dimensions: {e.stderr.decode('utf8')}")
        raise

WHISPER_MAX_BYTES = 24 * 1024 * 1024  # 24 MB safety margin (Whisper limit is 25 MB)

def _split_audio_into_chunks(audio_file: str, chunk_duration_secs: int = 600) -> list[tuple[str, float]]:
    """Splits an audio file into chunks and returns (chunk_path, start_offset_secs) tuples."""
    probe = ffmpeg.probe(audio_file)
    total_duration = float(probe['format']['duration'])
    logger.info(f"🔪 Audio duration: {total_duration:.1f}s — splitting into {chunk_duration_secs}s chunks...")

    chunks = []
    start = 0.0
    chunk_idx = 0
    while start < total_duration:
        end = min(start + chunk_duration_secs, total_duration)
        chunk_path = f"temp_chunk_{uuid.uuid4().hex}.mp3"
        (
            ffmpeg
            .input(audio_file, ss=start, t=(end - start))
            .output(chunk_path, acodec='mp3', ab='128k', vn=None)
            .run(overwrite_output=True, quiet=True)
        )
        logger.info(f"   Chunk {chunk_idx}: {start:.1f}s → {end:.1f}s  →  {chunk_path}")
        chunks.append((chunk_path, start))
        start = end
        chunk_idx += 1

    return chunks

def get_word_timestamps_from_audio(audio_file: str):
    """Ask Whisper for word-level timestamps. Splits into chunks if file exceeds size limit."""
    file_size = os.path.getsize(audio_file)
    logger.info(f"📦 Audio file size: {file_size / 1024 / 1024:.2f} MB")

    if file_size <= WHISPER_MAX_BYTES:
        logger.info(f"🎙️ Transcribing audio file directly: {audio_file}")
        with open(audio_file, "rb") as f:
            resp = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="verbose_json",
                timestamp_granularities=["word"],
            )
        logger.info(f"✅ Transcription complete with {len(resp.words)} words.")
        return resp.words

    logger.info(f"⚠️ File too large for Whisper ({file_size / 1024 / 1024:.1f} MB > 24 MB). Splitting into chunks...")
    chunks = _split_audio_into_chunks(audio_file)
    all_words = []
    try:
        for chunk_path, offset in chunks:
            logger.info(f"🎙️ Transcribing chunk: {chunk_path} (offset={offset:.1f}s)")
            with open(chunk_path, "rb") as f:
                resp = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    response_format="verbose_json",
                    timestamp_granularities=["word"],
                )
            logger.info(f"   → {len(resp.words)} words transcribed from chunk at offset {offset:.1f}s")
            for w in resp.words:
                w.start += offset
                w.end += offset
            all_words.extend(resp.words)
    finally:
        for chunk_path, _ in chunks:
            if os.path.exists(chunk_path):
                os.remove(chunk_path)
                logger.info(f"🧹 Removed chunk: {chunk_path}")

    logger.info(f"✅ Full transcription complete: {len(all_words)} words total.")
    return all_words

def _seconds_to_ass(ts: float) -> str:
    """Converts seconds to ASS subtitle format time."""
    h, rem   = divmod(ts, 3600)
    m, rem   = divmod(rem, 60)
    s, cs    = divmod(rem, 1)
    return f"{int(h):01d}:{int(m):02d}:{int(s):02d}.{int(cs*100):02d}"

def create_ass_subtitle_file(words, width=1080, height=1920, position: str = "middle", font_size: int = 95) -> str:
    """Build an .ass file with fancy karaoke-style captions — current word in yellow,
    next two words in white, chunked so no more than 3 words show at a time."""
    fd, path = tempfile.mkstemp(suffix=".ass")
    os.close(fd)
    logger.info(f"✍️ Creating ASS subtitle file at {path}")

    # --- Position mapping ---
    position_styles = {
        "top":    {"alignment": 8, "margin_v": 80},
        "middle": {"alignment": 5, "margin_v": 150},
        "bottom": {"alignment": 2, "margin_v": 80}
    }
    style_settings = position_styles.get(position.lower(), position_styles["middle"])
    alignment = style_settings["alignment"]
    margin_v = style_settings["margin_v"]

    # Bold, slightly larger font with thick black outline + shadow for legibility on any background
    style_header = (
        "Format: Name, Fontname, Fontsize, PrimaryColour, "
        "SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
    )
    style_line = (
        f"Style: Default,Arial,{font_size},&H00FFFFFF,&H0000FFFF,&H00000000,&HAA000000,"
        f"-1,0,0,0,100,100,1,0,1,5,2,{alignment},20,20,{margin_v},1"
    )

    highlight_color = "&H0000FFFF"  # Bright yellow (BGR in ASS)
    default_color   = "&H00FFFFFF"  # White

    dialogues: list[str] = []
    num_words = len(words)

    for i, word_info in enumerate(words):
        start_time_val = max(0, word_info.start)
        end_time_val   = max(start_time_val + 0.1, word_info.end)

        # Enforce minimum display duration of 150ms
        if end_time_val - start_time_val < 0.15:
            new_end = start_time_val + 0.15
            if i + 1 < num_words:
                new_end = min(new_end, words[i + 1].start)
            end_time_val = new_end

        start_time = _seconds_to_ass(start_time_val)
        end_time   = _seconds_to_ass(end_time_val)

        # Build up to 3-word chunk: [CURRENT] [next] [next+1]
        parts = [f"{{\\c{highlight_color}}}{word_info.word.upper()}"]

        for lookahead in range(1, 3):  # Show up to 2 words ahead
            j = i + lookahead
            if j >= num_words:
                break
            gap = words[j].start - end_time_val
            if gap > 1.0:  # Big pause — don't preview across it
                break
            parts.append(f"{{\\c{default_color}}}{words[j].word.upper()}")

        text = " ".join(parts)
        dialogues.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}")

    dialogues_str = "\n".join(dialogues)

    ass_contents = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
{style_header}{style_line}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
{dialogues_str}
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(ass_contents.strip())
    
    logger.info(f"✅ Subtitle file generated with {len(dialogues)} lines.")
    return path


def add_captions_to_video(video_path: str, output_path: str, captions_position: str = "middle", font_size: int = 95):
    """
    Main function to add burned-in captions to a video file.
    """
    logger.info(f"🚀 Starting captioning process for video: {video_path}")
    temp_files = []

    try:
        # Step 1: Extract audio from the video
        audio_file = extract_audio(video_path)
        temp_files.append(audio_file)

        # Step 2: Get transcript with word timestamps from the audio
        words = get_word_timestamps_from_audio(audio_file)

        # Step 3: Get video dimensions to correctly size subtitles
        width, height = get_video_dimensions(video_path)

        # Step 4: Create the ASS subtitle file
        subtitle_file = create_ass_subtitle_file(words, width=width, height=height, position=captions_position, font_size=font_size)
        temp_files.append(subtitle_file)

        # Step 5: Burn subtitles into the video using ffmpeg
        logger.info(f"🔥 Burning subtitles into video. Output will be: {output_path}")

        esc_sub = _escape_filter_path(os.path.abspath(subtitle_file))
        vf = f"subtitles='{esc_sub}'"
        logger.info(f"   subtitle filter: {vf}")

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", vf,
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-c:a", "copy",
            "-pix_fmt", "yuv420p",
            output_path,
        ]
        logger.info(f"   ffmpeg cmd: {' '.join(cmd[:6])} ... {output_path}")
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            logger.error(f"ffmpeg stderr:\n{proc.stderr[-3000:]}")
            raise RuntimeError(f"ffmpeg failed with code {proc.returncode}")

        logger.info(f"✅ Successfully created captioned video: {output_path}")

    except Exception as e:
        logger.error(f"❌ An error occurred during the captioning process.")
        traceback.print_exc()
        raise
    finally:
        logger.info("🧹 Cleaning up temporary files...")
        for f in temp_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                    logger.info(f"   - Removed temp file: {f}")
                except OSError as e:
                    logger.warning(f"   - Could not remove temp file {f}: {e}")


# --- Vertical shorts (9:16 letterbox + title top + captions bottom) ---

VERTICAL_OUT_W = 1080
VERTICAL_OUT_H = 1920


@dataclass
class WordSpan:
    """Lightweight word timing for ASS generation (seconds relative to clip start)."""

    start: float
    end: float
    word: str


def transcribe_video_words(video_path: str):
    """
    Full-video transcription with word timestamps (one Whisper pass).
    Returns list of objects with .start, .end, .word (same shape as OpenAI word objects).
    """
    logger.info(f"🎙️ transcribe_video_words: starting full-video transcription for {video_path}")
    temp_files = []
    try:
        audio_file = extract_audio(video_path)
        temp_files.append(audio_file)
        words = get_word_timestamps_from_audio(audio_file)
        logger.info(f"✅ transcribe_video_words: got {len(words)} words")
        return words
    finally:
        for f in temp_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                    logger.info(f"🧹 transcribe_video_words cleanup: {f}")
                except OSError as e:
                    logger.warning(f"Could not remove {f}: {e}")


def words_for_segment(words, segment_start: float, segment_duration: float) -> list[WordSpan]:
    """
    Keep words overlapping [segment_start, segment_start + segment_duration), re-based to t=0.
    """
    seg_end = segment_start + segment_duration
    out: list[WordSpan] = []
    for w in words:
        w_start = float(w.start)
        w_end = float(w.end)
        if w_end <= segment_start or w_start >= seg_end:
            continue
        adj_start = max(0.0, w_start - segment_start)
        adj_end = min(segment_duration, w_end - segment_start)
        if adj_end <= adj_start:
            continue
        out.append(WordSpan(start=adj_start, end=adj_end, word=str(w.word)))
    logger.info(
        f"   words_for_segment: [{segment_start:.2f}, {seg_end:.2f}) -> {len(out)} words after trim"
    )
    return out


def _escape_filter_path(path: str) -> str:
    """Escape path for ffmpeg filter arguments (subtitles=..., drawtext textfile=...)."""
    s = path.replace("\\", "/")
    s = s.replace(":", "\\:")
    s = s.replace("'", "\\'")
    return s


def render_vertical_short_clip(
    video_path: str,
    output_path: str,
    segment_start: float,
    segment_duration: float,
    title: str,
    words_segment: list[WordSpan],
    *,
    title_fontsize: int = 44,
    caption_font_size: int = 52,
) -> None:
    """
    One vertical 9:16 clip: scale horizontal video to width, pad to 1080x1920 black bars,
    white title in top bar (via drawtext + textfile), karaoke ASS captions near bottom.
    """
    logger.info(
        f"🎬 render_vertical_short_clip: out={output_path} start={segment_start}s "
        f"dur={segment_duration}s title={title!r}"
    )
    title_fd, title_path = tempfile.mkstemp(suffix=".txt")
    os.close(title_fd)

    temp_files: list[str] = [title_path]
    try:
        with open(title_path, "w", encoding="utf-8") as tf:
            tf.write(title.strip() or " ")

        # WordSpan works with create_ass if we pass objects with .start/.end/.word
        ass_path = create_ass_subtitle_file(
            words_segment,
            width=VERTICAL_OUT_W,
            height=VERTICAL_OUT_H,
            position="bottom",
            font_size=caption_font_size,
        )
        temp_files.append(ass_path)

        # Build video filter: scale fit width, pad 9:16, title, burn subs
        esc_ass = _escape_filter_path(os.path.abspath(ass_path))
        esc_title = _escape_filter_path(os.path.abspath(title_path))

        vf = (
            f"scale={VERTICAL_OUT_W}:-1,"
            f"pad={VERTICAL_OUT_W}:{VERTICAL_OUT_H}:(ow-iw)/2:(oh-ih)/2:black,"
            f"drawtext=fontcolor=white:fontsize={title_fontsize}:x=(w-text_w)/2:y=72:"
            f"textfile='{esc_title}',"
            f"subtitles='{esc_ass}'"
        )

        # -ss after -i: more accurate cuts (aligns with Whisper timestamps)
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-ss",
            str(segment_start),
            "-t",
            str(segment_duration),
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-pix_fmt",
            "yuv420p",
            output_path,
        ]
        logger.info(f"   ffmpeg: {' '.join(cmd[:8])} ... {output_path}")
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            logger.error(f"ffmpeg stderr:\n{proc.stderr}")
            raise RuntimeError(f"ffmpeg failed with code {proc.returncode}")
        logger.info(f"✅ Wrote vertical clip: {output_path}")
    finally:
        for f in temp_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass


def run_vertical_shorts_batch(
    video_path: str,
    segments: list[tuple[float, str]],
    clip_duration: float = 60.0,
    output_dir: Optional[str] = None,
    *,
    title_fontsize: int = 44,
    caption_font_size: int = 52,
) -> list[str]:
    """
    Transcribe once, then render each (start_sec, title) as a vertical 9:16 clip of clip_duration seconds.
    Returns list of output file paths.
    """
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(video_path))
    os.makedirs(output_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(video_path))[0]

    logger.info(f"📋 run_vertical_shorts_batch: video={video_path} output_dir={output_dir}")
    logger.info(f"   segments count={len(segments)} clip_duration={clip_duration}s")

    words = transcribe_video_words(video_path)
    out_paths: list[str] = []

    for idx, (start_sec, title) in enumerate(segments, start=1):
        seg_words = words_for_segment(words, start_sec, clip_duration)
        safe_title = re.sub(r"[^\w\s-]", "", title)[:40].strip().replace(" ", "_") or f"part_{idx}"
        out_name = f"{base}_vertical_{idx:02d}_{safe_title}.mp4"
        out_path = os.path.join(output_dir, out_name)
        logger.info(f"--- Clip {idx}/{len(segments)}: {start_sec}s → {start_sec + clip_duration}s | {title!r}")
        render_vertical_short_clip(
            video_path=video_path,
            output_path=out_path,
            segment_start=start_sec,
            segment_duration=clip_duration,
            title=title,
            words_segment=seg_words,
            title_fontsize=title_fontsize,
            caption_font_size=caption_font_size,
        )
        out_paths.append(out_path)

    logger.info(f"✅ run_vertical_shorts_batch: wrote {len(out_paths)} files")
    return out_paths


if __name__ == "__main__":
    # --- Hardcoded parameters: set RUN_MODE to "single" (full captioned horizontal) or "vertical_shorts" ---
    RUN_MODE = "single"  # "single" | "vertical_shorts"

    INPUT_VIDEO = "input_videos/example.mp4"

    # Edit these starts/titles after watching the source video.
    VERTICAL_SEGMENTS: list[tuple[float, str]] = [
        (0.0, "Main idea"),
        (60.0, "Second key moment"),
        (120.0, "Final takeaway"),
    ]
    CLIP_DURATION_SEC = 60.0
    OUTPUT_DIR = None  # None = same folder as INPUT_VIDEO

    CAPTIONS_POSITION = "bottom"
    FONT_SIZE = 42

    try:
        print("--- Video Captioner ---")
        print(f"RUN_MODE={RUN_MODE}")
        if not os.path.exists(INPUT_VIDEO):
            logger.error(f"Input video not found: {INPUT_VIDEO}")
            print("Set INPUT_VIDEO near the bottom of this script before running.")
            sys.exit(1)

        if RUN_MODE == "vertical_shorts":
            print(f"Rendering {len(VERTICAL_SEGMENTS)} vertical clips ({CLIP_DURATION_SEC}s each)...")
            paths = run_vertical_shorts_batch(
                INPUT_VIDEO,
                VERTICAL_SEGMENTS,
                clip_duration=CLIP_DURATION_SEC,
                output_dir=OUTPUT_DIR,
            )
            print("\nDone. Clips:")
            for p in paths:
                print(f"  - {p}")
        else:
            file_name, file_extension = os.path.splitext(INPUT_VIDEO)
            output_video_file = f"{file_name}_captioned{file_extension}"
            add_captions_to_video(
                video_path=INPUT_VIDEO,
                output_path=output_video_file,
                captions_position=CAPTIONS_POSITION,
                font_size=FONT_SIZE,
            )
            print(f"\nCaptioned video: {output_video_file}")
        print('RESULT: ' + json.dumps({"status": "succeeded", "mode": RUN_MODE, "input_video": INPUT_VIDEO}))

    except Exception:
        print("\nScript failed. See logs above.")
        traceback.print_exc()
        print('RESULT: ' + json.dumps({"status": "failed", "mode": RUN_MODE, "input_video": INPUT_VIDEO}))
        sys.exit(1)
