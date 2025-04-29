"""
Stub module for gpiozero Servo class
"""

from typing import Optional


class Servo:
    """Stub for GPIO-controlled Servo motor."""

    def __init__(
        self,
        pin: int,
        min_pulse_width: float = 0.001,
        max_pulse_width: float = 0.002,
    ) -> None:
        # Initialize servo value; -1.0 to 1.0 range
        self.value: Optional[float] = None

    def mid(self) -> None:
        # Center servo
        self.value = 0.0
