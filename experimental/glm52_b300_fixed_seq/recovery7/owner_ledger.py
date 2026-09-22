"""Sparse birth-identity receipts; ordinary state-only polls produce no writes.

Case receipts retain the accepted complete-snapshot schema. Campaign receipts
use a SHA-chained delta of retained identities, so fourteen runs do not rewrite
all earlier process histories on each poll. All in-memory identities remain.
"""

import hashlib
import json
import os
from pathlib import Path
import time
import core
from owned_history import Registry, CASE_HISTORY, CAMPAIGN_HISTORY, identity

# Explicit independent bounds on files and bytes, not an unbounded log stream.
CASE_RECORDS = 4096
CAMPAIGN_RECORDS = 65536
CASE_FILE_BYTES = 4 * 1024**2
CAMPAIGN_FILE_BYTES = 16 * 1024**2
CASE_TOTAL_BYTES = 256 * 1024**2
CAMPAIGN_TOTAL_BYTES = 128 * 1024**2


class Ledger:
    def __init__(self, root, prefix, *, campaign=False):
        self.root, self.prefix, self.campaign = Path(root), prefix, campaign
        self.counter, self.total_bytes, self.previous_sha256 = 0, 0, None
        self.revisions, self.identities = {}, {}

    def __call__(self, child):
        key = (child.proc.pid, child.birth["starttime"] if child.birth else None)
        if self.revisions.get(key) == child.identity_revision:
            return
        value = {
            "label": child.label,
            "pid": child.proc.pid,
            "birth": child.birth,
            "known": child.known,
            "at": time.time(),
        }
        updates = {}
        if self.campaign:
            previous = self.identities.get(key, {})
            updates = {
                pid: item
                for pid, item in child.known.items()
                if previous.get(pid) != identity(item)
            }
            value = {
                **value,
                "known": updates,
                "schema_version": 1,
                "kind": "CAMPAIGN_OWNED_IDENTITY_DELTA",
                "sequence": self.counter + 1,
                "previous_sha256": self.previous_sha256,
                "retained_count": len(child.known),
            }
        limit = CAMPAIGN_RECORDS if self.campaign else CASE_RECORDS
        core.need(self.counter + 1 <= limit, "Owner ledger count bound")
        data = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
        core.need(
            len(data) <= (CAMPAIGN_FILE_BYTES if self.campaign else CASE_FILE_BYTES),
            "Owner ledger file byte bound",
        )
        core.need(
            self.total_bytes + len(data)
            <= (CAMPAIGN_TOTAL_BYTES if self.campaign else CASE_TOTAL_BYTES),
            "Owner ledger total byte bound",
        )
        # Exclusive fsync: update the in-memory checkpoint only after durable IO.
        path = self.root / f"{self.prefix}-{self.counter + 1:06d}.json"
        with path.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        self.counter += 1
        self.total_bytes += len(data)
        self.previous_sha256 = hashlib.sha256(data).hexdigest()
        self.revisions[key] = child.identity_revision
        if self.campaign:
            self.identities[key] = {
                pid: identity(item) for pid, item in child.known.items()
            }

    def verify(self):
        core.need(self.campaign, "Delta folding is campaign-only")
        folded = fold_campaign(self.root, self.prefix)
        core.need(
            folded == self.summary(), "Campaign ledger differs from retained memory"
        )
        return folded

    def summary(self):
        return {
            "schema_version": 1,
            "kind": "CAMPAIGN_OWNED_IDENTITY_DELTA"
            if self.campaign
            else "CASE_FULL_OWNER_SNAPSHOT",
            "files": self.counter,
            "bytes": self.total_bytes,
            "last_sha256": self.previous_sha256,
            "retained_identities": sum(len(items) for items in self.identities.values())
            if self.campaign
            else None,
            "history_limit": CAMPAIGN_HISTORY if self.campaign else CASE_HISTORY,
        }


