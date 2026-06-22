import asyncio

from asyncua import Server


async def main() -> None:
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

    current_state = await traffic_light.add_variable(
        namespace_index,
        "CurrentState",
        "RED",
    )

    red_on = await traffic_light.add_variable(
        namespace_index,
        "RedOn",
        True,
    )

    yellow_on = await traffic_light.add_variable(
        namespace_index,
        "YellowOn",
        False,
    )

    green_on = await traffic_light.add_variable(
        namespace_index,
        "GreenOn",
        False,
    )

    touch_detected = await traffic_light.add_variable(
        namespace_index,
        "TouchDetected",
        False,
    )

    pedestrian_requested = await traffic_light.add_variable(
        namespace_index,
        "PedestrianRequested",
        False,
    )

    print("OPC UA Server started.")
    print("Endpoint: opc.tcp://0.0.0.0:4840/traffic-light/")

    async with server:
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
