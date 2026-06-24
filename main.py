"""Smart Factory Traffic Light application entry point."""

import asyncio
import signal

from controller import TrafficLightController
from hardware import TrafficLightHardware
from opcua_server import TrafficLightOpcUaServer


async def main() -> None:
    hardware = TrafficLightHardware()
    controller = TrafficLightController(hardware)
    opcua_server = TrafficLightOpcUaServer(controller)

    loop = asyncio.get_running_loop()

    def request_shutdown() -> None:
        print("Shutdown requested")

        controller.request_shutdown()
        opcua_server.request_shutdown()

    for signal_name in (
        signal.SIGINT,
        signal.SIGTERM,
    ):
        loop.add_signal_handler(
            signal_name,
            request_shutdown,
        )

    controller_task = asyncio.create_task(
        controller.run(),
        name="traffic-controller",
    )

    opcua_task = asyncio.create_task(
        opcua_server.run(),
        name="opcua-server",
    )

    print("Smart Factory Traffic Light started")

    try:
        await asyncio.gather(
            controller_task,
            opcua_task,
        )

    finally:
        controller.request_shutdown()
        opcua_server.request_shutdown()

        for task in (
            controller_task,
            opcua_task,
        ):
            if not task.done():
                task.cancel()

        await asyncio.gather(
            controller_task,
            opcua_task,
            return_exceptions=True,
        )

        hardware.close()
        print("Smart Factory Traffic Light stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
