"""
Screen Recorder — Full-screen capture for screencast tutorials.

Two modes:
1. Screencast mode (Xvfb + FFmpeg): Records the full virtual display including
   browser chrome (address bar, tabs), cursor movements, and all visual elements.
   Best for tutorials and product demos.
2. Playwright mode (fallback): Uses Playwright's built-in video recording which
   captures page content only. No cursor or browser chrome visible.

Both modes track events (clicks, scrolls, navigations) for post-production
zoom/click effects via demo_video_composer.py.

Usage (screencast mode):
    recorder = ScreenRecorder(mode="screencast")
    display = recorder.start_display()       # Start Xvfb virtual display
    # ... launch browser with headless=False on DISPLAY ...
    recorder.start_recording("my_tutorial")  # Start FFmpeg capture
    recorder.log_click(500, 300, "Sign In button")
    recorder.move_cursor(500, 300)           # Move visible X11 cursor
    # ... more actions ...
    recorder.stop_recording()                # Stop FFmpeg, save video + events
    recorder.stop_display()                  # Clean up Xvfb

Usage (playwright mode — backward compat):
    recorder = ScreenRecorder(mode="playwright")
    recorder.start("demo")                   # Start event logging
    # ... Playwright records via record_video_dir ...
    recorder.stop(video_path="...")          # Save events, set video path
"""

import json
import logging
import os
import signal
import subprocess
import time
from datetime import datetime

logger = logging.getLogger("screen_recorder")

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
RECORDINGS_DIR = os.path.join(REPO_ROOT, "screen_recordings")

CHROME_BAR_HEIGHT = 85