def fold_campaign(root, prefix):
    """Reparse exact bounded durable deltas; never consult or mutate processes."""
    files = sorted(Path(root).glob(prefix + "-*.json"))
    core.need(1 <= len(files) <= CAMPAIGN_RECORDS, "Campaign ledger count bound")
    total, previous, leaders = 0, None, {}
    for index, path in enumerate(files, 1):
        core.need(
            path.name == f"{prefix}-{index:06d}.json", "Campaign ledger gap/extra"
        )
        descriptor = core.describe(path, CAMPAIGN_FILE_BYTES)
        total += descriptor["bytes"]
        core.need(total <= CAMPAIGN_TOTAL_BYTES, "Campaign ledger total byte bound")
        raw = path.read_bytes()
        core.need(
            hashlib.sha256(raw).hexdigest() == descriptor["sha256"], "Ledger changed"
        )
        row = json.loads(raw)
        core.need(
            set(row)
            == {
                "label",
                "pid",
                "birth",
                "known",
                "at",
                "schema_version",
                "kind",
                "sequence",
                "previous_sha256",
                "retained_count",
            },
            "Campaign ledger schema differs",
        )
        core.need(
            row["schema_version"] == 1
            and row["kind"] == "CAMPAIGN_OWNED_IDENTITY_DELTA"
            and row["sequence"] == index
            and row["previous_sha256"] == previous,
            "Campaign chain differs",
        )
        core.need(
            row["label"] in ("campaign", "campaign-worker"), "Campaign label differs"
        )
        birth = row["birth"]
        core.need(birth["pid"] == row["pid"], "Campaign leader birth differs")
        key = (row["pid"], birth["starttime"])
        if key not in leaders:
            leaders[key] = {"birth": birth, "label": row["label"], "known": {}}
        prior = leaders[key]
        core.need(
            prior["birth"] == birth and prior["label"] == row["label"],
            "Campaign leader changed",
        )
        core.need(
            isinstance(row["known"], dict) and bool(row["known"]),
            "Empty campaign identity delta",
        )
        for pid, value in row["known"].items():
            core.need(
                set(value) == {"pid", "state", "ppid", "pgid", "sid", "starttime"}
                and str(value["pid"]) == pid,
                "Noncanonical process identity",
            )
            core.need(
                all(
                    type(value[k]) is int and value[k] >= (0 if k == "ppid" else 1)
                    for k in ("pid", "ppid", "pgid", "sid", "starttime")
                )
                and isinstance(value["state"], str)
                and len(value["state"]) == 1,
                "Invalid process identity",
            )
            if pid in prior["known"]:
                core.need(
                    prior["known"][pid]["starttime"] == value["starttime"],
                    "Campaign PID reused",
                )
                core.need(
                    identity(prior["known"][pid]) != identity(value),
                    "State-only redundant delta",
                )
            prior["known"][pid] = value
        core.need(
            str(row["pid"]) in prior["known"]
            and prior["known"][str(row["pid"])]["starttime"] == birth["starttime"],
            "Campaign leader missing",
        )
        core.need(
            len(prior["known"]) == row["retained_count"],
            "Campaign retained count differs",
        )
        core.need(
            sum(len(v["known"]) for v in leaders.values()) <= CAMPAIGN_HISTORY,
            "Campaign history bound",
        )
        previous = descriptor["sha256"]
    return {
        "schema_version": 1,
        "kind": "CAMPAIGN_OWNED_IDENTITY_DELTA",
        "files": len(files),
        "bytes": total,
        "last_sha256": previous,
        "retained_identities": sum(len(v["known"]) for v in leaders.values()),
        "history_limit": CAMPAIGN_HISTORY,
    }


# Import the already reviewed case implementation; replace only its ownership
# registry and persistence callback. Command, environment and phase logic stay exact.
import campaign


class PosixIO(campaign.case_adapter.PosixIO):
    def __init__(self, spec):
        super().__init__(spec)
        self.ledger = Ledger(self.root, "owner")
        self.registry = Registry(self.persist_owner, history_limit=CASE_HISTORY)

    def persist_owner(self, child):
        self.ledger(child)
