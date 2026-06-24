"""GPIO hardware adapter for LEDs and the touch sensor."""

import os

os.environ.setdefault("GPIOZERO_PIN_FACTORY", "lgpio")

from gpiozero import DigitalInputDevice, LED

from config import (
    GREEN_GPIO,
    RED_GPIO,
    TOUCH_GPIO,
    YELLOW_GPIO,
)


class TrafficLightHardware:
    """Controls the physical traffic-light hardware."""

    def __init__(self) -> None:
        self._red = LED(RED_GPIO)
        self._yellow = LED(YELLOW_GPIO)
        self._green = LED(GREEN_GPIO)

        self._touch = DigitalInputDevice(
            TOUCH_GPIO,
            pull_up=False,
        )

        self.all_off()

    def set_lights(
        self,
        *,
        red_on: bool,
        yellow_on: bool,
        green_on: bool,
    ) -> None:
        self._red.value = red_on
        self._yellow.value = yellow_on
        self._green.value = green_on

    def show_red(self) -> None:
        self.set_lights(
            red_on=True,
            yellow_on=False,
            green_on=False,
        )

    def show_yellow(self) -> None:
        self.set_lights(
            red_on=False,
            yellow_on=True,
            green_on=False,
        )

    def show_green(self) -> None:
        self.set_lights(
            red_on=False,
            yellow_on=False,
            green_on=True,
        )

    def all_off(self) -> None:
        self.set_lights(
            red_on=False,
            yellow_on=False,
            green_on=False,
        )

    def is_touch_active(self) -> bool:
        return bool(self._touch.value)

    def close(self) -> None:
        self.all_off()

        self._red.close()
        self._yellow.close()
        self._green.close()
        self._touch.close()

