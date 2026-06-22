import os
from time import monotonic, sleep

os.environ["GPIOZERO_PIN_FACTORY"] = "lgpio"

from gpiozero import DigitalInputDevice, LED


RED_DURATION = 30
YELLOW_DURATION = 5
GREEN_DURATION = 20
GREEN_AFTER_TOUCH_DURATION = 6

red = LED(17)
yellow = LED(27)
green = LED(22)

touch = DigitalInputDevice(
    18,
    pull_up=False,
)

previous_touch_value = touch.value


def set_lights(
    *,
    red_on: bool,
    yellow_on: bool,
    green_on: bool,
) -> None:
    red.value = red_on
    yellow.value = yellow_on
    green.value = green_on


def touch_activated() -> bool:
    global previous_touch_value

    current_value = touch.value

    activated = (
        current_value == 1
        and previous_touch_value == 0
    )

    previous_touch_value = current_value
    return activated


def wait_normally(seconds: int) -> None:
    end_time = monotonic() + seconds

    while monotonic() < end_time:
        sleep(0.1)


def run_green_phase() -> None:
    print(f"GREEN - maximum {GREEN_DURATION} seconds")

    green_end_time = monotonic() + GREEN_DURATION
    touch_request_time = None

    while monotonic() < green_end_time:
        if touch_request_time is None and touch_activated():
            touch_request_time = monotonic()

            print(
                "Touch detected. "
                f"Green will end in {GREEN_AFTER_TOUCH_DURATION} seconds."
            )

        if touch_request_time is not None:
            requested_end_time = (
                touch_request_time
                + GREEN_AFTER_TOUCH_DURATION
            )

            if monotonic() >= requested_end_time:
                print("Touch waiting period completed.")
                return

        sleep(0.1)


try:
    while True:
        set_lights(
            red_on=True,
            yellow_on=False,
            green_on=False,
        )
        print(f"RED - {RED_DURATION} seconds")
        wait_normally(RED_DURATION)

        set_lights(
            red_on=False,
            yellow_on=True,
            green_on=False,
        )
        print(f"YELLOW - {YELLOW_DURATION} seconds")
        wait_normally(YELLOW_DURATION)

        set_lights(
            red_on=False,
            yellow_on=False,
            green_on=True,
        )
        run_green_phase()

        set_lights(
            red_on=False,
            yellow_on=True,
            green_on=False,
        )
        print(f"YELLOW - {YELLOW_DURATION} seconds")
        wait_normally(YELLOW_DURATION)

except KeyboardInterrupt:
    print("\nTraffic system stopped.")

finally:
    red.off()
    yellow.off()
    green.off()
    touch.close()
