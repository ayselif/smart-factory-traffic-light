"""Domain models shared by the controller and OPC UA layers."""

from dataclasses import dataclass
from enum import IntEnum

from config import (
    DEFAULT_GREEN_AFTER_TOUCH_DURATION,
    DEFAULT_GREEN_DURATION,
    DEFAULT_RED_DURATION,
    DEFAULT_YELLOW_DURATION,
)


class TrafficMode(IntEnum):
    NORMAL = 0
    PEDESTRIAN_PRIORITY = 1


class TrafficColor:
    OFF = "OFF"
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"
    FAULT = "FAULT"


@dataclass
class TrafficLightState:
    current_color: str = TrafficColor.OFF

    red_on: bool = False
    yellow_on: bool = False
    green_on: bool = False

    mode: TrafficMode = TrafficMode.NORMAL

    touch_detected: bool = False
    pedestrian_requested: bool = False


@dataclass
class TrafficLightConfiguration:
    red_duration: float = DEFAULT_RED_DURATION
    yellow_duration: float = DEFAULT_YELLOW_DURATION
    green_duration: float = DEFAULT_GREEN_DURATION
    green_after_touch_duration: float = (
        DEFAULT_GREEN_AFTER_TOUCH_DURATION
    )

    def validate(self) -> None:
        durations = {
            "red_duration": self.red_duration,
            "yellow_duration": self.yellow_duration,
            "green_duration": self.green_duration,
            "green_after_touch_duration": (
                self.green_after_touch_duration
            ),
        }

        for name, value in durations.items():
            if value <= 0:
                raise ValueError(
                    f"{name} must be greater than zero."
                )
