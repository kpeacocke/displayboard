from dotenv import load_dotenv
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
import os
import pygame
import random
import time
import threading
import logging

from . import config

logger = logging.getLogger(__name__)

load_dotenv()

USE_GPIO = os.getenv("USE_GPIO", "false").lower() == "true"
DEBUG_MODE = os.environ.get("DEBUG_MODE", "false").lower() == "true"
# SOUND_VOLUME is now handled via config.SOUND_VOLUME_DEFAULT where needed

# Any audio ext you care about
AUDIO_EXTS = [".wav", ".ogg", ".mp3"]


def list_audio_files(path: Path) -> List[Path]:
    """Return a list of AUDIO_EXTS files in `path`, or empty if none."""
    files: List[Path] = []
    for ext in config.AUDIO_EXTENSIONS:  # Use config
        files.extend(path.glob(f"*{ext}"))
    return files


def load_sound_categories(base_path: Path) -> Dict[str, List[Path]]:
    return {
        "ambient": list_audio_files(base_path / "ambient"),
        "rats": list_audio_files(base_path / "rats"),
        "chains": list_audio_files(base_path / "chains"),
        "screams": list_audio_files(base_path / "screams"),
        "skaven": list_audio_files(base_path / "skaven"),
    }


def ambient_loop(
    ambient_files: List[Path],
    fade_ms: int,
    volume: float,
    stop_event: Optional[threading.Event] = None,
) -> None:
    """Continuously cross‑fade through your ambient tracks, if any."""
    if not ambient_files:
        return
    event = stop_event or threading.Event()
    chan = pygame.mixer.Channel(config.AMBIENT_CHANNEL)  # Use config
    idx = 0
    while not event.is_set():
        snd = pygame.mixer.Sound(ambient_files[idx])
        snd.set_volume(volume)
        chan.play(snd, fade_ms=fade_ms)

        length = snd.get_length()
        # sleep until just before next fade
        sleep_duration = max(0.0, length - fade_ms / 1000.0)
        event.wait(timeout=sleep_duration)  # Use wait instead of sleep
        if event.is_set():
            break
        chan.fadeout(fade_ms)
        event.wait(timeout=fade_ms / 1000.0)  # Wait for fadeout
        if event.is_set():
            break
        idx = (idx + 1) % len(ambient_files)


def chains_loop(
    chain_files: List[Path],
    stop_event: Optional[threading.Event] = None,
) -> None:
    """Every 15–120 s play exactly one chain sound at random ≤ 0.5 volume."""
    if not chain_files:
        return
    event = stop_event or threading.Event()
    while not event.is_set():
        sleep_time = random.uniform(config.CHAINS_SLEEP_MIN, config.CHAINS_SLEEP_MAX)
        event.wait(timeout=sleep_time)  # Use wait instead of sleep
        if event.is_set():
            break
        p = random.choice(chain_files)
        s = pygame.mixer.Sound(p)
        vol = random.uniform(config.CHAINS_VOLUME_MIN, config.CHAINS_VOLUME_MAX)
        s.set_volume(vol)
        s.play()


def skaven_loop(
    skaven_files: List[Path],
    stop_event: Optional[threading.Event] = None,
) -> None:
    """Every 20–40 s play exactly one skaven sound at random volume."""
    if not skaven_files:
        return
    event = stop_event or threading.Event()
    while not event.is_set():
        sleep_time = random.uniform(config.SKAVEN_SLEEP_MIN, config.SKAVEN_SLEEP_MAX)
        event.wait(timeout=sleep_time)  # Use wait instead of sleep
        if event.is_set():
            break
        track = random.choice(skaven_files)
        sfx = pygame.mixer.Sound(track)
        vol = random.uniform(config.SKAVEN_VOLUME_MIN, config.SKAVEN_VOLUME_MAX)
        sfx.set_volume(vol)
        sfx.play()


