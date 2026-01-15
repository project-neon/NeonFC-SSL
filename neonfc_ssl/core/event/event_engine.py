from collections import defaultdict
from logging import getLogger
from multiprocessing import Queue

from .event_socket import EventSocket
from .event_parser import EventParser
from .event_definitions import EventError, EventType

SUBSCRIPTION_ADDED_MSG = "Subscription added for event type: {}"
EVENT_HANDLED_MSG = "Event handled: type={}, source={}, queues={}"
EVENT_PARSE_ERROR_MSG = "Failed to parse event: {}"
QUEUE_PUT_ERROR_MSG = "Error putting event type {} into queue: {}"


class EventEngine:
    def __init__(self, logger=None):
        self.sockets = []
        self.subscriptions = defaultdict(list)
        self.logger = logger if logger is not None else getLogger(__name__)

    def add_socket(self, event_socket):
        """Add a socket and set its callback to this engine's handler"""
        self.sockets.append(event_socket)
        event_socket.set_callback(self.socket_callback)

    def remove_socket(self, event_socket):
        """Remove a socket from the engine"""
        self.sockets.remove(event_socket)
        event_socket.set_callback(None)

    def subscribe(self, event_type, queue):
        """Subscribe a multiprocessing queue to a specific event type"""
        if queue not in self.subscriptions[event_type]:
            self.subscriptions[event_type].append(queue)
            self.logger.debug(SUBSCRIPTION_ADDED_MSG.format(event_type))

    def socket_callback(self, event):
        """Handle events received from socket (callback mode)"""
        try:
            parsed_event = EventParser.parse(event)
            self.handle_event(parsed_event)
        except EventError as e:
            self.logger.error(EVENT_PARSE_ERROR_MSG.format(e))
        except Exception as e:
            error_msg = EVENT_PARSE_ERROR_MSG.format(e)
            self.logger.error(error_msg)
            raise EventError(error_msg) from e

    def handle_event(self, parsed_event):
        """Put events into all queues subscribed to the event's type"""
        # EventParser.validate_json already ensures 'type' exists
        event_type = parsed_event.type
        event_source = parsed_event.source
        queues = self.subscriptions.get(event_type, [])

        self.logger.debug(EVENT_HANDLED_MSG.format(event_type, event_source, len(queues)))

        # Send to all queues, log errors but continue to other queues
        for queue in queues:
            try:
                queue.put(parsed_event)
            except Exception as e:
                self.logger.error(QUEUE_PUT_ERROR_MSG.format(event_type, e))

    def stop_all(self):
        """Stop all sockets"""
        for socket in self.sockets:
            socket.stop()
