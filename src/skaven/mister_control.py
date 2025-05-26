import time
import typing

if typing.TYPE_CHECKING:
    import RPi.GPIO as GPIO
else:
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        from unittest import mock

        GPIO = mock.MagicMock()
        GPIO.BCM = 11
        GPIO.OUT = 0
        GPIO.HIGH = 1
        GPIO.LOW = 0

# Configuration
MISTER_PIN = 22  # BCM numbering, change to your wiring


def setup() -> None:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(MISTER_PIN, GPIO.OUT)
    GPIO.output(MISTER_PIN, GPIO.LOW)  # Start OFF


def trigger_mister(duration: int = 5) -> None:
    print(f"Turning mister ON for {duration} seconds...")
    GPIO.output(MISTER_PIN, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(MISTER_PIN, GPIO.LOW)
    print("Mister OFF.")


def cleanup() -> None:
    GPIO.output(MISTER_PIN, GPIO.LOW)
    GPIO.cleanup()


def main() -> None:
    setup()
    try:
        trigger_mister(duration=5)  # Run for 5 seconds
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        cleanup()
        print("GPIO cleaned up.")


if __name__ == "__main__":
    main()
