# CodePilot demo workspace

This directory is the default workspace root. The `read_file` Tool can read
only paths below this directory, such as `demo/hello.py`.

`calculator.py` and `test_calculator.py` are the V3 review example. `add()`
intentionally contains a one-character operator bug. The intended V3 flow is:

```text
search/read or run test
→ propose_patch (does not write)
→ human POST approval
→ run_tests
```

The initial test is supposed to fail. After approving the proposal it passes.
