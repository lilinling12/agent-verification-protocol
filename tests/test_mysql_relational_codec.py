from __future__ import annotations

import unittest
from datetime import timedelta

from avp_ref.relational import (
    ColumnDefinition,
    ColumnType,
    RelationalCompatibilityError,
    ValueType,
)
from avp_ref.tck_adapter.mysql_relational.codec import from_database, sql_type
from avp_ref.tck_adapter.mysql_relational.driver import (
    MySQLConnectionSettings,
    quote_identifier,
)


class MySQLRelationalCodecTest(unittest.TestCase):
    def test_integer_storage_preserves_portable_65_digit_domain(self) -> None:
        column = ColumnDefinition("value", ColumnType(ValueType.INTEGER))

        self.assertEqual("DECIMAL(65,0)", sql_type(column))

    def test_text_storage_uses_explicit_binary_utf8mb4_collation(self) -> None:
        column = ColumnDefinition("value", ColumnType(ValueType.TEXT))

        self.assertEqual(
            "LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin",
            sql_type(column),
        )

    def test_connector_timedelta_time_decodes_to_portable_local_time(self) -> None:
        column = ColumnDefinition(
            "value",
            ColumnType(ValueType.TIME_LOCAL, fractional_precision=6),
        )

        observed = from_database(
            column,
            timedelta(hours=23, minutes=59, seconds=58, microseconds=123456),
        )

        self.assertEqual("23:59:58.123456", observed.value)

    def test_time_outside_portable_day_fails_closed(self) -> None:
        column = ColumnDefinition(
            "value",
            ColumnType(ValueType.TIME_LOCAL, fractional_precision=0),
        )

        with self.assertRaisesRegex(
            RelationalCompatibilityError,
            "outside the portable local-time domain",
        ):
            from_database(column, timedelta(days=1))

    def test_control_dsn_decodes_credentials_without_exposing_driver_api(self) -> None:
        settings = MySQLConnectionSettings.from_dsn(
            "mysql://root:p%40ss@127.0.0.1:3307/mysql"
        )

        self.assertEqual("root", settings.user)
        self.assertEqual("p@ss", settings.password)
        self.assertEqual(3307, settings.port)
        self.assertEqual("mysql", settings.database)

    def test_identifier_quoting_rejects_non_generated_input(self) -> None:
        with self.assertRaises(RelationalCompatibilityError):
            quote_identifier("logical.id` DROP TABLE x")


if __name__ == "__main__":
    unittest.main()
