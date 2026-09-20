from datetime import datetime
import json
from typing import Dict, Any

from .event_definitions import EventType, EventError, Event

PARSE_ERROR_MSG = "Failed to parse event data: {}"
MISSING_FIELD_MSG = "Event data missing '{}' field: {}"
UNKNOWN_EVENT_TYPE_MSG = "Unknown event type: {}"
INVALID_TIMESTAMP_MSG = "Invalid timestamp format: {}"


class EventParser:
    """Parser for converting raw event data to Event objects"""

    REQUIRED_FIELDS = ['type', 'source', 'sent_time_stamp']

    @classmethod
    def parse(cls, event_data: bytes) -> list[Event]:
        """
        Parse raw event data into a list of Event objects.
        event_data may contain one or more concatenated JSON objects.

        Args:
            event_data: Raw bytes containing one or more JSON events

        Returns:
            List[Event]: Parsed and validated Event objects

        Raises:
            EventError: If parsing or validation fails
        """
        json_strings, remainder = cls._extract_json_objects(event_data.decode('utf-8'))

        if remainder.strip():
            # leftover bytes that don't form a complete JSON object
            raise EventError(PARSE_ERROR_MSG.format(f"Incomplete JSON data: {remainder!r}"))

        events = []
        for json_str in json_strings:
            raw_dict = cls._parse_json(json_str)
            cls._validate_required_fields(raw_dict)
            events.append(cls._build_event(raw_dict))

        return events

    @staticmethod
    def _parse_json(event_data: str) -> Dict[str, Any]:
        """Parse JSON string into a dictionary"""
        try:
            return json.loads(event_data)
        except json.JSONDecodeError as e:
            raise EventError(PARSE_ERROR_MSG.format(e)) from e

    @staticmethod
    def _extract_json_objects(buffer: str):
        """
        Pull as many complete JSON objects as possible out of buffer.
        Returns (list_of_json_strings, remaining_buffer).
        """
        decoder = json.JSONDecoder()
        objects = []
        buffer = buffer.lstrip()

        while buffer:
            try:
                obj, idx = decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                break  # incomplete object at the end, wait for more bytes

            objects.append(buffer[:idx])
            buffer = buffer[idx:].lstrip()

        return objects, buffer

    @classmethod
    def _validate_required_fields(cls, event_dict: Dict[str, Any]) -> None:
        """Validate that all required fields are present"""
        for field in cls.REQUIRED_FIELDS:
            if field not in event_dict:
                raise EventError(MISSING_FIELD_MSG.format(field, event_dict))

    @classmethod
    def _build_event(cls, event_dict: Dict[str, Any]) -> Event:
        """Build an Event object from validated dictionary"""
        event_type = cls._parse_event_type(event_dict['type'])
        timestamp = cls._parse_timestamp(event_dict['sent_time_stamp'])

        return Event(
            type=event_type,
            source=event_dict['source'],
            sent_time_stamp=timestamp,
            event_data=event_dict.get('event_data')
        )

    @staticmethod
    def _parse_event_type(type_value: str) -> EventType:
        """Convert string to EventType enum"""
        try:
            return EventType(type_value)
        except ValueError as e:
            raise EventError(UNKNOWN_EVENT_TYPE_MSG.format(type_value)) from e

    @staticmethod
    def _parse_timestamp(timestamp_value: str) -> datetime:
        """
        Convert ISO 8601 timestamp string to datetime object.
        Expected format: "YYYY-MM-DDTHH:mm:ss.sssZ"
        """
        if not isinstance(timestamp_value, str):
            raise EventError(INVALID_TIMESTAMP_MSG.format(f"Expected string, got {type(timestamp_value).__name__}"))

        try:
            # Remove 'Z' suffix and parse
            # Python's fromisoformat doesn't handle 'Z', so we strip it
            timestamp_str = timestamp_value.rstrip('Z')
            return datetime.fromisoformat(timestamp_str)
        except ValueError as e:
            raise EventError(INVALID_TIMESTAMP_MSG.format(timestamp_value)) from e