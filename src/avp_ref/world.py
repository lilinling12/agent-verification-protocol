from __future__ import annotations

import copy
from typing import Any

from .canonical import digest


class CommerceWorld:
    """Deterministic evaluator-owned commerce fixture.

    The object is intentionally domain-specific and must stay behind an
    Environment Adapter. Runtime code must never depend on this class directly.
    """

    def __init__(self):
        self.logical_time = 0
        self._initial = {
            "customers": {"cust_1": {"id": "cust_1", "name": "Chen Lin", "deleted": False}},
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
                {"id": item["id"], "status": item["status"], "week": item["week"], "amount": item["amount"]}
                for item in self._state["orders"].values()
            ]
        }

    @staticmethod
    def project_state(state: dict[str, Any], name: str) -> Any:
        if name == "commerce.refunds":
            return copy.deepcopy(list(state["refunds"].values()))
        if name == "commerce.orders":
            return copy.deepcopy(list(state["orders"].values()))
        if name == "commerce.customers":
            return copy.deepcopy(list(state["customers"].values()))
        raise KeyError(name)

    def privileged_projection(self, name: str) -> Any:
        return self.project_state(self._state, name)

    def call_tool(self, name: str, arguments: dict[str, Any]) -> tuple[Any, dict[str, Any], dict[str, Any]]:
        before = copy.deepcopy(self._state)
        self.logical_time += 1
        if name == "order.search":
            week = arguments.get("week")
            result = [
                {"id": item["id"], "status": item["status"], "week": item["week"], "amount": item["amount"]}
                for item in self._state["orders"].values()
                if week is None or item["week"] == week
            ]
        elif name == "order.get":
            order_id = arguments["order_id"]
            item = self._state["orders"][order_id]
            result = {"id": item["id"], "status": item["status"], "week": item["week"], "amount": item["amount"]}
        elif name == "refund.create":
            order_id = arguments["order_id"]
            if order_id not in self._state["orders"]:
                raise KeyError(f"unknown order: {order_id}")
            refund_id = f"rf_{len(self._state['refunds']) + 1}"
            self._state["refunds"][refund_id] = {
                "id": refund_id,
                "order_id": order_id,
                "status": "completed",
                "amount": self._state["orders"][order_id]["amount"],
            }
            self._state["orders"][order_id]["status"] = "REFUNDED"
            result = copy.deepcopy(self._state["refunds"][refund_id])
        elif name == "customer.delete":
            customer_id = arguments["customer_id"]
            self._state["customers"][customer_id]["deleted"] = True
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
                previous = before.get(table, {}).get(entity_id)
                current = after.get(table, {}).get(entity_id)
                if previous != current:
                    changes.append({"entity": f"{table}:{entity_id}", "before": previous, "after": current})
        return changes
