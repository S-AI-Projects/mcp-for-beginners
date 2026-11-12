from pathlib import Path
import sys

folder = Path(__file__).parent
expected = (folder / "expected-results.txt").read_text()
actual = (folder / "actual-results.txt").read_text()

if expected != actual:
    print("FAIL: output mismatch")
    sys.exit(1)

wrong_expected = expected + '{"wrong":true}\n'

if wrong_expected == actual:
    print("FAIL: wrong expectation accepted")
    sys.exit(1)

print("PASS: output matches expected")
print("PASS: deliberately wrong expectation rejected")