import os
from time import sleep

os.environ["GPIOZERO_PIN_FACTORY"] = "lgpio"

from gpiozero import DigitalInputDevice, LED


red = LED(17)
yellow = LED(27)
green = LED(22)

touch = DigitalInputDevice(
    18,
    pull_up=False,
)

pedestrian_requested = False
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


def check_touch() -> None:
    global pedestrian_requested
    global previous_touch_value

    current_value = touch.value

    if current_value == 1 and previous_touch_value == 0:
        pedestrian_requested = True
        print("Touch detected: pedestrian request created")

    previous_touch_value = current_value


def wait_with_touch(seconds: int) -> bool:
    for _ in range(seconds * 10):
        check_touch()

        if pedestrian_requested:
            return True

        sleep(0.1)

    return False


try:
    while True:
        pedestrian_requested = False

        set_lights(
            red_on=True,
            yellow_on=False,
            green_on=False,
        )
        print("RED")
        wait_with_touch(3)

        set_lights(
            red_on=False,
            yellow_on=True,
            green_on=False,
        )
        print("YELLOW")
        wait_with_touch(2)

        set_lights(
            red_on=False,
            yellow_on=False,
            green_on=True,
        )
        print("GREEN")

        request_received = wait_with_touch(8)

        if request_received:
            print("Pedestrian request accepted. Ending green phase early.")

        set_lights(
            red_on=False,
            yellow_on=True,
            green_on=False,
        )
        print("YELLOW")
        sleep(2)

except KeyboardInterrupt:
    print("\nTraffic system stopped.")

finally:
    red.off()
    yellow.off()
    green.off()
    touch.close()
