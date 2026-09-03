"""TEL-002 concurrency tests for deterministic run-scoped network allocation."""

from __future__ import annotations

import ipaddress
import unittest

from acceptance.network_control.toxiproxy_binding import ToxiproxyRunTopology


class RunTopologyConcurrencyTests(unittest.TestCase):
    def test_runs_that_shared_old_hash_bucket_receive_distinct_subnets(self) -> None:
        # run-20/run-21 share the first SHA-256 byte (0xcc), so the earlier
        # ~200-slot allocator mapped them to the same subnet. The 14-bit slot
        # allocator must keep these legitimate concurrent runs independent.
        first = ToxiproxyRunTopology.for_run("run-20")
        second = ToxiproxyRunTopology.for_run("run-21")
        self.assertNotEqual(first.admin_subnet, second.admin_subnet)
        self.assertNotEqual(first.data_subnet, second.data_subnet)

    def test_admin_and_data_address_pools_are_disjoint_private_ranges(self) -> None:
        for run_id in ("run-a", "run-b", "run-c", "run-d"):
            with self.subTest(run_id=run_id):
                topology = ToxiproxyRunTopology.for_run(run_id)
                admin = ipaddress.ip_address(topology.admin_address)
                data = ipaddress.ip_address(topology.data_address)
                self.assertTrue(admin.is_private)
                self.assertTrue(data.is_private)
                self.assertIn(admin.packed[1], range(64, 128))
                self.assertIn(data.packed[1], range(128, 192))
                self.assertNotEqual(topology.admin_subnet, topology.data_subnet)

    def test_role_host_offset_remains_stable_for_live_lab_materialization(self) -> None:
        topology = ToxiproxyRunTopology.for_run("stable-host-offset")
        self.assertEqual(int(ipaddress.ip_address(topology.admin_address)) & 0xF, 2)
        self.assertEqual(int(ipaddress.ip_address(topology.data_address)) & 0xF, 2)


if __name__ == "__main__":
    unittest.main()
