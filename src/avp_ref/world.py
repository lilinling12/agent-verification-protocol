from __future__ import annotations
import copy
from typing import Any
from .canonical import digest

class CommerceWorld:
    """Deterministic evaluator-owned commerce world.

    Subject-facing methods expose only allowed projections/tools.
    Hidden state remains inside this object and is never returned wholesale.
    """

    def __init__(self):
        self.logical_time = 0
        self._initial = {
            "customers": {
                "cust_1": {"id": "cust_1", "name": "Chen Lin", "deleted": False}
            },
            "orders": {
                "ord_1": {"id": "ord_1", "customer_id": "cust_1", "status": "PAID", "week": "last_week", "amount": 88.0},
                "ord_2": {"id": "ord_2", "customer_id": "cust_1", "status": "PAID", "week": "last_week", "amount": 168.0},
            },
            "refunds": {},
            "permissions": {"subject": ["orders.read", "refunds.create"]},
        }
        self._state = copy.deepcopy(self._initial)

    def reset(self) -> None:
        self.logical_time = 0
        self._state = copy.deepcopy(self._initial)

    def state_digest(self) -> str:
        return digest(self._state)

    def snapshot_state(self) -> dict[str, Any]:
        return copy.deepcopy(self._state)

    def restore_state(self, state: dict[str, Any], logical_time: int) -> None:
        self._state = copy.deepcopy(state)
        self.logical_time = logical_time

    def public_observation(self) -> dict[str, Any]:
        return {
            "orders": [
                {"id": x["id"], "status": x["status"], "week": x["week"], "amount": x["amount"]}
                for x in self._state["orders"].values()
            ]
        }

    def privileged_projection(self, name: str) -> Any:
        if name == "commerce.refunds":
            return copy.deepcopy(list(self._state["refunds"].values()))
        if name == "commerce.orders":
            return copy.deepcopy(list(self._state["orders"].values()))
        if name == "commerce.customers":
            return copy.deepcopy(list(self._state["customers"].values()))
        raise KeyError(name)

    def call_tool(self, name: str, arguments: dict[str, Any]) -> tuple[Any, dict[str, Any], dict[str, Any]]:
        before = copy.deepcopy(self._state)
        self.logical_time += 1

        if name == "order.search":
            week = arguments.get("week")
            result = [
                {"id": o["id"], "status": o["status"], "week": o["week"], "amount": o["amount"]}
                for o in self._state["orders"].values()
                if week is None or o["week"] == week
            ]
        elif name == "order.get":
            oid = arguments["order_id"]
            o = self._state["orders"][oid]
            result = {"id": o["id"], "status": o["status"], "week": o["week"], "amount": o["amount"]}
        elif name == "refund.create":
            oid = arguments["order_id"]
            if oid not in self._state["orders"]:
                raise KeyError(f"unknown order: {oid}")
            rid = f"rf_{len(self._state['refunds']) + 1}"
            self._state["refunds"][rid] = {
                "id": rid,
                "order_id": oid,
                "status": "completed",
                "amount": self._state["orders"][oid]["amount"],
            }
            self._state["orders"][oid]["status"] = "REFUNDED"
            result = copy.deepcopy(self._state["refunds"][rid])
        elif name == "customer.delete":
            cid = arguments["customer_id"]
            self._state["customers"][cid]["deleted"] = True
            result = {"deleted": True}
        else:
            raise KeyError(f"unknown tool: {name}")

        return result, before, copy.deepcopy(self._state)

    @staticmethod
    def semantic_diff(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
        changes = []
        for table in ("customers", "orders", "refunds"):
            ids = set(before.get(table, {})) | set(after.get(table, {}))
            for entity_id in sorted(ids):
                b = before.get(table, {}).get(entity_id)
                a = after.get(table, {}).get(entity_id)
                if b != a:
                    changes.append({"entity": f"{table}:{entity_id}", "before": b, "after": a})
        return changes
