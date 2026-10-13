"""Subprocess helpers shared by the scan engines' job managers (garak, PyRIT)."""

import subprocess


def kill_process_tree(pid: int) -> None:
    # /T walks the Windows parent-PID tree, which also reaches any child
    # processes the scan spawned (e.g. garak's multiprocessing.Pool workers).
    subprocess.run(
        ["taskkill", "/F", "/T", "/PID", str(pid)],
        capture_output=True,
        text=True,
    )  # ignore result: the process may have already exited on its own
