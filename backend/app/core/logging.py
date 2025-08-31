import json, logging, sys, time, uuid

class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "ts": int(time.time()*1000),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "component": getattr(record, "component", "api"),
            "version": getattr(record, "version", "0.1.0"),
            "request_id": getattr(record, "request_id", None),
            "correlation_id": getattr(record, "correlation_id", None),
            "user_id": getattr(record, "user_id", None),
            "span_id": getattr(record, "span_id", str(uuid.uuid4())[:8]),
        }
        return json.dumps(payload, ensure_ascii=False)

def setup_logging():
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [h]
