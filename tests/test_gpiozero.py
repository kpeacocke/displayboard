import math
from skaven.gpiozero import Servo


def test_servo_initialization() -> None:
    # Test Servo initialization with default parameters
    servo = Servo(pin=17)
    assert servo.value is None

    # Test Servo initialization with custom parameters
    servo = Servo(pin=17, min_pulse_width=0.0005, max_pulse_width=0.0025)
    assert servo.value is None


def test_servo_mid() -> None:
    # Test the mid() method sets the servo value to 0.0
    servo = Servo(pin=17)
    servo.mid()
    # Ensure servo.value is set before float comparison for type narrowing
    assert servo.value is not None
    assert math.isclose(servo.value, 0.0, rel_tol=1e-6)
