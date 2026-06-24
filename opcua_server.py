"""OPC UA server and TrafficLight information model."""

import asyncio
from dataclasses import dataclass
from typing import Optional

from asyncua import Server, ua, uamethod
from asyncua.common.node import Node

from config import (
    NAMESPACE_URI,
    OPCUA_SYNC_INTERVAL,
    SERVER_ENDPOINT,
    SERVER_NAME,
)
from controller import TrafficLightController
from models import TrafficLightConfiguration


@dataclass
class TrafficLightOpcUaNodes:
    current_color: Optional[Node] = None
    red_on: Optional[Node] = None
    yellow_on: Optional[Node] = None
    green_on: Optional[Node] = None

    mode: Optional[Node] = None
    mode_value: Optional[Node] = None
    touch_detected: Optional[Node] = None
    pedestrian_requested: Optional[Node] = None

    red_duration: Optional[Node] = None
    yellow_duration: Optional[Node] = None
    green_duration: Optional[Node] = None
    green_after_touch_duration: Optional[Node] = None


class TrafficLightOpcUaServer:
    """Publishes the controller state through OPC UA."""

    def __init__(
        self,
        controller: TrafficLightController,
    ) -> None:
        self.controller = controller
        self.server = Server()
        self.nodes = TrafficLightOpcUaNodes()

        self._shutdown_requested = False

    def request_shutdown(self) -> None:
        self._shutdown_requested = True

    @staticmethod
    def _require_node(
        node: Optional[Node],
        name: str,
    ) -> Node:
        if node is None:
            raise RuntimeError(
                f"{name} OPC UA node is not initialized."
            )

        return node

    @uamethod
    async def change_mode(
        self,
        parent: Node,
        new_mode: int,
    ) -> bool:
        del parent

        return self.controller.change_mode(
            int(new_mode)
        )

    @uamethod
    async def request_pedestrian_crossing(
        self,
        parent: Node,
    ) -> bool:
        del parent

        return self.controller.request_pedestrian_crossing(
            source="OPC_UA_CLIENT"
        )

    @uamethod
    async def reset_request(
        self,
        parent: Node,
    ) -> bool:
        del parent

        return self.controller.reset_pedestrian_request()

    async def initialize(self) -> None:
        await self.server.init()

        self.server.set_endpoint(SERVER_ENDPOINT)
        self.server.set_server_name(SERVER_NAME)

        namespace_index = (
            await self.server.register_namespace(
                NAMESPACE_URI
            )
        )

        await self._build_information_model(
            namespace_index
        )

    async def _build_information_model(
        self,
        namespace_index: int,
    ) -> None:
        traffic_light = (
            await self.server.nodes.objects.add_object(
                namespace_index,
                "TrafficLight",
            )
        )

        state_object = await traffic_light.add_object(
            namespace_index,
            "State",
        )

        operation_object = await traffic_light.add_object(
            namespace_index,
            "Operation",
        )

        configuration_object = await traffic_light.add_object(
            namespace_index,
            "Configuration",
        )

        state = self.controller.state
        configuration = self.controller.configuration

        self.nodes.current_color = (
            await state_object.add_variable(
                namespace_index,
                "CurrentColor",
                ua.Variant(
                    state.current_color,
                    ua.VariantType.String,
                ),
            )
        )

        self.nodes.red_on = await state_object.add_variable(
            namespace_index,
            "RedOn",
            ua.Variant(
                state.red_on,
                ua.VariantType.Boolean,
            ),
        )

        self.nodes.yellow_on = (
            await state_object.add_variable(
                namespace_index,
                "YellowOn",
                ua.Variant(
                    state.yellow_on,
                    ua.VariantType.Boolean,
                ),
            )
        )

        self.nodes.green_on = (
            await state_object.add_variable(
                namespace_index,
                "GreenOn",
                ua.Variant(
                    state.green_on,
                    ua.VariantType.Boolean,
                ),
            )
        )

        self.nodes.mode = (
            await operation_object.add_variable(
                namespace_index,
                "Mode",
                ua.Variant(
                    state.mode.name,
                    ua.VariantType.String,
                ),
            )
        )

        self.nodes.mode_value = (
            await operation_object.add_variable(
                namespace_index,
                "ModeValue",
                ua.Variant(
                    state.mode.value,
                    ua.VariantType.UInt16,
                ),
            )
        )

        self.nodes.touch_detected = (
            await operation_object.add_variable(
                namespace_index,
                "TouchDetected",
                ua.Variant(
                    state.touch_detected,
                    ua.VariantType.Boolean,
                ),
            )
        )

        self.nodes.pedestrian_requested = (
            await operation_object.add_variable(
                namespace_index,
                "PedestrianRequested",
                ua.Variant(
                    state.pedestrian_requested,
                    ua.VariantType.Boolean,
                ),
            )
        )

        self.nodes.red_duration = (
            await configuration_object.add_variable(
                namespace_index,
                "RedDuration",
                ua.Variant(
                    configuration.red_duration,
                    ua.VariantType.Double,
                ),
            )
        )

        self.nodes.yellow_duration = (
            await configuration_object.add_variable(
                namespace_index,
                "YellowDuration",
                ua.Variant(
                    configuration.yellow_duration,
                    ua.VariantType.Double,
                ),
            )
        )

        self.nodes.green_duration = (
            await configuration_object.add_variable(
                namespace_index,
                "GreenDuration",
                ua.Variant(
                    configuration.green_duration,
                    ua.VariantType.Double,
                ),
            )
        )

        self.nodes.green_after_touch_duration = (
            await configuration_object.add_variable(
                namespace_index,
                "GreenAfterTouchDuration",
                ua.Variant(
                    configuration.green_after_touch_duration,
                    ua.VariantType.Double,
                ),
            )
        )

        await self._require_node(
            self.nodes.red_duration,
            "RedDuration",
        ).set_writable()

        await self._require_node(
            self.nodes.yellow_duration,
            "YellowDuration",
        ).set_writable()

        await self._require_node(
            self.nodes.green_duration,
            "GreenDuration",
        ).set_writable()

        await self._require_node(
            self.nodes.green_after_touch_duration,
            "GreenAfterTouchDuration",
        ).set_writable()

        await traffic_light.add_method(
            namespace_index,
            "ChangeMode",
            self.change_mode,
            [ua.VariantType.UInt16],
            [ua.VariantType.Boolean],
        )

        await traffic_light.add_method(
            namespace_index,
            "RequestPedestrianCrossing",
            self.request_pedestrian_crossing,
            [],
            [ua.VariantType.Boolean],
        )

        await traffic_light.add_method(
            namespace_index,
            "ResetRequest",
            self.reset_request,
            [],
            [ua.VariantType.Boolean],
        )

    async def _publish_controller_state(self) -> None:
        state = self.controller.state

        await self._require_node(
            self.nodes.current_color,
            "CurrentColor",
        ).write_value(
            ua.Variant(
                state.current_color,
                ua.VariantType.String,
            )
        )

        await self._require_node(
            self.nodes.red_on,
            "RedOn",
        ).write_value(
            ua.Variant(
                state.red_on,
                ua.VariantType.Boolean,
            )
        )

        await self._require_node(
            self.nodes.yellow_on,
            "YellowOn",
        ).write_value(
            ua.Variant(
                state.yellow_on,
                ua.VariantType.Boolean,
            )
        )

        await self._require_node(
            self.nodes.green_on,
            "GreenOn",
        ).write_value(
            ua.Variant(
                state.green_on,
                ua.VariantType.Boolean,
            )
        )

        await self._require_node(
            self.nodes.mode,
            "Mode",
        ).write_value(
            ua.Variant(
                state.mode.name,
                ua.VariantType.String,
            )
        )

        await self._require_node(
            self.nodes.mode_value,
            "ModeValue",
        ).write_value(
            ua.Variant(
                state.mode.value,
                ua.VariantType.UInt16,
            )
        )

        await self._require_node(
            self.nodes.touch_detected,
            "TouchDetected",
        ).write_value(
            ua.Variant(
                state.touch_detected,
                ua.VariantType.Boolean,
            )
        )

        await self._require_node(
            self.nodes.pedestrian_requested,
            "PedestrianRequested",
        ).write_value(
            ua.Variant(
                state.pedestrian_requested,
                ua.VariantType.Boolean,
            )
        )

    async def _read_client_configuration(self) -> None:
        configuration = TrafficLightConfiguration(
            red_duration=float(
                await self._require_node(
                    self.nodes.red_duration,
                    "RedDuration",
                ).read_value()
            ),
            yellow_duration=float(
                await self._require_node(
                    self.nodes.yellow_duration,
                    "YellowDuration",
                ).read_value()
            ),
            green_duration=float(
                await self._require_node(
                    self.nodes.green_duration,
                    "GreenDuration",
                ).read_value()
            ),
            green_after_touch_duration=float(
                await self._require_node(
                    self.nodes.green_after_touch_duration,
                    "GreenAfterTouchDuration",
                ).read_value()
            ),
        )

        self.controller.update_configuration(
            configuration
        )

    async def _synchronize(self) -> None:
        while not self._shutdown_requested:
            await self._publish_controller_state()
            await self._read_client_configuration()

            await asyncio.sleep(OPCUA_SYNC_INTERVAL)

    async def run(self) -> None:
        await self.initialize()

        print("OPC UA server started")
        print(f"Endpoint: {SERVER_ENDPOINT}")

        async with self.server:
            await self._synchronize()
