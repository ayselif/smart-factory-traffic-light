"""Traffic-light application and domain logic."""

import asyncio
from time import monotonic

from config import GPIO_POLL_INTERVAL
from hardware import TrafficLightHardware
from models import (
    TrafficColor,
    TrafficLightConfiguration,
    TrafficLightState,
    TrafficMode,
)


class TrafficLightController:
    """Coordinates traffic rules independently from OPC UA."""

    def __init__(
        self,
        hardware: TrafficLightHardware,
    ) -> None:
        self.hardware = hardware

        self.state = TrafficLightState()
        self.configuration = TrafficLightConfiguration()

        self._shutdown_requested = False
        self._previous_touch_state = (
            self.hardware.is_touch_active()
        )

    def request_shutdown(self) -> None:
        self._shutdown_requested = True

    def change_mode(self, new_mode: int) -> bool:
        try:
            mode = TrafficMode(new_mode)
        except ValueError:
            print(f"Invalid traffic mode rejected: {new_mode}")
            return False

        self.state.mode = mode

        print(
            "Traffic mode changed: "
            f"{mode.value} / {mode.name}"
        )

        return True

    def request_pedestrian_crossing(
        self,
        source: str,
    ) -> bool:
        if self.state.pedestrian_requested:
            print(
                "Pedestrian request already exists "
                f"| source={source}"
            )
            return True

        self.state.pedestrian_requested = True

        print(
            "Pedestrian crossing requested "
            f"| source={source}"
        )

        return True

    def reset_pedestrian_request(self) -> bool:
        self.state.pedestrian_requested = False
        print("Pedestrian request reset")
        return True

    def update_configuration(
        self,
        configuration: TrafficLightConfiguration,
    ) -> bool:
        try:
            configuration.validate()
        except ValueError as error:
            print(f"Invalid configuration rejected: {error}")
            return False

        self.configuration = configuration
        return True

    def _set_state(
        self,
        color: str,
        *,
        red_on: bool,
        yellow_on: bool,
        green_on: bool,
    ) -> None:
        self.state.current_color = color
        self.state.red_on = red_on
        self.state.yellow_on = yellow_on
        self.state.green_on = green_on

        self.hardware.set_lights(
            red_on=red_on,
            yellow_on=yellow_on,
            green_on=green_on,
        )

        print(f"Traffic state: {color}")

    def _show_red(self) -> None:
        self._set_state(
            TrafficColor.RED,
            red_on=True,
            yellow_on=False,
            green_on=False,
        )

    def _show_yellow(self) -> None:
        self._set_state(
            TrafficColor.YELLOW,
            red_on=False,
            yellow_on=True,
            green_on=False,
        )

    def _show_green(self) -> None:
        self._set_state(
            TrafficColor.GREEN,
            red_on=False,
            yellow_on=False,
            green_on=True,
        )

    def _read_touch_event(self) -> bool:
        current_touch = self.hardware.is_touch_active()
        self.state.touch_detected = current_touch

        rising_edge = (
            current_touch
            and not self._previous_touch_state
        )

        self._previous_touch_state = current_touch
        return rising_edge

    async def _wait(
        self,
        duration: float,
        *,
        accept_pedestrian_request: bool,
    ) -> bool:
        end_time = monotonic() + duration

        while (
            monotonic() < end_time
            and not self._shutdown_requested
        ):
            touch_started = self._read_touch_event()

            if touch_started:
                self.request_pedestrian_crossing(
                    source="TOUCH_SENSOR"
                )

            if (
                accept_pedestrian_request
                and self.state.pedestrian_requested
            ):
                return True

            await asyncio.sleep(GPIO_POLL_INTERVAL)

        return False

    async def _run_green_phase(self) -> None:
        request_received = await self._wait(
            self.configuration.green_duration,
            accept_pedestrian_request=True,
        )

        if not request_received:
            return

        remaining_time = (
            self.configuration.green_after_touch_duration
        )

        print(
            "Pedestrian request accepted. "
            f"Green will remain active for "
            f"{remaining_time:.1f} seconds."
        )

        await self._wait(
            remaining_time,
            accept_pedestrian_request=False,
        )

    async def run(self) -> None:
        self.configuration.validate()

        try:
            while not self._shutdown_requested:
                self._show_red()

                await self._wait(
                    self.configuration.red_duration,
                    accept_pedestrian_request=False,
                )

                if self._shutdown_requested:
                    break

                self._show_yellow()

                await self._wait(
                    self.configuration.yellow_duration,
                    accept_pedestrian_request=False,
                )

                if self._shutdown_requested:
                    break

                self._show_green()
                await self._run_green_phase()

                if self._shutdown_requested:
                    break

                self._show_yellow()

                await self._wait(
                    self.configuration.yellow_duration,
                    accept_pedestrian_request=False,
                )

                if self.state.pedestrian_requested:
                    self.reset_pedestrian_request()

        finally:
            self.state.current_color = TrafficColor.OFF
            self.state.red_on = False
            self.state.yellow_on = False
            self.state.green_on = False

            self.hardware.all_off()
