"""Unit tests for backend.app.core.logging."""

import io
import json
import logging
import unittest

from backend.app.core.logging import (
    JSONFormatter,
    get_logger,
    get_request_id,
    get_workflow_id,
    log_context,
    set_request_id,
    set_workflow_id,
    setup_logging,
)


class TestLogging(unittest.TestCase):
    """Test suite for structured JSON logging and context propagation."""

    def setUp(self):
        # Reset context variables before each test
        set_request_id(None)
        set_workflow_id(None)

    def test_json_formatter_default_fields(self):
        """Log record formats as JSON with request_id and workflow_id null when unset."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=20,
            msg="Hello, world!",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        data = json.loads(formatted)

        self.assertEqual(data["level"], "INFO")
        self.assertEqual(data["logger"], "test_logger")
        self.assertEqual(data["message"], "Hello, world!")
        self.assertIsNone(data["request_id"])
        self.assertIsNone(data["workflow_id"])
        self.assertIn("timestamp", data)
        self.assertTrue(data["timestamp"].endswith("Z"))

    def test_log_context_manager(self):
        """log_context sets request_id and workflow_id within block and resets on exit."""
        self.assertIsNone(get_request_id())
        self.assertIsNone(get_workflow_id())

        with log_context(request_id="req-abc", workflow_id="wf-123"):
            self.assertEqual(get_request_id(), "req-abc")
            self.assertEqual(get_workflow_id(), "wf-123")

            formatter = JSONFormatter()
            record = logging.LogRecord(
                name="test_logger",
                level=logging.WARNING,
                pathname=__file__,
                lineno=45,
                msg="Context test",
                args=(),
                exc_info=None,
            )
            data = json.loads(formatter.format(record))
            self.assertEqual(data["request_id"], "req-abc")
            self.assertEqual(data["workflow_id"], "wf-123")

            # Nested context overrides and restores
            with log_context(workflow_id="wf-inner"):
                self.assertEqual(get_request_id(), "req-abc")
                self.assertEqual(get_workflow_id(), "wf-inner")

            self.assertEqual(get_workflow_id(), "wf-123")

        # Context exited
        self.assertIsNone(get_request_id())
        self.assertIsNone(get_workflow_id())

    def test_extra_fields_merged_in_json(self):
        """Custom extra keys passed to logging are merged into the JSON payload."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=60,
            msg="Action taken",
            args=(),
            exc_info=None,
        )
        record.ticket_id = "CD-1002"
        record.action = "refund_requested"

        data = json.loads(formatter.format(record))
        self.assertEqual(data["ticket_id"], "CD-1002")
        self.assertEqual(data["action"], "refund_requested")

    def test_exception_included_in_json(self):
        """Exception traceback is formatted and included under 'exception' key."""
        formatter = JSONFormatter()
        try:
            raise ValueError("Something broke")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname=__file__,
            lineno=80,
            msg="Failure occurred",
            args=(),
            exc_info=exc_info,
        )

        data = json.loads(formatter.format(record))
        self.assertIn("exception", data)
        self.assertIn("ValueError: Something broke", data["exception"])

    def test_setup_logging_integration(self):
        """setup_logging configures root logger to output JSON to stdout."""
        setup_logging("DEBUG")
        logger = get_logger("clouddesk.test")

        # Capture output using a custom StreamHandler with JSONFormatter
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

        with log_context(request_id="req-live-999"):
            logger.info("Live test message")

        logger.removeHandler(handler)
        output = stream.getvalue().strip()
        data = json.loads(output)

        self.assertEqual(data["message"], "Live test message")
        self.assertEqual(data["request_id"], "req-live-999")
        self.assertIsNone(data["workflow_id"])


if __name__ == "__main__":
    unittest.main()

