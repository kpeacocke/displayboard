from dotenv import load_dotenv
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
import os
import pygame
import random
import time
import threading


load_dotenv()

USE_GPIO = os.getenv("USE_GPIO", "false").lower() == "true"
DEBUG_MODE = os.environ.get("DEBUG_MODE", "false").lower() == "true"
SOUND_VOLUME = float(os.getenv("SOUND_VOLUME", 0.75))

# Any audio ext you care about
AUDIO_EXTS = [".wav", ".ogg", ".mp3"]


def list_audio_files(path: Path) -> List[Path]:
    """Return a list of AUDIO_EXTS files in `path`, or empty if none."""
    files: List[Path] = []
    for ext in AUDIO_EXTS:
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
) -> None:
    """Continuously cross‑fade through your ambient tracks, if any."""
    if not ambient_files:
        return
    chan = pygame.mixer.Channel(0)
    idx = 0
    while True:
        snd = pygame.mixer.Sound(str(ambient_files[idx]))
        snd.set_volume(volume)
        chan.play(snd, fade_ms=fade_ms)

        length = snd.get_length()
        # sleep until just before next fade
        time.sleep(max(0.0, length - fade_ms / 1000.0))
        chan.fadeout(fade_ms)
        time.sleep(fade_ms / 1000.0)
        idx = (idx + 1) % len(ambient_files)


def chains_loop(chain_files: List[Path]) -> None:
    """Every 15–120 s play exactly one chain sound at random ≤ 0.5 volume."""
    if not chain_files:
        return
    while True:
        time.sleep(random.uniform(15, 120))
        p = random.choice(chain_files)
        s = pygame.mixer.Sound(str(p))
        s.set_volume(random.uniform(0.0, 0.5))
        s.play()


def skaven_loop(skaven_files: List[Path]) -> None:
    """Every 20–40 s play exactly one skaven sound at random volume."""
    if not skaven_files:
        return
    while True:
        time.sleep(random.uniform(20, 40))
        track = random.choice(skaven_files)
        sfx = pygame.mixer.Sound(str(track))
        sfx.set_volume(random.uniform(0.0, 1.0))
        sfx.play()


def rats_loop(
    rat_files: List[Path],
    channels: Sequence[Any],  # channel-like objects supporting play/fadeout
) -> None:
    """
    Keep at least one rat sound playing, and every 2–6 s
    pick a new random "horde" of up to len(channels) rats
    at varying volumes.
    """
    if not rat_files:
        return
    while True:
        # fade out current
        for c in channels:
            c.fadeout(500)
        time.sleep(0.5)

        # choose how many to play (1..min(channels, files))
        max_n = min(len(channels), len(rat_files))
        n = random.randint(1, max_n)
        picks = random.sample(rat_files, n)

        # random weights → volumes
        weights = [random.random() for _ in picks]
        tot = sum(weights) or 1.0
        for idx, p in enumerate(picks):
            snd = pygame.mixer.Sound(str(p))
            snd.set_volume(SOUND_VOLUME * (weights[idx] / tot))
            channels[idx].play(snd)

        time.sleep(random.uniform(2, 6))


def main(stop_after: Optional[int] = None) -> None:
    # Main function logic
    if stop_after is not None:
        print(f"Stopping after {stop_after} cycles")

    pygame.init()
    pygame.mixer.init()
    # adjust as needed
    pygame.mixer.set_num_channels(16)

    sounds_dir = Path(__file__).resolve().parent.parent / "sounds"
    cats = load_sound_categories(sounds_dir)
    ambient_files = cats["ambient"]
    rat_files = cats["rats"]
    chain_files = cats["chains"]
    scream_files = cats["screams"]
    skaven_files = cats["skaven"]

    # Ambient on channel 0
    threading.Thread(
        target=ambient_loop,
        args=(ambient_files, 3000, SOUND_VOLUME),
        daemon=True,
    ).start()

    # Chains anywhere
    threading.Thread(
        target=chains_loop,
        args=(chain_files,),
        daemon=True,
    ).start()

    # Skaven anywhere
    threading.Thread(
        target=skaven_loop,
        args=(skaven_files,),
        daemon=True,
    ).start()

    # Rats on channels 1–4
    rat_chans = [pygame.mixer.Channel(i) for i in range(1, 5)]
    threading.Thread(
        target=rats_loop,
        args=(rat_files, rat_chans),
        daemon=True,
    ).start()

    # Main thread: scream SFX every 2 minutes
    try:
        while True:
            time.sleep(120)
            if not scream_files:
                continue
            p = random.choice(scream_files)
            s = pygame.mixer.Sound(str(p))
            s.set_volume(SOUND_VOLUME)
            s.play()
    except KeyboardInterrupt:
        # graceful shutdown
        pygame.mixer.Channel(0).fadeout(2000)
        for c in rat_chans:
            c.fadeout(1000)
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            pass


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
]
