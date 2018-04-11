import types
import uuid
import uqbar.strings
from patterns_testbase import TestCase
import supriya.patterns
import supriya.realtime


class TestCase(TestCase):

    def test__perform_realtime_01(self):
        node_uuid = uuid.uuid4()
        event = supriya.patterns.GroupEvent(
            uuid=node_uuid,
            )
        server = types.SimpleNamespace(
            node_id_allocator=supriya.realtime.NodeIdAllocator(),
            )
        uuids = {}
        event_products = event._perform_realtime(
            server=server,
            timestamp=100.0,
            uuids=uuids,
            )
        assert self.get_objects_as_string(
            event_products,
            replace_uuids=True,
        ) == uqbar.strings.normalize('''
            EventProduct(
                event=GroupEvent(
                    uuid=UUID('A'),
                    ),
                requests=[
                    GroupNewRequest(
                        add_action=AddAction.ADD_TO_HEAD,
                        node_id=1000,
                        target_node_id=1,
                        ),
                    ],
                timestamp=100.0,
                uuid=UUID('A'),
                )
            ''')
        assert node_uuid in uuids
        assert isinstance(uuids[node_uuid], dict)
        assert list(uuids[node_uuid].keys()) == [1000]

    def test__perform_realtime_02(self):
        node_uuid = uuid.uuid4()
        event = supriya.patterns.GroupEvent(
            is_stop=True,
            uuid=node_uuid,
            )
        server = types.SimpleNamespace(
            node_id_allocator=supriya.realtime.NodeIdAllocator(),
            )
        uuids = {
            node_uuid: {
                1000: supriya.realtime.Group(),
                },
            }
        event_products = event._perform_realtime(
            server=server,
            timestamp=100.0,
            uuids=uuids,
            )
        assert self.get_objects_as_string(
            event_products,
            replace_uuids=True,
        ) == uqbar.strings.normalize('''
            EventProduct(
                event=GroupEvent(
                    is_stop=True,
                    uuid=UUID('A'),
                    ),
                is_stop=True,
                requests=[
                    NodeFreeRequest(
                        node_ids=(1000,),
                        ),
                    ],
                timestamp=100.0,
                uuid=UUID('A'),
                )
            ''')