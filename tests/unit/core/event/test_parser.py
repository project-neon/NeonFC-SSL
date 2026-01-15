import pytest
import json
from datetime import datetime

from neonfc_ssl.core.event import EventParser
from neonfc_ssl.core.event import EventError, EventType


@pytest.mark.unit
class TestEventParser:
    """Test cases for EventParser"""

    def test_parse_valid_json(self):
        """Test parsing valid JSON event data"""
        event_data = json.dumps({
            'type': 'MasterState',
            'source': 'sensor1',
            'sent_time_stamp': '2024-01-15T10:30:45.123Z'
        }).encode('utf-8')

        result = EventParser.parse(event_data)

        assert result.type == EventType.MASTER_STATE
        assert result.source == 'sensor1'
        assert result.sent_time_stamp == datetime.fromisoformat('2024-01-15T10:30:45.123')
        assert result.event_data is None

    def test_parse_with_event_data(self):
        """Test parsing event with event_data field"""
        event_data = json.dumps({
            'type': 'MasterState',
            'source': 'sensor2',
            'sent_time_stamp': '2024-01-15T10:30:45.123',
            'event_data': {'value': 100.5}
        }).encode('utf-8')

        result = EventParser.parse(event_data)

        assert result.event_data == {'value': 100.5}

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON raises EventError"""
        invalid_data = b'not valid json'

        with pytest.raises(EventError, match='Failed to parse event data'):
            EventParser.parse(invalid_data)

    def test_parse_missing_type_field(self):
        """Test parsing event missing 'type' field raises EventError"""
        event_data = json.dumps({
            'source': 'sensor1',
            'sent_time_stamp': '2024-01-15T10:30:45.123Z'
        }).encode('utf-8')

        with pytest.raises(EventError, match="missing 'type' field"):
            EventParser.parse(event_data)

    def test_parse_missing_source_field(self):
        """Test parsing event missing 'source' field raises EventError"""
        event_data = json.dumps({
            'type': 'MasterState',
            'sent_time_stamp': '2024-01-15T10:30:45.123Z'
        }).encode('utf-8')

        with pytest.raises(EventError, match="missing 'source' field"):
            EventParser.parse(event_data)

    def test_parse_missing_timestamp_field(self):
        """Test parsing event missing 'sent_time_stamp' field raises EventError"""
        event_data = json.dumps({
            'type': 'MasterState',
            'source': 'sensor1'
        }).encode('utf-8')

        with pytest.raises(EventError, match="missing 'sent_time_stamp' field"):
            EventParser.parse(event_data)

    def test_parse_unknown_event_type(self):
        """Test parsing event with unknown type raises EventError"""
        event_data = json.dumps({
            'type': 'UNKNOWN_TYPE',
            'source': 'sensor1',
            'sent_time_stamp': '2024-01-15T10:30:45.123Z'
        }).encode('utf-8')

        with pytest.raises(EventError, match='Unknown event type'):
            EventParser.parse(event_data)
