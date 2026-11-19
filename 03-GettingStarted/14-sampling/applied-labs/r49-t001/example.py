
class ConsentGate:
    def __init__(self):
        self.state = "pending"
        self.model_call_count = 0
        self.result = None

    def _call_model(self):
        self.model_call_count += 1
        return "Mock model response"

    def decide(self, decision):
        if self.state != "pending":
            raise ValueError("Request already completed")

        if decision == "approved":
            self.result = self._call_model()
            self.state = "approved"

        elif decision == "denied":
            self.state = "denied"

        else:
            raise ValueError("Invalid decision")


if __name__ == "__main__":
    gate = ConsentGate()

    decision = input("Approve or deny the request? ").strip().lower()

    try:
        gate.decide(decision)
    except ValueError as error:
        print("Error:", error)

    print("Final state:", gate.state)
    print("Model calls:", gate.model_call_count)
    print("Result:", gate.result)
