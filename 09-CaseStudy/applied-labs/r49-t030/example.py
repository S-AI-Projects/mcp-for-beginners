"""
Local Tool Contract Fixture with Applied Questions and Executable Checks.
Extends 09-CaseStudy/README.md.

Demonstrates allowlist tool dispatch, numeric argument validation, failure
isolation, and three applied questions covering output prediction, failure
diagnosis, and boundary policy decisions.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class AppliedQuestion:
    """Represents an applied question with factual answer, rationale, and check."""
    question_id: str
    category: str  # "predict_output", "diagnose_failure", "choose_boundary_policy"
    prompt: str
    factual_answer: Any
    rationale: str


class LocalContractDispatcher:
    """
    Local JSON tool dispatcher implementing allowlist routing, numeric
    argument validation, and strict execution isolation.
    """

    def __init__(self) -> None:
        self.allowlist: Dict[str, Callable[[float, float], float]] = {
            "add": self._add_handler,
            "multiply": self._multiply_handler,
        }
        self.execution_counts: Dict[str, int] = {
            "add": 0,
            "multiply": 0,
        }

    def _add_handler(self, a: float, b: float) -> float:
        self.execution_counts["add"] += 1
        return a + b

    def _multiply_handler(self, a: float, b: float) -> float:
        self.execution_counts["multiply"] += 1
        return a * b

    def dispatch(self, call_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatches a local JSON call payload through validation and allowlist routing.

        Payload schema:
        {
            "tool": str,
            "arguments": {"a": number, "b": number}
        }
        """
        if not isinstance(call_payload, dict):
            return {
                "status": "error",
                "error": {
                    "code": "INVALID_PAYLOAD",
                    "message": f"Payload must be a dictionary, got {type(call_payload).__name__}",
                },
            }

        tool_name = call_payload.get("tool")
        if not tool_name or tool_name not in self.allowlist:
            return {
                "status": "error",
                "error": {
                    "code": "UNKNOWN_TOOL",
                    "message": f"Tool '{tool_name}' is not in allowlist: {sorted(self.allowlist.keys())}",
                },
            }

        args = call_payload.get("arguments")
        if not isinstance(args, dict):
            return {
                "status": "error",
                "error": {
                    "code": "INVALID_ARGUMENT_STRUCTURE",
                    "message": f"Arguments must be a dictionary, got {type(args).__name__}",
                },
            }

        # Check required fields
        for param in ("a", "b"):
            if param not in args:
                return {
                    "status": "error",
                    "error": {
                        "code": "MISSING_ARGUMENT",
                        "message": f"Missing required parameter '{param}'",
                    },
                }

        # Numeric schema validation (strictly excluding booleans)
        for param in ("a", "b"):
            val = args[param]
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                return {
                    "status": "error",
                    "error": {
                        "code": "INVALID_ARGUMENT",
                        "parameter": param,
                        "message": (
                            f"Argument '{param}' must be a number (int or float), "
                            f"got {type(val).__name__}: {val!r}"
                        ),
                    },
                }

        # Safe execution through allowlist handler
        handler = self.allowlist[tool_name]
        result = handler(args["a"], args["b"])
        return {
            "status": "success",
            "result": result,
        }


def get_applied_questions() -> List[AppliedQuestion]:
    """Returns the three curriculum applied questions with answers and rationales."""
    return [
        AppliedQuestion(
            question_id="Q1_PREDICT_OUTPUT",
            category="predict_output",
            prompt="Predict the status and result when dispatching: {'tool': 'multiply', 'arguments': {'a': 2.5, 'b': 4}}.",
            factual_answer={
                "status": "success",
                "result": 10.0,
            },
            rationale=(
                "The tool 'multiply' is in the allowlist. Arguments a=2.5 (float) and b=4 (int) "
                "pass numeric validation. The multiplication handler computes 2.5 * 4 = 10.0."
            ),
        ),
        AppliedQuestion(
            question_id="Q2_DIAGNOSE_FAILURE",
            category="diagnose_failure",
            prompt=(
                "Diagnose the failure when dispatching: {'tool': 'add', 'arguments': {'a': '2', 'b': 3}}. "
                "What is the structured error code, and did any tool handler execute?"
            ),
            factual_answer={
                "code": "INVALID_ARGUMENT",
                "parameter": "a",
                "handler_invoked": False,
            },
            rationale=(
                "Argument 'a' has value '2' of type string. Numeric validation fails before "
                "handler dispatch. The system returns error code 'INVALID_ARGUMENT' and does not invoke "
                "the 'add' handler, keeping execution counts at zero."
            ),
        ),
        AppliedQuestion(
            question_id="Q3_BOUNDARY_POLICY",
            category="choose_boundary_policy",
            prompt=(
                "Choose a boundary policy for boolean inputs like {'tool': 'add', 'arguments': {'a': True, 'b': 3}}. "
                "Should booleans be coerced to integers (True=1) or strictly rejected?"
            ),
            factual_answer={
                "policy": "STRICT_REJECT_BOOLEANS",
                "decision": "REJECT",
                "error_code": "INVALID_ARGUMENT",
            },
            rationale=(
                "In Python, bool is a subclass of int (isinstance(True, int) is True). However, in JSON "
                "and MCP protocols, booleans and numbers are separate primitive types. Coercing booleans "
                "to numbers causes silent semantic corruption in tool arguments. Strict rejection enforces "
                "cross-language protocol integrity."
            ),
        ),
    ]


def verify_question_1(dispatcher: LocalContractDispatcher, q: AppliedQuestion) -> bool:
    """Executable check for Question 1: Output prediction."""
    payload = {"tool": "multiply", "arguments": {"a": 2.5, "b": 4}}
    actual = dispatcher.dispatch(payload)
    return actual == q.factual_answer


def verify_question_2(dispatcher: LocalContractDispatcher, q: AppliedQuestion) -> bool:
    """Executable check for Question 2: Failure diagnosis and isolation."""
    counts_before = dict(dispatcher.execution_counts)
    payload = {"tool": "add", "arguments": {"a": "2", "b": 3}}
    actual = dispatcher.dispatch(payload)

    err = actual.get("error", {})
    code_match = err.get("code") == q.factual_answer["code"]
    param_match = err.get("parameter") == q.factual_answer["parameter"]
    counts_unchanged = (dispatcher.execution_counts == counts_before)

    return code_match and param_match and counts_unchanged


def verify_question_3(dispatcher: LocalContractDispatcher, q: AppliedQuestion) -> bool:
    """Executable check for Question 3: Boundary policy choice."""
    payload = {"tool": "add", "arguments": {"a": True, "b": 3}}
    actual = dispatcher.dispatch(payload)

    err = actual.get("error", {})
    rejected = actual.get("status") == "error"
    code_match = err.get("code") == q.factual_answer["error_code"]

    return rejected and code_match
