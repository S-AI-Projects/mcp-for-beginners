import json
import sys


def process_stream(input_stream, output_stream, diagnostic_stream):
    """Parse one JSON message per line, keeping protocol and diagnostics separate."""
    for line_number, line in enumerate(input_stream, start=1):
        if not line.strip():
            continue

        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            result = {
                "ok": False,
                "error": {
                    "code": "PARSE_ERROR",
                    "line": line_number,
                },
            }
            print(
                f"Malformed JSON on line {line_number}: {exc.msg}",
                file=diagnostic_stream,
            )
        else:
            if not isinstance(message, dict):
                result = {
                    "ok": False,
                    "error": {
                        "code": "INVALID_MESSAGE",
                        "line": line_number,
                    },
                }
                print(
                    f"Expected a JSON object on line {line_number}",
                    file=diagnostic_stream,
                )
            else:
                result = {
                    "ok": True,
                    "message": message,
                }

        print(json.dumps(result, separators=(",", ":")), file=output_stream)


def main():
    process_stream(sys.stdin, sys.stdout, sys.stderr)


if __name__ == "__main__":
    main()