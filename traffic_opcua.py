import asyncio
import os
from time import monotonic

os.environ["GPIOZERO_PIN_FACTORY"] = "lgpio"

from asyncua import Server
from gpiozero import DigitalInputDevice, LED


RED_DURATION = 30
YELLOW_DURATION = 5
GREEN_DURATION = 20
GREEN_AFTER_TOUCH_DURATION = 6

RED_GPIO = 17
YELLOW_GPIO = 27
GREEN_GPIO = 22
TOUCH_GPIO = 18


red = LED(RED_GPIO)
yellow = LED(YELLOW_GPIO)
green = LED(GREEN_GPIO)

touch = DigitalInputDevice(
    TOUCH_GPIO,
    pull_up=False,
)


class OpcUaNodes:
    def __init__(self) -> None:
        self.current_state = None
        self.red_on = None
        self.yellow_on = None
        self.green_on = None
        self.touch_detected = None
        self.pedestrian_requested = None


nodes = OpcUaNodes()
previous_touch_value = touch.value
pedestrian_requested_value = False


async def set_lights(
    state: str,
    *,
    red_value: bool,
    yellow_value: bool,
    green_value: bool,
) -> None:
    red.value = red_value
    yellow.value = yellow_value
    green.value = green_value

    await nodes.current_state.write_value(state)
    await nodes.red_on.write_value(red_value)
    await nodes.yellow_on.write_value(yellow_value)
    await nodes.green_on.write_value(green_value)

    print(state)


async def update_touch_state() -> bool:
    global previous_touch_value
    global pedestrian_requested_value

    current_touch_value = bool(touch.value)

    await nodes.touch_detected.write_value(current_touch_value)

    touch_activated = (
        current_touch_value
        and not previous_touch_value
    )

    previous_touch_value = current_touch_value

    if touch_activated:
        pedestrian_requested_value = True
        await nodes.pedestrian_requested.write_value(True)
        print("Touch detected: pedestrian request created")

    return touch_activated


async def wait_without_touch(seconds: float) -> None:
    end_time = monotonic() + seconds

    while monotonic() < end_time:
        # Touch is still published, but ignored during red/yellow.
        await nodes.touch_detected.write_value(bool(touch.value))
        await asyncio.sleep(0.1)


async def run_green_phase() -> None:
    global pedestrian_requested_value

    green_end_time = monotonic() + GREEN_DURATION
    touch_request_time = None

    while monotonic() < green_end_time:
        touch_activated = await update_touch_state()

        if touch_request_time is None and touch_activated:
            touch_request_time = monotonic()

            print(
                "Pedestrian request accepted. "
                f"Green will end in {GREEN_AFTER_TOUCH_DURATION} seconds."
            )

        if touch_request_time is not None:
            requested_end_time = (
                touch_request_time
                + GREEN_AFTER_TOUCH_DURATION
            )

            if monotonic() >= requested_end_time:
                return

        await asyncio.sleep(0.1)


async def traffic_cycle() -> None:
    global pedestrian_requested_value

    while True:
        pedestrian_requested_value = False
        await nodes.pedestrian_requested.write_value(False)

        await set_lights(
            "RED",
            red_value=True,
            yellow_value=False,
            green_value=False,
        )
        await wait_without_touch(RED_DURATION)

        await set_lights(
            "YELLOW",
            red_value=False,
            yellow_value=True,
            green_value=False,
        )
        await wait_without_touch(YELLOW_DURATION)

        await set_lights(
            "GREEN",
            red_value=False,
            yellow_value=False,
            green_value=True,
        )
        await run_green_phase()

        await set_lights(
            "YELLOW",
            red_value=False,
            yellow_value=True,
            green_value=False,
        )
        await wait_without_touch(YELLOW_DURATION)


async def create_opcua_server() -> Server:
    server = Server()
    await server.init()

    server.set_endpoint(
        "opc.tcp://0.0.0.0:4840/traffic-light/"
    )

    namespace_uri = "urn:smart-factory:traffic-light"
    namespace_index = await server.register_namespace(namespace_uri)

    traffic_light = await server.nodes.objects.add_object(
        namespace_index,
        "TrafficLight",
    )

    nodes.current_state = await traffic_light.add_variable(
        namespace_index,
        "CurrentState",
        "STARTING",
    )

    nodes.red_on = await traffic_light.add_variable(
        namespace_index,
        "RedOn",
        False,
    )

    nodes.yellow_on = await traffic_light.add_variable(
        namespace_index,
        "YellowOn",
        False,
    )

    nodes.green_on = await traffic_light.add_variable(
        namespace_index,
        "GreenOn",
        False,
    )

    nodes.touch_detected = await traffic_light.add_variable(
        namespace_index,
        "TouchDetected",
        False,
    )

    nodes.pedestrian_requested = await traffic_light.add_variable(
        namespace_index,
        "PedestrianRequested",
        False,
    )

    return server


async def main() -> None:
    server = await create_opcua_server()

    print("OPC UA Server started.")
    print("Port: 4840")
    print("Path: /traffic-light/")

    async with server:
        await traffic_cycle()


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("\nSystem stopped.")

    finally:
        red.off()
        yellow.off()
        green.off()

        red.close()
        yellow.close()
        green.close()
        touch.close()
