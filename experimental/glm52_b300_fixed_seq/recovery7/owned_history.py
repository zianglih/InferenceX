"""Birth-bound Linux child ownership; imported without reading /proc or spawning.

Private successor of frozen owned.py. Separate task and historical limits;
identity revisions omit scheduler state. Birth/group/cleanup rules are unchanged.
"""

import os
from pathlib import Path
import signal
import subprocess
import time

MAX_TASKS = 1024
CASE_HISTORY = 4096
CAMPAIGN_HISTORY = 65536


def identity(value):
    return tuple(value[k] for k in ("pid", "starttime", "ppid", "pgid", "sid"))


def proc_info(pid):
    raw = Path(f"/proc/{pid}/stat").read_text()
    fields = raw.rsplit(")", 1)[1].split()
    return {
        "pid": pid,
        "state": fields[0],
        "ppid": int(fields[1]),
        "pgid": int(fields[2]),
        "sid": int(fields[3]),
        "starttime": int(fields[19]),
    }


def same(now, birth):
    return (
        now is not None
        and now["pid"] == birth["pid"]
        and now["starttime"] == birth["starttime"]
    )


class Owned:
    def __init__(
        self, proc, label, persist, read=proc_info, history_limit=CASE_HISTORY
    ):
        # Registration precedes all fallible birth/receipt work.
        self.proc, self.label, self.persist, self.read = proc, label, persist, read
        self.known, self.birth, self.errors = {}, None, []
        self.history_limit, self.identity_revision = history_limit, 0
        self.frontier = (
            set()
        )  # Retire only traversal, never retained identity evidence.

    def existing(self, pid):
        try:
            return self.read(pid)
        except (FileNotFoundError, ProcessLookupError):
            return None

    def identify(self):
        current = self.read(self.proc.pid)
        if current["ppid"] != os.getpid():
            raise ValueError("New process is not this supervisor child")
        self.birth = current
        self.known[current["pid"]] = current
        self.frontier.add(current["pid"])
        self.identity_revision += 1
        self.persist(self)

    def refresh(self):
        pending = [self.known[pid] for pid in self.frontier]
        seen = set()
        while pending:
            prior = pending.pop()
            if prior["pid"] in seen:
                continue
            seen.add(prior["pid"])
            current = self.existing(prior["pid"])
            if not same(current, prior) or current["state"] == "Z":
                self.frontier.discard(prior["pid"])
                continue
            tasks = Path(f"/proc/{prior['pid']}/task")
            try:
                tids = list(tasks.iterdir())
            except FileNotFoundError:
                continue
            if len(tids) > MAX_TASKS:
                raise ValueError("Owned task count exceeds bound")
            for tid in tids:
                try:
                    raw = (tid / "children").read_text()
                except FileNotFoundError:
                    continue
                if len(raw) > 32768:
                    raise ValueError("Owned children list exceeds bound")
                for child_pid in map(int, raw.split()):
                    child = self.existing(child_pid)
                    if child is None:
                        continue
                    if child["ppid"] != prior["pid"]:
                        continue
                    if child_pid in self.known and not same(
                        child, self.known[child_pid]
                    ):
                        raise ValueError("Known child PID reused")
                    prior_child = self.known.get(child_pid)
                    if prior_child is None or identity(child) != identity(prior_child):
                        self.identity_revision += 1
                    self.known[child_pid] = child
                    self.frontier.add(child_pid)
                    pending.append(child)
                    if len(self.known) > self.history_limit:
                        raise ValueError("Owned retained history exceeds bound")
        self.persist(self)

    def bind_rank(self, owner):
        self.refresh()
        current = self.existing(owner["pid"])
        known = self.known.get(owner["pid"])
        if (
            known is None
            or not same(current, known)
            or not same(current, owner)
            or current["state"] == "Z"
        ):
            raise ValueError("Native rank is not a retained live descendant")
        return {"pid": current["pid"], "starttime": current["starttime"]}

    def live(self):
        result = []
        for prior in self.known.values():
            current = self.existing(prior["pid"])
            if same(current, prior) and current["state"] != "Z":
                result.append(current)
        return result

    def signal_owned(self, sig):
        living = self.live()
        # Never signal a reused/unproven group after its leader is gone.
        if any(
            x["pgid"] == self.proc.pid and x["sid"] == self.proc.pid for x in living
        ):
            try:
                os.killpg(self.proc.pid, sig)
            except ProcessLookupError:
                pass
        for item in living:
            current = self.existing(item["pid"])
            if same(current, item) and current["state"] != "Z":
                try:
                    os.kill(item["pid"], sig)
                except ProcessLookupError:
                    pass

    def cleanup(self, term=30, kill=10):
        try:
            self.refresh()
        except BaseException as error:
            self.errors.append("refresh: " + repr(error))
        if self.birth is None:
            # An unreaped Popen child cannot have its PID reused. Kill only that
            # directly owned child, not an unproven process group. Missing birth
            # means descendants cannot be certified and cleanup remains pending.
            self.errors.append("Missing birth: descendant completeness unproven")
            for sig, delay in ((signal.SIGTERM, term), (signal.SIGKILL, kill)):
                if self.proc.poll() is None:
                    self.proc.send_signal(sig)
                try:
                    self.proc.wait(timeout=delay)
                except subprocess.TimeoutExpired:
                    pass
        else:
            for sig, delay in ((signal.SIGTERM, term), (signal.SIGKILL, kill)):
                try:
                    self.signal_owned(sig)
                except BaseException as error:
                    self.errors.append("signal: " + repr(error))
                end = time.monotonic() + delay
                while self.live() and time.monotonic() < end:
                    time.sleep(0.1)
                try:
                    self.proc.wait(timeout=max(0.01, end - time.monotonic()))
                except subprocess.TimeoutExpired:
                    pass
        remaining = self.live()
        return {
            "label": self.label,
            "leader_pid": self.proc.pid,
            "birth": self.birth,
            "returncode": self.proc.poll(),
            "remaining": remaining,
            "errors": self.errors,
            "cleanup_pending": bool(
                remaining or self.errors or self.proc.poll() is None
            ),
        }


class Registry:
    def __init__(
        self,
        persist,
        popen=subprocess.Popen,
        read=proc_info,
        history_limit=CASE_HISTORY,
    ):
        self.persist, self.popen, self.read, self.children = persist, popen, read, []
        self.history_limit = history_limit

    def persist_checked(self, child):
        if sum(len(item.known) for item in self.children) > self.history_limit:
            raise ValueError("Registry retained history exceeds bound")
        self.persist(child)

    def spawn(self, argv, *, env, output, label, new_session=False):
        proc = self.popen(
            argv,
            env=env,
            stdout=output,
            stderr=subprocess.STDOUT,
            start_new_session=new_session,
        )
        child = Owned(proc, label, self.persist_checked, self.read, self.history_limit)
        self.children.append(child)  # Popen success is owned before birth/IO.
        try:
            child.identify()
            return child
        except BaseException:
            # The outer registry still retains this child if cleanup also fails.
            child.cleanup()
            raise

    def refresh(self):
        for child in self.children:
            child.refresh()

    def cleanup(self):
        receipts = []
        for child in reversed(self.children):
            try:
                receipts.append(child.cleanup())
            except BaseException as error:
                receipts.append(
                    {
                        "label": child.label,
                        "leader_pid": child.proc.pid,
                        "cleanup_pending": True,
                        "error": repr(error),
                    }
                )
        return receipts
