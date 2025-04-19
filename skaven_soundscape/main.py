from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, List, Optional
import os
import pygame
import random
import time

load_dotenv()  # Reads .env file if present

USE_GPIO = os.getenv("USE_GPIO", "false").lower() == "true"
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
SOUND_VOLUME = float(os.getenv("SOUND_VOLUME", 0.75))
SOUND_PATTERN = "*.wav"


def pick_random_category() -> str:
    return random.choices(
        ["rats", "chains", "screams"],
        weights=[0.6, 0.3, 0.1],
        k=1,
    )[0]


def load_sound_categories(base_path: Path) -> Dict[str, List[Path]]:
    return {
        "rats": list((base_path / "rats").glob(SOUND_PATTERN)),
        "chains": list((base_path / "chains").glob(SOUND_PATTERN)),
        "screams": list((base_path / "screams").glob(SOUND_PATTERN)),
    }


def main(iterations: Optional[int] = None) -> None:
    pygame.init()
    pygame.mixer.init()

    sound_root = Path(__file__).resolve().parent.parent / "sounds"
    categories = load_sound_categories(sound_root)

    ambient_file = sound_root / "ambient" / "sewer_loop_1.wav"
    pygame.mixer.music.load(str(ambient_file))
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play(-1)  # Loop forever

    try:
        loop = (
            range(iterations) if iterations is not None else iter(int, 1)
        )  # Infinite if None
        for _ in loop:
            time.sleep(random.uniform(4, 15))

            category = pick_random_category()
            sound = random.choice(categories[category])
            sfx = pygame.mixer.Sound(str(sound))
            sfx.set_volume(random.uniform(0.5, 1.0))
            sfx.play()
    except KeyboardInterrupt:
        pygame.mixer.music.stop()


if __name__ == "__main__":
    main()
