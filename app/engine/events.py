import os
import uuid

try:
    from kafka import KafkaConsumer, KafkaProducer
except ImportError:
    KafkaConsumer = None  # type: ignore[misc, assignment]
    KafkaProducer = None  # type: ignore[misc, assignment]

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TASK_COMPLETED_TOPIC = "task_completed"

_kafka_producer = None


def _get_producer():
    global _kafka_producer
    if KafkaProducer is None:
        return None
    if _kafka_producer is None:
        try:
            _kafka_producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP.split(","),
                request_timeout_ms=3000,
            )
        except Exception:
            return None
    return _kafka_producer


def send_task_completed_kafka(task_id: int) -> bool:
    producer = _get_producer()
    if producer is None:
        return False
    try:
        producer.send(
            TASK_COMPLETED_TOPIC,
            value=str(task_id).encode("utf-8"),
        )
        producer.flush(timeout=5)
        return True
    except Exception:
        return False


def create_choreo_consumer():
    if KafkaConsumer is None:
        return None
    try:
        consumer = KafkaConsumer(
            TASK_COMPLETED_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP.split(","),
            group_id=str(uuid.uuid4()),
            auto_offset_reset="latest",
            enable_auto_commit=True,
            consumer_timeout_ms=5000,
        )
        consumer.poll(0)
        for _ in range(50):
            if consumer.assignment():
                break
            consumer.poll(100)
        for partition in consumer.assignment():
            consumer.seek_to_end(partition)
        return consumer
    except Exception:
        return None


class EventBus:
    """Simple in-memory publish/subscribe event bus.

    Used by the choreography engine to chain task execution reactively.
    Each active workflow run registers its own ``task_completed:{run_id}``
    channel so runs are fully isolated from one another.
    """

    def __init__(self) -> None:
        self.subscribers: dict[str, list] = {}
        self.log_event = None

    def subscribe(self, event_name: str, handler) -> None:
        """Register *handler* to be called when *event_name* is published."""
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []
        self.subscribers[event_name].append(handler)

    def publish(self, event_name: str, data) -> None:
        """Invoke all handlers registered under *event_name* with *data*."""
        handlers = self.subscribers.get(event_name, [])
        if handlers:
            if self.log_event:
                self.log_event(
                    f"EVENT BUS: publishing '{event_name}' with data={data}"
                )
        for handler in handlers:
            handler(data)


event_bus = EventBus()