class ScreenRecorder:
    """Records browser sessions via Xvfb+FFmpeg (screencast) or Playwright (fallback)."""

    def __init__(self, width=1920, height=1080, fps=30, mode="playwright", output_dir=None):
        self.width = width
        self.height = height
        self.fps = fps
        self.mode = mode
        self.output_dir = output_dir or RECORDINGS_DIR

        self.display = None
        self._xvfb_proc = None
        self._original_display = os.environ.get("DISPLAY")

        self._ffmpeg_proc = None

        self.video_path = None
        self.events_path = None
        self.events = []
        self.start_time = None
        self.is_recording = False
        self._filename_prefix = "recording"

    # ─── Xvfb (virtual display) ──────────────────────────────

    def start_display(self):
        """Start Xvfb virtual display on an available display number.
        Returns the display string (e.g. ':99').
        """
        if self.mode != "screencast":
            logger.info("Not in screencast mode — skipping Xvfb")
            return None

        for num in range(99, 130):
            lock_file = f"/tmp/.X{num}-lock"
            if not os.path.exists(lock_file):
                self.display = f":{num}"
                break
        else:
            raise RuntimeError("No available X display numbers (:99-:129)")

        logger.info(f"Starting Xvfb on display {self.display} ({self.width}x{self.height}x24)")

        self._xvfb_proc = subprocess.Popen(
            [
                "Xvfb", self.display,
                "-screen", "0", f"{self.width}x{self.height}x24",
                "+extension", "RANDR",
                "-ac",
                "-nolisten", "tcp",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

        time.sleep(1.0)

        if self._xvfb_proc.poll() is not None:
            stderr = self._xvfb_proc.stderr.read().decode() if self._xvfb_proc.stderr else ""
            raise RuntimeError(f"Xvfb failed to start on {self.display}: {stderr}")

        os.environ["DISPLAY"] = self.display
        logger.info(f"DISPLAY set to {self.display}")

        try:
            subprocess.run(
                ["xsetroot", "-cursor_name", "left_ptr"],
                env={"DISPLAY": self.display, "PATH": os.environ.get("PATH", "/usr/bin")},
                timeout=5,
                capture_output=True,
            )
            logger.info("Default cursor set (left_ptr)")
        except Exception as e:
            logger.warning(f"Could not set cursor theme: {e}")

        logger.info(f"Xvfb started on {self.display} (PID {self._xvfb_proc.pid})")
        return self.display

    def stop_display(self):
        """Stop the Xvfb virtual display and restore DISPLAY env var."""
        if self._xvfb_proc:
            pid = self._xvfb_proc.pid
            logger.info(f"Stopping Xvfb on {self.display} (PID {pid})")
            try:
                self._xvfb_proc.terminate()
                self._xvfb_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Xvfb didn't stop gracefully, killing...")
                self._xvfb_proc.kill()
                try:
                    self._xvfb_proc.wait(timeout=3)
                except Exception:
                    pass
            except Exception as e:
                logger.warning(f"Error stopping Xvfb: {e}")
            self._xvfb_proc = None

        if self._original_display:
            os.environ["DISPLAY"] = self._original_display
        elif "DISPLAY" in os.environ:
            del os.environ["DISPLAY"]

        if self.display:
            num = self.display.lstrip(":")
            lock_file = f"/tmp/.X{num}-lock"
            try:
                if os.path.exists(lock_file):
                    os.remove(lock_file)
            except Exception:
                pass

        logger.info("Xvfb stopped and DISPLAY restored")

    def get_display(self):
        """Return the current Xvfb display string (e.g., ':99')."""
        return self.display

    # ─── FFmpeg recording ────────────────────────────────────

    def start_recording(self, filename_prefix="recording"):
        """Start screen capture.
        Screencast mode: starts FFmpeg on the Xvfb display.
        Playwright mode: just starts event logging (Playwright records separately).
        """
        self._filename_prefix = filename_prefix
        self.events = []
        self.start_time = time.time()
        self.is_recording = True

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(self.output_dir, exist_ok=True)
        self.events_path = os.path.join(
            self.output_dir, f"{filename_prefix}_{ts}_events.json"
        )

        if self.mode == "screencast":
            if not self.display:
                raise RuntimeError("No Xvfb display — call start_display() first")

            self.video_path = os.path.join(
                self.output_dir, f"{filename_prefix}_{ts}.mp4"
            )

            cmd = [
                "ffmpeg", "-y",
                "-f", "x11grab",
                "-video_size", f"{self.width}x{self.height}",
                "-framerate", str(self.fps),
                "-draw_mouse", "1",
                "-i", self.display,
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-pix_fmt", "yuv420p",
                "-crf", "20",
                self.video_path,
            ]

            logger.info(f"Starting FFmpeg recording: {' '.join(cmd)}")
            self._ffmpeg_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                env={**os.environ, "DISPLAY": self.display},
            )

            time.sleep(0.5)
            if self._ffmpeg_proc.poll() is not None:
                stderr = self._ffmpeg_proc.stderr.read().decode() if self._ffmpeg_proc.stderr else ""
                self.is_recording = False
                raise RuntimeError(f"FFmpeg failed to start: {stderr}")

            logger.info(f"FFmpeg recording started (PID {self._ffmpeg_proc.pid})")
            logger.info(f"  Display: {self.display} | {self.width}x{self.height} @ {self.fps}fps")
            logger.info(f"  Output: {self.video_path}")
        else:
            logger.info("Playwright mode — event logging only (Playwright records video)")
            logger.info(f"  Events will be saved to: {self.events_path}")

        return self.events_path

    def stop_recording(self):
        """Stop recording and save events log. Returns video path."""
        if not self.is_recording:
            logger.warning("No recording in progress")
            return None

        self.is_recording = False
        duration = time.time() - self.start_time if self.start_time else 0

        if self.mode == "screencast" and self._ffmpeg_proc:
            logger.info("Stopping FFmpeg recording...")
            try:
                self._ffmpeg_proc.send_signal(signal.SIGINT)
                self._ffmpeg_proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                logger.warning("FFmpeg didn't stop gracefully, killing...")
                self._ffmpeg_proc.kill()
                try:
                    self._ffmpeg_proc.wait(timeout=5)
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"Error stopping FFmpeg: {e}")
            self._ffmpeg_proc = None

        self._save_events(duration)

        if self.video_path and os.path.exists(self.video_path):
            size_mb = os.path.getsize(self.video_path) / (1024 * 1024)
            logger.info(f"Recording stopped after {duration:.1f}s")
            logger.info(f"  Video: {self.video_path} ({size_mb:.1f} MB)")
            logger.info(f"  Events: {self.events_path} ({len(self.events)} events)")
        else:
            logger.info(f"Recording stopped after {duration:.1f}s (video path: {self.video_path})")

        return self.video_path

    def _save_events(self, duration=None):
        """Save the events log to JSON."""
        if duration is None:
            duration = time.time() - self.start_time if self.start_time else 0

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not self.events_path:
            os.makedirs(self.output_dir, exist_ok=True)
            self.events_path = os.path.join(
                self.output_dir, f"{self._filename_prefix}_{ts}_events.json"
            )

        with open(self.events_path, "w") as f:
            json.dump({
                "recording_file": self.video_path or "pending",
                "mode": self.mode,
                "duration_seconds": round(duration, 2),
                "width": self.width,
                "height": self.height,
                "fps": self.fps,
                "display": self.display,
                "chrome_bar_height": CHROME_BAR_HEIGHT if self.mode == "screencast" else 0,
                "events": self.events,
            }, f, indent=2)

    # ─── Cursor control (screencast mode) ────────────────────

    def move_cursor(self, x, y, chrome_offset=True):
        """Move the X11 cursor to position using xdotool.
        When chrome_offset=True, adds CHROME_BAR_HEIGHT to y so page coordinates
        map correctly to the browser window (which includes tab bar + address bar).
        """
        if self.mode != "screencast" or not self.display:
            return

        display_y = y + CHROME_BAR_HEIGHT if chrome_offset else y

        try:
            subprocess.run(
                ["xdotool", "mousemove", "--screen", "0", str(int(x)), str(int(display_y))],
                env={"DISPLAY": self.display, "PATH": os.environ.get("PATH", "/usr/bin")},
                timeout=2,
                capture_output=True,
            )
        except Exception as e:
            logger.debug(f"xdotool mousemove failed: {e}")

    def smooth_move_cursor(self, from_x, from_y, to_x, to_y, steps=20, duration=0.4, chrome_offset=True):
        """Smoothly animate cursor from one position to another using eased interpolation."""
        if self.mode != "screencast" or not self.display:
            return

        step_delay = duration / steps
        for i in range(steps + 1):
            t = i / steps
            eased = t * t * (3.0 - 2.0 * t)
            cx = from_x + (to_x - from_x) * eased
            cy = from_y + (to_y - from_y) * eased
            self.move_cursor(cx, cy, chrome_offset=chrome_offset)
            time.sleep(step_delay)

    # ─── Event logging ───────────────────────────────────────

    def _elapsed(self):
        return round(time.time() - self.start_time, 3) if self.start_time else 0

    def log_click(self, x, y, element="", button="left"):
        """Log a click event and move cursor if in screencast mode."""
        if self.is_recording and self.mode == "screencast":
            self.move_cursor(x, y)

        event = {
            "type": "click",
            "timestamp": self._elapsed(),
            "x": x,
            "y": y,
            "element": element,
            "button": button,
        }
        self.events.append(event)
        logger.info(f"Event: click at ({x},{y}) on '{element}' @ {event['timestamp']}s")

    def log_scroll(self, direction="down", amount=300, x=960, y=540):
        """Log a scroll event."""
        if self.is_recording and self.mode == "screencast":
            self.move_cursor(x, y)

        event = {
            "type": "scroll",
            "timestamp": self._elapsed(),
            "direction": direction,
            "amount": amount,
            "x": x,
            "y": y,
        }
        self.events.append(event)
        logger.info(f"Event: scroll {direction} {amount}px @ {event['timestamp']}s")

    def log_type(self, text, element=""):
        """Log a typing event."""
        event = {
            "type": "type",
            "timestamp": self._elapsed(),
            "text_preview": text[:50],
            "char_count": len(text),
            "element": element,
        }
        self.events.append(event)
        logger.info(f"Event: type '{text[:30]}...' into '{element}' @ {event['timestamp']}s")

    def log_navigate(self, url):
        """Log a navigation event."""
        event = {
            "type": "navigate",
            "timestamp": self._elapsed(),
            "url": url,
        }
        self.events.append(event)
        logger.info(f"Event: navigate to {url[:60]} @ {event['timestamp']}s")

    def log_marker(self, label):
        """Log a custom marker (scene change, section start, etc.)."""
        event = {
            "type": "marker",
            "timestamp": self._elapsed(),
            "label": label,
        }
        self.events.append(event)
        logger.info(f"Event: marker '{label}' @ {event['timestamp']}s")

    # ─── Playwright compatibility (backward compat) ──────────

    def get_video_dir(self):
        """Return the directory for Playwright's record_video_dir."""
        os.makedirs(self.output_dir, exist_ok=True)
        return self.output_dir

    def get_video_size(self):
        """Return the video size dict for Playwright's record_video_size."""
        return {"width": self.width, "height": self.height}

    def set_video_path(self, path):
        """Set the video path (used when Playwright saves the video)."""
        self.video_path = path
        logger.info(f"Video path set: {path}")

    def start(self, filename_prefix="recording"):
        """Legacy start method — calls start_recording."""
        return self.start_recording(filename_prefix=filename_prefix)

    def stop(self, video_path=None):
        """Legacy stop method — calls stop_recording."""
        if video_path:
            self.video_path = video_path
        return self.stop_recording()
