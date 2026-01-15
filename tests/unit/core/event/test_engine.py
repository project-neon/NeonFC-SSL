import pytest
from unittest.mock import Mock, patch
from multiprocessing import Queue
from datetime import datetime

from neonfc_ssl.core.event import EventParser
from neonfc_ssl.core.event import EventEngine
from neonfc_ssl.core.event import EventError, EventType, Event


@pytest.mark.unit
class TestEventEngine:
    """Test cases for EventEngine"""

    @pytest.fixture
    def logger(self):
        """Create mock logger"""
        return Mock()

    @pytest.fixture
    def engine(self, logger):
        """Create EventEngine instance"""
        return EventEngine(logger=logger)

    def test_subscribe(self, engine):
        """Test subscribing queue to event type"""
        test_queue = Queue()

        engine.subscribe(EventType.MASTER_STATE, test_queue)

        assert test_queue in engine.subscriptions[EventType.MASTER_STATE]

    def test_subscribe_same_queue_twice(self, engine):
        """Test subscribing same queue twice doesn't duplicate"""
        test_queue = Queue()

        engine.subscribe(EventType.MASTER_STATE, test_queue)
        engine.subscribe(EventType.MASTER_STATE, test_queue)

        assert len(engine.subscriptions[EventType.MASTER_STATE]) == 1

    def test_subscribe_multiple_queues(self, engine):
        """Test subscribing multiple queues to same event type"""
        queue1 = Queue()
        queue2 = Queue()

        engine.subscribe(EventType.MASTER_STATE, queue1)
        engine.subscribe(EventType.MASTER_STATE, queue2)

        assert len(engine.subscriptions[EventType.MASTER_STATE]) == 2

    @patch.object(EventParser, 'parse')
    def test_handle_event_multiple_queues(self, mock_parse, engine):
        """Test handle_event puts event into all subscribed queues"""
        queue1 = Queue()
        queue2 = Queue()
        parsed_event = Event(
            type=EventType.MASTER_STATE,
            source='sensor1',
            sent_time_stamp=datetime.fromisoformat('2024-01-15T10:30:45.123'),
            event_data=None
        )
        mock_parse.return_value = parsed_event

        engine.subscribe(EventType.MASTER_STATE, queue1)
        engine.subscribe(EventType.MASTER_STATE, queue2)
        engine.handle_event(parsed_event)

        assert queue1.get(timeout=1.0) == parsed_event
        assert queue2.get(timeout=1.0) == parsed_event

    def test_handle_event_no_subscribers(self, engine):
        """Test handle_event with no subscribers doesn't raise error"""
        parsed_event = Event(
            type=EventType.MASTER_STATE,
            source='sensor1',
            sent_time_stamp=datetime.fromisoformat('2024-01-15T10:30:45.123'),
            event_data=None
        )
        # Should not raise exception
        engine.handle_event(parsed_event)

    @patch.object(EventParser, 'parse')
    def test_socket_callback_parses_and_handles(self, mock_parse, engine):
        """Test socket_callback parses event and calls handle_event"""
        test_queue = Queue()
        raw_event = b'raw event data'
        parsed_event = Event(
            type=EventType.MASTER_STATE,
            source='sensor1',
            sent_time_stamp=datetime.fromisoformat('2024-01-15T10:30:45.123'),
            event_data=None
        )
        mock_parse.return_value = parsed_event

        engine.subscribe(EventType.MASTER_STATE, test_queue)
        engine.socket_callback(raw_event)

        mock_parse.assert_called_once_with(raw_event)
        assert test_queue.get(timeout=1.0)

    @patch.object(EventParser, 'parse')
    def test_socket_callback_handles_parse_error(self, mock_parse, engine):
        """Test socket_callback handles EventError from parser"""
        mock_parse.side_effect = EventError("Parse failed")

        # Should not raise exception, just log it
        engine.socket_callback(b'bad data')