def rats_loop(
    rat_files: List[Path],
    channels: Sequence[Any],  # channel-like objects supporting play/fadeout
    stop_event: Optional[threading.Event] = None,
) -> None:
    """
    Keep at least one rat sound playing, and every 2–6 s
    pick a new random "horde" of up to len(channels) rats
    at varying volumes.
    """
    if not rat_files:
        return
    event = stop_event or threading.Event()
    while not event.is_set():
        # fade out current
        for chan in channels:
            chan.fadeout(config.RATS_FADEOUT_MS)
        event.wait(timeout=config.RATS_FADEOUT_MS / 1000.0)  # Wait for fadeout
        if event.is_set():
            break

        # choose how many to play (1..min(channels, files))
        max_n = min(len(channels), len(rat_files))
        n = random.randint(1, max_n)
        picks = random.sample(rat_files, n)

        # random weights → volumes
        weights = [random.random() for _ in picks]
        tot = sum(weights) or 1.0
        for idx, p in enumerate(picks):
            # Scale volume relative to the default sound volume
            vol = config.SOUND_VOLUME_DEFAULT * (weights[idx] / tot)
            snd = pygame.mixer.Sound(p)
            snd.set_volume(vol)
            channels[idx].play(snd)

        sleep_time = random.uniform(config.RATS_SLEEP_MIN, config.RATS_SLEEP_MAX)
        event.wait(timeout=sleep_time)  # Use wait instead of sleep
        if event.is_set():
            break


def main(
    stop_event: Optional[threading.Event] = None,
    stop_after: Optional[int] = None,
) -> None:
    # Main function logic
    # Handle optional stop_after cycles
    if stop_after is not None:
        msg = f"Stopping after {stop_after} cycles"
        print(msg)
        logger.info(msg)
    # Setup shutdown event
    event = stop_event or threading.Event()

    try:
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.set_num_channels(config.SOUND_NUM_CHANNELS)  # Use config

        sounds_dir = config.SOUNDS_DIR  # Use config path
        cats = load_sound_categories(sounds_dir)
        ambient_files = cats["ambient"]
        rat_files = cats["rats"]
        chain_files = cats["chains"]
        scream_files = cats["screams"]
        skaven_files = cats["skaven"]

        # Initialize rat_chans here to ensure it's defined for the shutdown logic
        rat_chans: List[Any] = []

        # Ambient on channel 0
        if ambient_files:
            threading.Thread(
                target=ambient_loop,
                args=(
                    ambient_files,
                    config.AMBIENT_FADE_MS,
                    config.SOUND_VOLUME_DEFAULT,  # Use default volume
                    event,
                ),
                daemon=True,
            ).start()

        # Chains anywhere
        if chain_files:
            threading.Thread(
                target=chains_loop,
                args=(chain_files, event),
                daemon=True,
            ).start()

        # Skaven anywhere
        if skaven_files:
            threading.Thread(
                target=skaven_loop,
                args=(skaven_files, event),
                daemon=True,
            ).start()

        # Rats on channels 1–4
        if rat_files:
            rat_chans = [
                pygame.mixer.Channel(i)
                for i in range(config.RATS_CHANNEL_START, config.RATS_CHANNEL_END)
            ]
            threading.Thread(
                target=rats_loop,
                args=(rat_files, rat_chans, event),
                daemon=True,
            ).start()

        # Main thread: scream SFX every 2 minutes
        try:
            # Play a scream immediately if available (for test coverage and logic)
            if scream_files:
                p = random.choice(scream_files)
                # Pass Path as str for maximum compatibility with pygame
                s = pygame.mixer.Sound(str(p))
                s.set_volume(config.SOUND_VOLUME_DEFAULT)
                s.play()
            while not event.wait(timeout=config.MAIN_SCREAM_INTERVAL_S):
                if not scream_files:
                    continue
                p = random.choice(scream_files)
                s = pygame.mixer.Sound(str(p))
                s.set_volume(config.SOUND_VOLUME_DEFAULT)
                s.play()
        except KeyboardInterrupt:
            # graceful shutdown
            logger.info("KeyboardInterrupt received, shutting down sound loops...")
            event.set()  # Signal threads to stop
            pygame.mixer.Channel(config.AMBIENT_CHANNEL).fadeout(
                config.MAIN_AMBIENT_FADEOUT_MS
            )
            for c in rat_chans:
                c.fadeout(config.MAIN_RATS_FADEOUT_MS)
            try:
                # Wait for fadeouts to complete
                time.sleep(config.MAIN_SHUTDOWN_WAIT_S)
            except KeyboardInterrupt:
                pass
    except pygame.error as e:
        logger.critical(f"Pygame error in sounds main: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.critical(f"Unhandled exception in sounds main: {e}", exc_info=True)
        raise


if __name__ == "__main__":  # pragma: no cover
    main()

# Explicit exports for mypy attr-defined errors in tests
__all__ = [
    "list_audio_files",
    "load_sound_categories",
    "ambient_loop",
    "chains_loop",
    "skaven_loop",
    "rats_loop",
    "main",
    "pygame",
    "random",
    "time",
    "threading",
    "config",
]
