"""Deterministic synthetic-data generator for industrial service operations."""

from __future__ import annotations

import csv
import hashlib
import json
import random
import shutil
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

from industrial_service_platform.generation.config import GenerationConfig
from industrial_service_platform.generation.validation import (
    Row,
    Tables,
    validate_tables,
)

UTC = timezone.utc


@dataclass(frozen=True)
class GenerationResult:
    """Paths and row counts produced by one generation run."""

    row_counts: dict[str, int]
    output_directory: Path
    sample_directory: Path
    manifest_path: Path
    validation_report_path: Path


class SyntheticDataGenerator:
    """Generate relationally consistent industrial service datasets."""

    def __init__(
        self,
        config: GenerationConfig,
        schema_path: Path,
        project_root: Path | None = None,
    ) -> None:
        self.config = config
        self.project_root = project_root or Path.cwd()
        self.schema_path = schema_path
        self.schema: dict[str, Any] = json.loads(schema_path.read_text(encoding="utf-8"))
        self.rng = random.Random(config.seed)
        self.tables: Tables = {}
        self._case_events: list[Row] = []
        self._order_metadata: dict[str, dict[str, Any]] = {}

    def generate(self) -> GenerationResult:
        """Generate, validate, and write all configured datasets."""
        self._validate_required_row_counts()
        self.tables = {}
        self._case_events = []
        self._order_metadata = {}

        self.tables["customers"] = self._generate_customers()
        self.tables["sites"] = self._generate_sites()
        self.tables["assets"] = self._generate_assets()
        self.tables["service_contracts"] = self._generate_contracts()
        self.tables["technicians"] = self._generate_technicians()
        self.tables["parts"] = self._generate_parts()
        self.tables["customer_cases"] = self._generate_cases()
        self.tables["case_status_history"] = self._case_events
        self.tables["service_orders"] = self._generate_service_orders()
        self.tables["service_order_parts"] = self._generate_service_order_parts()
        self.tables["service_costs"] = self._generate_service_costs()
        self.tables["equipment_alerts"] = self._generate_equipment_alerts()
        self.tables["technician_notes"] = self._generate_technician_notes()

        expected_counts = {
            name: count for name, count in self.config.row_counts.items() if name in self.tables
        }
        report = validate_tables(self.tables, self.schema, expected_counts=expected_counts)
        if not report.is_valid:
            preview = "; ".join(
                f"{issue.dataset}:{issue.row_number}:{issue.code}" for issue in report.issues[:10]
            )
            raise RuntimeError(f"Generated data failed validation: {preview}")

        output_directory = self._resolve(self.config.output_directory)
        sample_directory = self._resolve(self.config.sample_directory)
        self._prepare_directory(output_directory)
        self._prepare_directory(sample_directory)

        self._write_tables(output_directory, self.tables)
        self._write_sample_tables(sample_directory, self.tables)
        invalid_manifest = self._write_invalid_examples(output_directory, sample_directory)

        validation_report_path = output_directory / "validation_report.json"
        report.write_json(validation_report_path)
        report.write_json(sample_directory / "validation_report.json")

        summary = self._build_summary(invalid_manifest)
        self._write_json(output_directory / "generation_summary.json", summary)
        self._write_json(sample_directory / "generation_summary.json", summary)

        manifest_path = output_directory / "generation_manifest.json"
        self._write_manifest(output_directory, manifest_path)
        self._write_manifest(sample_directory, sample_directory / "generation_manifest.json")

        return GenerationResult(
            row_counts={name: len(rows) for name, rows in self.tables.items()},
            output_directory=output_directory,
            sample_directory=sample_directory,
            manifest_path=manifest_path,
            validation_report_path=validation_report_path,
        )

    def _validate_required_row_counts(self) -> None:
        required = {
            "customers",
            "sites",
            "assets",
            "service_contracts",
            "technicians",
            "parts",
            "customer_cases",
            "service_orders",
            "service_order_parts",
            "equipment_alerts",
            "technician_notes",
        }
        missing = sorted(required - self.config.row_counts.keys())
        if missing:
            raise ValueError(f"Missing required row-count settings: {missing}")

    def _generate_customers(self) -> list[Row]:
        prefixes = [
            "Nordic",
            "Baltic",
            "Helios",
            "Meridian",
            "Atlas",
            "Vistula",
            "Danube",
            "Aurora",
            "Summit",
            "Orion",
        ]
        nouns = [
            "Energy",
            "Process Industries",
            "Industrial Systems",
            "Materials",
            "Utilities",
            "Engineering",
            "Manufacturing",
            "Resources",
        ]
        industries = ["ENERGY", "CHEMICALS", "MANUFACTURING", "MINING", "UTILITIES"]
        regions = ["NORTH", "SOUTH", "EAST", "WEST", "CENTRAL"]
        rows: list[Row] = []
        for index in range(1, self.config.required_count("customers") + 1):
            created = self._random_datetime(
                self.config.history_start - timedelta(days=900),
                self.config.history_start + timedelta(days=120),
            )
            updated = self._random_datetime(created, self.config.reporting_as_of)
            name = f"{self.rng.choice(prefixes)} {self.rng.choice(nouns)} {index:03d}"
            rows.append(
                {
                    "customer_id": self._identifier("CUST", index),
                    "customer_name": name,
                    "industry": self.rng.choice(industries),
                    "customer_region": self.rng.choice(regions),
                    "customer_status": "ACTIVE" if self.rng.random() < 0.94 else "INACTIVE",
                    "created_at": self._timestamp(created),
                    "updated_at": self._timestamp(updated),
                }
            )
        return rows

    def _generate_sites(self) -> list[Row]:
        countries = [
            ("DE", "Europe/Berlin"),
            ("PL", "Europe/Warsaw"),
            ("SE", "Europe/Stockholm"),
            ("DK", "Europe/Copenhagen"),
            ("FI", "Europe/Helsinki"),
            ("NL", "Europe/Amsterdam"),
            ("NO", "Europe/Oslo"),
            ("CZ", "Europe/Prague"),
        ]
        site_terms = ["Plant", "Works", "Terminal", "Station", "Processing Site", "Service Base"]
        customers = self.tables["customers"]
        rows: list[Row] = []
        for index in range(1, self.config.required_count("sites") + 1):
            customer = customers[(index - 1) % len(customers)]
            country, timezone_name = self.rng.choice(countries)
            customer_created = self._parse_timestamp(customer["created_at"])
            created = self._random_datetime(
                max(customer_created, self.config.history_start - timedelta(days=600)),
                self.config.history_start + timedelta(days=240),
            )
            updated = self._random_datetime(created, self.config.reporting_as_of)
            rows.append(
                {
                    "site_id": self._identifier("SITE", index),
                    "customer_id": customer["customer_id"],
                    "site_name": f"{country} {self.rng.choice(site_terms)} {index:03d}",
                    "country_code": country,
                    "region": customer["customer_region"],
                    "timezone": timezone_name,
                    "site_status": "ACTIVE" if self.rng.random() < 0.95 else "INACTIVE",
                    "created_at": self._timestamp(created),
                    "updated_at": self._timestamp(updated),
                }
            )
        self.rng.shuffle(rows)
        return rows

    def _generate_assets(self) -> list[Row]:
        asset_types = ["GAS_TURBINE", "STEAM_TURBINE", "COMPRESSOR", "INDUSTRIAL_PUMP"]
        type_weights = [0.18, 0.16, 0.34, 0.32]
        manufacturers = [
            "Apex Dynamics",
            "Northstar Engineering",
            "Helix Machinery",
            "Vector Works",
        ]
        criticalities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        criticality_weights = [0.15, 0.45, 0.30, 0.10]
        sites = self.tables["sites"]
        rows: list[Row] = []
        earliest_install = date(1998, 1, 1)
        latest_install = (self.config.reporting_as_of - timedelta(days=90)).date()
        for index in range(1, self.config.required_count("assets") + 1):
            site = self.rng.choice(sites)
            asset_type = self.rng.choices(asset_types, weights=type_weights, k=1)[0]
            installation = self._random_date(earliest_install, latest_install)
            created_start = max(
                installation,
                self.config.history_start.date() - timedelta(days=365),
            )
            created_date = self._random_date(
                created_start,
                self.config.history_start.date() + timedelta(days=300),
            )
            created = datetime.combine(created_date, datetime.min.time(), tzinfo=UTC) + timedelta(
                hours=self.rng.randint(0, 23)
            )
            updated = self._random_datetime(created, self.config.reporting_as_of)
            status_roll = self.rng.random()
            status = "ACTIVE"
            if status_roll < 0.03:
                status = "RETIRED"
            elif status_roll < 0.08:
                status = "OUT_OF_SERVICE"
            manufacturer = self.rng.choice(manufacturers)
            rows.append(
                {
                    "asset_id": self._identifier("ASSET", index),
                    "site_id": site["site_id"],
                    "asset_name": f"{asset_type.replace('_', ' ').title()} {index:04d}",
                    "asset_type": asset_type,
                    "manufacturer": manufacturer,
                    "model": f"{manufacturer.split()[0][:3].upper()}-{self.rng.randint(100, 999)}",
                    "serial_number": f"SN-{index:08d}",
                    "installation_date": installation.isoformat(),
                    "criticality": self.rng.choices(
                        criticalities,
                        weights=criticality_weights,
                        k=1,
                    )[0],
                    "asset_status": status,
                    "created_at": self._timestamp(created),
                    "updated_at": self._timestamp(updated),
                }
            )
        return rows

    def _generate_contracts(self) -> list[Row]:
        sites = self.tables["sites"]
        customer_by_id = self._index(self.tables["customers"], "customer_id")
        contract_types = ["BASIC", "STANDARD", "PREMIUM"]
        response_hours = {"BASIC": 24, "STANDARD": 8, "PREMIUM": 2}
        resolution_hours = {"BASIC": 168, "STANDARD": 72, "PREMIUM": 24}
        rows: list[Row] = []
        count = self.config.required_count("service_contracts")
        for index in range(1, count + 1):
            site = sites[(index - 1) % len(sites)]
            customer = customer_by_id[site["customer_id"]]
            cycle = (index - 1) // len(sites)
            if cycle % 2 == 0:
                start = self._random_date(date(2022, 1, 1), date(2023, 12, 31))
                end = start + timedelta(days=self.rng.randint(540, 900))
            else:
                start = self._random_date(date(2025, 1, 1), date(2026, 3, 1))
                end = start + timedelta(days=self.rng.randint(540, 1000))
            contract_type = self.rng.choices(contract_types, weights=[0.25, 0.50, 0.25], k=1)[0]
            status = "ACTIVE"
            reporting_date = self.config.reporting_as_of.date()
            if self.rng.random() < 0.04:
                status = "CANCELLED"
            elif start > reporting_date:
                status = "DRAFT"
            elif end < reporting_date:
                status = "EXPIRED"
            created = datetime.combine(
                max(
                    customer_creation_date(customer),
                    start - timedelta(days=self.rng.randint(20, 120)),
                ),
                datetime.min.time(),
                tzinfo=UTC,
            )
            updated = self._random_datetime(created, self.config.reporting_as_of)
            rows.append(
                {
                    "contract_id": self._identifier("CONT", index),
                    "customer_id": site["customer_id"],
                    "site_id": site["site_id"],
                    "contract_type": contract_type,
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                    "response_sla_hours": str(response_hours[contract_type]),
                    "resolution_sla_hours": str(resolution_hours[contract_type]),
                    "contract_status": status,
                    "created_at": self._timestamp(created),
                    "updated_at": self._timestamp(updated),
                }
            )
        return rows

    def _generate_technicians(self) -> list[Row]:
        first_names = [
            "Anna",
            "Marek",
            "Lina",
            "Erik",
            "Sara",
            "Jonas",
            "Klara",
            "Tomas",
            "Nadia",
            "Emil",
        ]
        last_names = [
            "Nowak",
            "Lindberg",
            "Hansen",
            "Kowalski",
            "Berg",
            "Muller",
            "Novak",
            "Jensen",
            "Kallio",
            "Svensson",
        ]
        regions = ["NORTH", "SOUTH", "EAST", "WEST", "CENTRAL"]
        specialisations = [
            "ROTATING_EQUIPMENT",
            "ELECTRICAL",
            "CONTROLS",
            "INSTRUMENTATION",
            "GENERAL",
        ]
        levels = ["JUNIOR", "INTERMEDIATE", "SENIOR", "EXPERT"]
        rows: list[Row] = []
        for index in range(1, self.config.required_count("technicians") + 1):
            created = self._random_datetime(
                self.config.history_start - timedelta(days=600),
                self.config.history_start + timedelta(days=300),
            )
            updated = self._random_datetime(created, self.config.reporting_as_of)
            rows.append(
                {
                    "technician_id": self._identifier("TECH", index),
                    "technician_name": (
                        f"{self.rng.choice(first_names)} {self.rng.choice(last_names)} {index:03d}"
                    ),
                    "home_region": self.rng.choice(regions),
                    "specialisation": self.rng.choice(specialisations),
                    "skill_level": self.rng.choices(
                        levels,
                        weights=[0.18, 0.38, 0.32, 0.12],
                        k=1,
                    )[0],
                    "technician_status": "ACTIVE" if self.rng.random() < 0.96 else "INACTIVE",
                    "created_at": self._timestamp(created),
                    "updated_at": self._timestamp(updated),
                }
            )
        return rows

    def _generate_parts(self) -> list[Row]:
        categories = [
            "BEARING",
            "SEAL",
            "LUBRICATION",
            "ELECTRICAL",
            "CONTROL",
            "VALVE",
            "FILTER",
            "FASTENER",
            "OTHER",
        ]
        cost_ranges = {
            "BEARING": (400, 16000),
            "SEAL": (80, 5000),
            "LUBRICATION": (25, 1200),
            "ELECTRICAL": (120, 9000),
            "CONTROL": (250, 18000),
            "VALVE": (300, 22000),
            "FILTER": (30, 1800),
            "FASTENER": (5, 450),
            "OTHER": (50, 7000),
        }
        rows: list[Row] = []
        for index in range(1, self.config.required_count("parts") + 1):
            category = categories[(index - 1) % len(categories)]
            low, high = cost_ranges[category]
            created = self._random_datetime(
                self.config.history_start - timedelta(days=500),
                self.config.history_start + timedelta(days=365),
            )
            updated = self._random_datetime(created, self.config.reporting_as_of)
            rows.append(
                {
                    "part_id": self._identifier("PART", index),
                    "part_name": f"{category.replace('_', ' ').title()} Assembly {index:04d}",
                    "part_category": category,
                    "unit_cost_eur": self._money(self.rng.uniform(low, high)),
                    "standard_lead_time_days": str(self.rng.randint(1, 45)),
                    "part_status": "OBSOLETE" if self.rng.random() < 0.06 else "ACTIVE",
                    "created_at": self._timestamp(created),
                    "updated_at": self._timestamp(updated),
                }
            )
        return rows

    def _generate_cases(self) -> list[Row]:
        assets = self.tables["assets"]
        sites_by_id = self._index(self.tables["sites"], "site_id")
        contracts_by_site = self._group(self.tables["service_contracts"], "site_id")
        asset_weights = [self._asset_event_weight(asset) for asset in assets]
        case_types = [
            "TECHNICAL_FAULT",
            "INSPECTION_REQUEST",
            "MAINTENANCE_REQUEST",
            "GENERAL_ENQUIRY",
        ]
        rows: list[Row] = []
        event_counter = 1
        for index in range(1, self.config.required_count("customer_cases") + 1):
            case_type = self.rng.choices(case_types, weights=[0.68, 0.10, 0.17, 0.05], k=1)[0]
            asset: Row | None = None
            if case_type != "GENERAL_ENQUIRY" or self.rng.random() < 0.25:
                asset = self.rng.choices(assets, weights=asset_weights, k=1)[0]
            if asset is None:
                site = self.rng.choice(self.tables["sites"])
            else:
                site = sites_by_id[asset["site_id"]]

            created_start = self.config.history_start
            if asset is not None:
                installation = datetime.combine(
                    date.fromisoformat(asset["installation_date"]),
                    datetime.min.time(),
                    tzinfo=UTC,
                )
                created_start = max(created_start, installation)
            created = self._random_datetime(
                created_start,
                self.config.reporting_as_of - timedelta(hours=2),
            )

            contract = self._contract_for_date(
                contracts_by_site.get(site["site_id"], []),
                created.date(),
            )
            priority = self._case_priority(case_type, asset)
            fault_category = self._fault_category(case_type, asset)
            response_sla, resolution_sla = self._case_sla_hours(priority, contract)
            response_due = created + timedelta(hours=response_sla)
            resolution_due = created + timedelta(hours=resolution_sla)
            status = self._case_status(created)

            response_delay_factor = self.rng.uniform(0.15, 1.6)
            first_response: datetime | None = None
            if status != "CANCELLED" and (
                self.rng.random() < 0.94 or self.config.reporting_as_of <= response_due
            ):
                first_response = min(
                    created + timedelta(hours=response_sla * response_delay_factor),
                    self.config.reporting_as_of,
                )

            resolved: datetime | None = None
            closed: datetime | None = None
            if status in {"RESOLVED", "CLOSED"}:
                base_hours = self._resolution_hours(priority, fault_category)
                resolved = min(
                    created + timedelta(hours=base_hours),
                    self.config.reporting_as_of - timedelta(minutes=10),
                )
                if resolved <= created:
                    status = "IN_PROGRESS"
                    resolved = None
                elif status == "CLOSED":
                    closed = min(
                        resolved + timedelta(hours=self.rng.uniform(2, 72)),
                        self.config.reporting_as_of,
                    )

            terminal = closed or resolved or first_response or created
            updated = min(
                max(terminal, created) + timedelta(hours=self.rng.uniform(0, 48)),
                self.config.reporting_as_of,
            )
            case_id = self._identifier("CASE", index)
            row = {
                "case_id": case_id,
                "customer_id": site["customer_id"],
                "site_id": site["site_id"],
                "contract_id": contract["contract_id"] if contract is not None else "",
                "asset_id": asset["asset_id"] if asset is not None else "",
                "case_type": case_type,
                "priority": priority,
                "fault_category": fault_category,
                "case_status": status,
                "created_at": self._timestamp(created),
                "response_due_at": self._timestamp(response_due),
                "resolution_due_at": self._timestamp(resolution_due),
                "first_response_at": self._timestamp(first_response) if first_response else "",
                "resolved_at": self._timestamp(resolved) if resolved else "",
                "closed_at": self._timestamp(closed) if closed else "",
                "updated_at": self._timestamp(updated),
            }
            rows.append(row)
            events, event_counter = self._case_status_events(row, event_counter)
            self._case_events.extend(events)
        return rows

    def _generate_service_orders(self) -> list[Row]:
        cases = [row for row in self.tables["customer_cases"] if row["asset_id"]]
        assets_by_id = self._index(self.tables["assets"], "asset_id")
        sites_by_id = self._index(self.tables["sites"], "site_id")
        technicians = self.tables["technicians"]
        rows: list[Row] = []
        for index in range(1, self.config.required_count("service_orders") + 1):
            linked_case = self.rng.choice(cases) if self.rng.random() < 0.86 else None
            if linked_case is None:
                asset = self.rng.choice(self.tables["assets"])
                case_id = ""
                order_type = "PREVENTIVE_MAINTENANCE"
                created_by = "PLANNED_MAINTENANCE"
                fault_category = "INSPECTION"
                created = self._random_datetime(
                    self.config.history_start,
                    self.config.reporting_as_of - timedelta(hours=12),
                )
            else:
                asset = assets_by_id[linked_case["asset_id"]]
                case_id = linked_case["case_id"]
                order_type = self._order_type(linked_case)
                created_by = "CRM_CASE"
                fault_category = linked_case["fault_category"] or "OTHER"
                case_created = self._parse_timestamp(linked_case["created_at"])
                case_end = (
                    self._parse_timestamp(linked_case["resolved_at"])
                    if linked_case["resolved_at"]
                    else self.config.reporting_as_of
                )
                latest_created = max(case_created, case_end - timedelta(hours=2))
                created = self._random_datetime(case_created, latest_created)

            site = sites_by_id[asset["site_id"]]
            technician = self._choose_technician(technicians, fault_category, site["region"])
            delay_propensity = min(
                0.95,
                max(
                    0.05,
                    self.rng.betavariate(2.0, 4.5)
                    + (0.18 if order_type == "EMERGENCY_REPAIR" else 0.0),
                ),
            )
            status = self._order_status(linked_case)
            scheduled = created + timedelta(hours=self.rng.uniform(4, 96))
            actual: datetime | None = None
            completed: datetime | None = None
            downtime_start: datetime | None = None
            downtime_end: datetime | None = None
            resolution_code = ""

            if status in {"IN_PROGRESS", "COMPLETED"}:
                actual = min(
                    scheduled + timedelta(hours=self.rng.uniform(-3, 24)),
                    self.config.reporting_as_of - timedelta(minutes=20),
                )
                actual = max(actual, created)
                duration_hours = self._order_duration_hours(order_type, delay_propensity)
                if status == "COMPLETED":
                    completed = min(
                        actual + timedelta(hours=duration_hours),
                        self.config.reporting_as_of,
                    )
                    if linked_case is not None and linked_case["resolved_at"]:
                        case_resolved = self._parse_timestamp(linked_case["resolved_at"])
                        completed = min(completed, case_resolved)
                        if completed <= actual:
                            actual = max(created, completed - timedelta(hours=0.5))
                    resolution_code = self.rng.choices(
                        [
                            "FIXED",
                            "ADJUSTED",
                            "REPLACED_COMPONENT",
                            "NO_FAULT_FOUND",
                            "FOLLOW_UP_REQUIRED",
                        ],
                        weights=[0.34, 0.20, 0.24, 0.08, 0.14],
                        k=1,
                    )[0]
                if order_type in {"CORRECTIVE_REPAIR", "EMERGENCY_REPAIR"}:
                    downtime_start = actual
                    downtime_end = completed or min(
                        self.config.reporting_as_of,
                        actual + timedelta(hours=duration_hours),
                    )
            elif status == "CANCELLED":
                resolution_code = "NOT_COMPLETED"

            order_id = self._identifier("SORD", index)
            rows.append(
                {
                    "service_order_id": order_id,
                    "case_id": case_id,
                    "asset_id": asset["asset_id"],
                    "lead_technician_id": technician["technician_id"],
                    "order_type": order_type,
                    "order_status": status,
                    "created_at": self._timestamp(created),
                    "scheduled_start_at": self._timestamp(scheduled),
                    "actual_start_at": self._timestamp(actual) if actual else "",
                    "completed_at": self._timestamp(completed) if completed else "",
                    "downtime_start_at": self._timestamp(downtime_start) if downtime_start else "",
                    "downtime_end_at": self._timestamp(downtime_end) if downtime_end else "",
                    "resolution_code": resolution_code,
                    "created_by_source": created_by,
                }
            )
            self._order_metadata[order_id] = {
                "delay_propensity": delay_propensity,
                "fault_category": fault_category,
                "site_region": site["region"],
            }
        return rows

    def _generate_service_order_parts(self) -> list[Row]:
        orders = [
            row
            for row in self.tables["service_orders"]
            if row["order_status"] in {"IN_PROGRESS", "COMPLETED"}
        ]
        parts_by_category = self._group(self.tables["parts"], "part_category")
        counters: dict[str, int] = {}
        rows: list[Row] = []
        weights = [
            0.5 + float(self._order_metadata[row["service_order_id"]]["delay_propensity"])
            for row in orders
        ]
        for _ in range(self.config.required_count("service_order_parts")):
            order = self.rng.choices(orders, weights=weights, k=1)[0]
            order_id = order["service_order_id"]
            counters[order_id] = counters.get(order_id, 0) + 1
            category = self._part_category_for_fault(
                str(self._order_metadata[order_id]["fault_category"])
            )
            candidates = parts_by_category.get(category, self.tables["parts"])
            part = self.rng.choice(candidates)
            created = self._parse_timestamp(order["created_at"])
            actual = (
                self._parse_timestamp(order["actual_start_at"])
                if order["actual_start_at"]
                else created + timedelta(hours=12)
            )
            requested = self._random_datetime(created, max(created, actual))
            required = requested + timedelta(days=self.rng.randint(1, 7))
            propensity = float(self._order_metadata[order_id]["delay_propensity"])
            delivered: datetime | None
            if (
                order["order_status"] == "IN_PROGRESS"
                and self.rng.random() < 0.18 + propensity * 0.35
            ):
                delivered = None
            else:
                if self.rng.random() < 0.12 + propensity * 0.60:
                    delay_days = self.rng.randint(1, max(2, int(3 + propensity * 25)))
                    delivered = required + timedelta(
                        days=delay_days,
                        hours=self.rng.randint(0, 20),
                    )
                else:
                    delivered = max(
                        requested,
                        required - timedelta(hours=self.rng.randint(0, 36)),
                    )
            rows.append(
                {
                    "service_order_id": order_id,
                    "part_id": part["part_id"],
                    "line_number": str(counters[order_id]),
                    "quantity": str(self.rng.randint(1, 4)),
                    "requested_at": self._timestamp(requested),
                    "required_at": self._timestamp(required),
                    "delivered_at": self._timestamp(delivered) if delivered else "",
                    "unit_cost_eur": part["unit_cost_eur"],
                }
            )
        rows.sort(key=lambda row: (row["service_order_id"], int(row["line_number"])))
        return rows

    def _generate_service_costs(self) -> list[Row]:
        part_lines = self._group(self.tables["service_order_parts"], "service_order_id")
        technicians = self._index(self.tables["technicians"], "technician_id")
        assets = self._index(self.tables["assets"], "asset_id")
        sites = self._index(self.tables["sites"], "site_id")
        rows: list[Row] = []
        cost_index = 1
        for order in self.tables["service_orders"]:
            if order["order_status"] == "CANCELLED":
                continue
            recorded_at = (
                self._parse_timestamp(order["completed_at"])
                if order["completed_at"]
                else self._parse_timestamp(order["scheduled_start_at"])
            )
            duration = self._duration_hours(order["actual_start_at"], order["completed_at"])
            estimated_hours = max(duration, 4.0)
            labour_rate = self.rng.uniform(70, 145)
            rows.append(
                self._cost_row(
                    cost_index,
                    order,
                    "LABOUR",
                    estimated_hours * labour_rate,
                    recorded_at,
                )
            )
            cost_index += 1

            technician = technicians[order["lead_technician_id"]]
            asset = assets[order["asset_id"]]
            site = sites[asset["site_id"]]
            travel_multiplier = 1.8 if technician["home_region"] != site["region"] else 1.0
            rows.append(
                self._cost_row(
                    cost_index,
                    order,
                    "TRAVEL",
                    self.rng.uniform(90, 700) * travel_multiplier,
                    recorded_at,
                )
            )
            cost_index += 1

            lines = part_lines.get(order["service_order_id"], [])
            if lines:
                part_total = sum(
                    Decimal(line["unit_cost_eur"]) * int(line["quantity"]) for line in lines
                )
                rows.append(
                    self._cost_row(
                        cost_index,
                        order,
                        "PART",
                        float(part_total),
                        recorded_at,
                    )
                )
                cost_index += 1

            if self.rng.random() < 0.12:
                rows.append(
                    self._cost_row(
                        cost_index,
                        order,
                        "EXTERNAL_SERVICE",
                        self.rng.uniform(400, 9000),
                        recorded_at,
                    )
                )
                cost_index += 1
        return rows

    def _generate_equipment_alerts(self) -> list[Row]:
        assets = self.tables["assets"]
        asset_weights = [self._asset_event_weight(asset) for asset in assets]
        cases_by_asset = self._group(
            [row for row in self.tables["customer_cases"] if row["asset_id"]],
            "asset_id",
        )
        rows: list[Row] = []
        for index in range(1, self.config.required_count("equipment_alerts") + 1):
            link_to_case = self.rng.random() < 0.38
            related_case: Row | None = None
            if link_to_case:
                linked_candidates = [
                    row for row in self.tables["customer_cases"] if row["asset_id"]
                ]
                related_case = self.rng.choice(linked_candidates)
                asset = self._find(assets, "asset_id", related_case["asset_id"])
                case_created = self._parse_timestamp(related_case["created_at"])
                installation = datetime.combine(
                    date.fromisoformat(asset["installation_date"]),
                    datetime.min.time(),
                    tzinfo=UTC,
                )
                raised = max(
                    installation,
                    case_created - timedelta(hours=self.rng.uniform(0, 72)),
                )
            else:
                asset = self.rng.choices(assets, weights=asset_weights, k=1)[0]
                installation = datetime.combine(
                    date.fromisoformat(asset["installation_date"]),
                    datetime.min.time(),
                    tzinfo=UTC,
                )
                raised = self._random_datetime(
                    max(self.config.history_start, installation),
                    self.config.reporting_as_of - timedelta(minutes=20),
                )
                candidates = cases_by_asset.get(asset["asset_id"], [])
                if candidates and self.rng.random() < 0.05:
                    related_case = self.rng.choice(candidates)

            alert_type = self._alert_type_for_case_or_asset(related_case, asset)
            severity = self._alert_severity(asset, related_case)
            threshold, measured, unit = self._measurement(alert_type, severity)
            age_hours = (self.config.reporting_as_of - raised).total_seconds() / 3600
            status = self._alert_status(age_hours, severity)
            acknowledged: datetime | None = None
            cleared: datetime | None = None
            if status in {"ACKNOWLEDGED", "CLEARED"}:
                acknowledged = min(
                    raised
                    + timedelta(
                        hours=self.rng.uniform(
                            0.1,
                            12 if severity == "CRITICAL" else 36,
                        )
                    ),
                    self.config.reporting_as_of,
                )
            if status == "CLEARED":
                cleared = min(
                    (acknowledged or raised) + timedelta(hours=self.rng.uniform(1, 120)),
                    self.config.reporting_as_of,
                )
            rows.append(
                {
                    "alert_id": self._identifier("ALERT", index),
                    "asset_id": asset["asset_id"],
                    "related_case_id": related_case["case_id"] if related_case is not None else "",
                    "alert_type": alert_type,
                    "severity": severity,
                    "alert_status": status,
                    "raised_at": self._timestamp(raised),
                    "acknowledged_at": self._timestamp(acknowledged) if acknowledged else "",
                    "cleared_at": self._timestamp(cleared) if cleared else "",
                    "measured_value": self._decimal6(measured),
                    "threshold_value": self._decimal6(threshold),
                    "measurement_unit": unit,
                }
            )
        return rows

    def _generate_technician_notes(self) -> list[Row]:
        orders = [
            row
            for row in self.tables["service_orders"]
            if row["actual_start_at"] and row["order_status"] != "CANCELLED"
        ]
        cases = self._index(self.tables["customer_cases"], "case_id")
        assets = self._index(self.tables["assets"], "asset_id")
        rows: list[Row] = []
        for index in range(1, self.config.required_count("technician_notes") + 1):
            order = self.rng.choice(orders)
            case = cases.get(order["case_id"])
            asset = assets[order["asset_id"]]
            note_type = self.rng.choices(
                ["INSPECTION", "DIAGNOSIS", "REPAIR", "COMPLETION"],
                weights=[0.24, 0.29, 0.30, 0.17],
                k=1,
            )[0]
            actual = self._parse_timestamp(order["actual_start_at"])
            end = (
                self._parse_timestamp(order["completed_at"])
                if order["completed_at"]
                else self.config.reporting_as_of
            )
            created = self._random_datetime(actual, max(actual, end))
            fault = (
                case["fault_category"]
                if case is not None and case["fault_category"]
                else str(self._order_metadata[order["service_order_id"]]["fault_category"])
            )
            text = self._note_text(note_type, fault, asset["asset_type"], order["resolution_code"])
            rows.append(
                {
                    "note_id": self._identifier("NOTE", index),
                    "service_order_id": order["service_order_id"],
                    "technician_id": order["lead_technician_id"],
                    "note_type": note_type,
                    "note_text": text,
                    "created_at": self._timestamp(created),
                }
            )
        return rows

    def _case_status_events(self, case: Row, start_index: int) -> tuple[list[Row], int]:
        created = self._parse_timestamp(case["created_at"])
        updated = self._parse_timestamp(case["updated_at"])
        status = case["case_status"]
        sequence = ["OPEN"]
        if status == "ASSIGNED":
            sequence.append("ASSIGNED")
        elif status == "IN_PROGRESS":
            sequence.extend(["ASSIGNED", "IN_PROGRESS"])
        elif status == "WAITING_PARTS":
            sequence.extend(["ASSIGNED", "IN_PROGRESS", "WAITING_PARTS"])
        elif status == "RESOLVED":
            sequence.extend(["ASSIGNED", "IN_PROGRESS"])
            if self.rng.random() < 0.30:
                sequence.append("WAITING_PARTS")
            sequence.append("RESOLVED")
        elif status == "CLOSED":
            sequence.extend(["ASSIGNED", "IN_PROGRESS"])
            if self.rng.random() < 0.30:
                sequence.append("WAITING_PARTS")
            sequence.extend(["RESOLVED", "CLOSED"])
        elif status == "CANCELLED":
            if self.rng.random() < 0.45:
                sequence.append("ASSIGNED")
            sequence.append("CANCELLED")

        terminal = updated
        if case["closed_at"]:
            terminal = self._parse_timestamp(case["closed_at"])
        elif case["resolved_at"]:
            terminal = self._parse_timestamp(case["resolved_at"])
        if terminal < created:
            terminal = created

        events: list[Row] = []
        previous = ""
        for position, new_status in enumerate(sequence):
            if len(sequence) == 1:
                changed = created
            else:
                fraction = position / (len(sequence) - 1)
                changed = created + (terminal - created) * fraction
            events.append(
                {
                    "case_status_event_id": self._identifier("CSEVT", start_index),
                    "case_id": case["case_id"],
                    "previous_status": previous,
                    "new_status": new_status,
                    "changed_at": self._timestamp(changed),
                    "change_reason": self._status_reason(new_status),
                }
            )
            start_index += 1
            previous = new_status
        return events, start_index

    def _write_tables(self, directory: Path, tables: Tables) -> None:
        for dataset_name, rows in tables.items():
            file_name = self.schema["datasets"][dataset_name]["file_name"]
            field_names = [
                field["name"] for field in self.schema["datasets"][dataset_name]["fields"]
            ]
            self._write_csv(directory / file_name, field_names, rows)

    def _write_sample_tables(self, directory: Path, tables: Tables) -> None:
        for dataset_name, rows in tables.items():
            file_name = self.schema["datasets"][dataset_name]["file_name"]
            field_names = [
                field["name"] for field in self.schema["datasets"][dataset_name]["fields"]
            ]
            self._write_csv(
                directory / file_name,
                field_names,
                rows[: self.config.sample_rows_per_dataset],
            )

    def _write_invalid_examples(
        self,
        output_directory: Path,
        sample_directory: Path,
    ) -> list[dict[str, Any]]:
        invalid_tables, manifest = self._invalid_examples()
        for root in (output_directory / "invalid", sample_directory / "invalid"):
            root.mkdir(parents=True, exist_ok=True)
            for dataset_name, rows in invalid_tables.items():
                file_name = self.schema["datasets"][dataset_name]["file_name"]
                field_names = [
                    field["name"] for field in self.schema["datasets"][dataset_name]["fields"]
                ]
                self._write_csv(root / file_name, field_names, rows)
            self._write_json(root / "invalid_manifest.json", {"scenarios": manifest})
        return manifest

    def _invalid_examples(self) -> tuple[Tables, list[dict[str, Any]]]:
        invalid: Tables = {}
        manifest: list[dict[str, Any]] = []

        missing_asset = dict(self.tables["assets"][0])
        missing_asset["asset_id"] = ""
        invalid["assets"] = [missing_asset]
        manifest.append(
            self._invalid_manifest_entry(
                "missing_asset_id",
                "assets",
                1,
                "MISSING_REQUIRED_FIELD",
            )
        )

        invalid_cases: list[Row] = []
        bad_status = dict(self.tables["customer_cases"][0])
        bad_status["case_id"] = "CASE-INVALID-STATUS"
        bad_status["case_status"] = "ESCALATED"
        invalid_cases.append(bad_status)
        manifest.append(
            self._invalid_manifest_entry(
                "invalid_case_status",
                "customer_cases",
                1,
                "INVALID_ENUM_VALUE",
            )
        )

        unknown_customer = dict(self.tables["customer_cases"][1])
        unknown_customer["case_id"] = "CASE-UNKNOWN-CUSTOMER"
        unknown_customer["customer_id"] = "CUST-999999"
        invalid_cases.append(unknown_customer)
        manifest.append(
            self._invalid_manifest_entry(
                "unknown_customer",
                "customer_cases",
                2,
                "UNKNOWN_FOREIGN_KEY",
            )
        )

        impossible_case = dict(self.tables["customer_cases"][2])
        impossible_case["case_id"] = "CASE-INVALID-TIME"
        impossible_case["case_status"] = "RESOLVED"
        created = self._parse_timestamp(impossible_case["created_at"])
        impossible_case["resolved_at"] = self._timestamp(created - timedelta(hours=5))
        impossible_case["closed_at"] = ""
        invalid_cases.append(impossible_case)
        manifest.append(
            self._invalid_manifest_entry(
                "impossible_case_timestamps",
                "customer_cases",
                3,
                "INVALID_TIMESTAMP_ORDER",
            )
        )
        invalid["customer_cases"] = invalid_cases

        duplicate_order = dict(self.tables["service_orders"][0])
        invalid["service_orders"] = [duplicate_order]
        manifest.append(
            self._invalid_manifest_entry(
                "duplicate_service_order",
                "service_orders",
                1,
                "DUPLICATE_BUSINESS_KEY",
            )
        )

        negative_cost = dict(self.tables["service_costs"][0])
        negative_cost["service_cost_id"] = "COST-INVALID-NEGATIVE"
        negative_cost["cost_amount_eur"] = "-150.00"
        invalid["service_costs"] = [negative_cost]
        manifest.append(
            self._invalid_manifest_entry(
                "negative_service_cost",
                "service_costs",
                1,
                "NEGATIVE_MONETARY_VALUE",
            )
        )

        malformed_note = dict(self.tables["technician_notes"][0])
        malformed_note["note_id"] = "NOTE-INVALID-EMPTY"
        malformed_note["note_text"] = ""
        invalid["technician_notes"] = [malformed_note]
        manifest.append(
            self._invalid_manifest_entry(
                "empty_technician_note",
                "technician_notes",
                1,
                "MALFORMED_TEXT",
            )
        )

        return invalid, manifest

    def _build_summary(self, invalid_manifest: list[dict[str, Any]]) -> dict[str, Any]:
        delayed_lines = sum(
            1
            for row in self.tables["service_order_parts"]
            if row["delivered_at"]
            and self._parse_timestamp(row["delivered_at"])
            > self._parse_timestamp(row["required_at"])
        )
        linked_alerts = sum(1 for row in self.tables["equipment_alerts"] if row["related_case_id"])
        return {
            "schema_version": self.schema["schema_version"],
            "configuration": self.config.as_manifest_dict(),
            "row_counts": {name: len(rows) for name, rows in sorted(self.tables.items())},
            "quality_signals": {
                "delayed_part_lines": delayed_lines,
                "alerts_linked_to_cases": linked_alerts,
                "invalid_example_scenarios": len(invalid_manifest),
            },
        }

    def _write_manifest(self, root: Path, path: Path) -> None:
        files: list[dict[str, str]] = []
        for file_path in sorted(root.rglob("*")):
            if not file_path.is_file() or file_path == path:
                continue
            files.append(
                {
                    "path": file_path.relative_to(root).as_posix(),
                    "sha256": hashlib.sha256(file_path.read_bytes()).hexdigest(),
                }
            )
        self._write_json(
            path,
            {
                "configuration": self.config.as_manifest_dict(),
                "files": files,
            },
        )

    def _cost_row(
        self,
        index: int,
        order: Row,
        cost_type: str,
        amount: float,
        recorded_at: datetime,
    ) -> Row:
        return {
            "service_cost_id": self._identifier("COST", index),
            "service_order_id": order["service_order_id"],
            "cost_type": cost_type,
            "cost_amount_eur": self._money(amount),
            "cost_recorded_at": self._timestamp(recorded_at),
        }

    def _invalid_manifest_entry(
        self,
        scenario_id: str,
        dataset: str,
        row_number: int,
        expected_code: str,
    ) -> dict[str, Any]:
        return {
            "scenario_id": scenario_id,
            "dataset": dataset,
            "file_name": self.schema["datasets"][dataset]["file_name"],
            "row_number": row_number,
            "expected_code": expected_code,
        }

    def _case_status(self, created: datetime) -> str:
        age_days = (self.config.reporting_as_of - created).days
        if age_days > 120:
            return self.rng.choices(
                ["CLOSED", "RESOLVED", "CANCELLED", "IN_PROGRESS", "WAITING_PARTS"],
                weights=[0.70, 0.12, 0.05, 0.07, 0.06],
                k=1,
            )[0]
        if age_days > 30:
            return self.rng.choices(
                ["CLOSED", "RESOLVED", "IN_PROGRESS", "WAITING_PARTS", "ASSIGNED"],
                weights=[0.42, 0.16, 0.20, 0.14, 0.08],
                k=1,
            )[0]
        return self.rng.choices(
            ["OPEN", "ASSIGNED", "IN_PROGRESS", "WAITING_PARTS", "RESOLVED", "CLOSED"],
            weights=[0.18, 0.20, 0.30, 0.14, 0.12, 0.06],
            k=1,
        )[0]

    def _case_priority(self, case_type: str, asset: Row | None) -> str:
        if case_type == "GENERAL_ENQUIRY":
            return self.rng.choices(["LOW", "MEDIUM"], weights=[0.75, 0.25], k=1)[0]
        criticality = asset["criticality"] if asset is not None else "MEDIUM"
        weights = {
            "LOW": [0.48, 0.38, 0.12, 0.02],
            "MEDIUM": [0.22, 0.48, 0.25, 0.05],
            "HIGH": [0.08, 0.30, 0.45, 0.17],
            "CRITICAL": [0.03, 0.16, 0.42, 0.39],
        }[criticality]
        return self.rng.choices(["LOW", "MEDIUM", "HIGH", "CRITICAL"], weights=weights, k=1)[0]

    def _fault_category(self, case_type: str, asset: Row | None) -> str:
        if case_type == "GENERAL_ENQUIRY":
            return ""
        if case_type == "INSPECTION_REQUEST":
            return "INSPECTION"
        if case_type == "MAINTENANCE_REQUEST":
            return self.rng.choice(["LUBRICATION", "INSPECTION", "OTHER"])
        asset_type = asset["asset_type"] if asset is not None else "COMPRESSOR"
        categories = {
            "GAS_TURBINE": ["OVERHEATING", "VIBRATION", "CONTROL_SYSTEM", "ELECTRICAL", "SEAL"],
            "STEAM_TURBINE": ["VIBRATION", "BEARING", "SEAL", "LUBRICATION", "CONTROL_SYSTEM"],
            "COMPRESSOR": ["VIBRATION", "BEARING", "PRESSURE", "SEAL", "LUBRICATION"],
            "INDUSTRIAL_PUMP": ["FLOW", "PRESSURE", "SEAL", "BEARING", "ELECTRICAL"],
        }
        return self.rng.choice(categories[asset_type])

    def _case_sla_hours(self, priority: str, contract: Row | None) -> tuple[int, int]:
        if contract is not None:
            base_response = int(contract["response_sla_hours"])
            base_resolution = int(contract["resolution_sla_hours"])
        else:
            base_response = 24
            base_resolution = 168
        factors = {"LOW": 1.0, "MEDIUM": 0.75, "HIGH": 0.40, "CRITICAL": 0.20}
        factor = factors[priority]
        return max(1, round(base_response * factor)), max(4, round(base_resolution * factor))

    def _resolution_hours(self, priority: str, fault_category: str) -> float:
        base = {
            "LOW": 96.0,
            "MEDIUM": 60.0,
            "HIGH": 38.0,
            "CRITICAL": 20.0,
        }[priority]
        multiplier = {
            "BEARING": 1.35,
            "VIBRATION": 1.15,
            "OVERHEATING": 1.20,
            "LUBRICATION": 0.75,
            "SEAL": 1.10,
            "ELECTRICAL": 1.05,
            "CONTROL_SYSTEM": 1.25,
            "PRESSURE": 0.95,
            "FLOW": 0.90,
            "INSPECTION": 0.55,
            "OTHER": 1.00,
            "": 0.45,
        }[fault_category]
        return max(1.0, base * multiplier * self.rng.uniform(0.35, 2.4))

    def _order_type(self, case: Row) -> str:
        if case["case_type"] == "INSPECTION_REQUEST":
            return "INSPECTION"
        if case["case_type"] == "MAINTENANCE_REQUEST":
            return "PREVENTIVE_MAINTENANCE"
        if case["priority"] == "CRITICAL":
            return "EMERGENCY_REPAIR"
        return "CORRECTIVE_REPAIR"

    def _order_status(self, case: Row | None) -> str:
        if case is not None and case["case_status"] in {"RESOLVED", "CLOSED"}:
            return self.rng.choices(["COMPLETED", "CANCELLED"], weights=[0.96, 0.04], k=1)[0]
        return self.rng.choices(
            ["PLANNED", "DISPATCHED", "IN_PROGRESS", "COMPLETED", "CANCELLED"],
            weights=[0.12, 0.13, 0.20, 0.50, 0.05],
            k=1,
        )[0]

    def _order_duration_hours(self, order_type: str, delay_propensity: float) -> float:
        base = {
            "INSPECTION": 6.0,
            "PREVENTIVE_MAINTENANCE": 12.0,
            "CORRECTIVE_REPAIR": 24.0,
            "EMERGENCY_REPAIR": 36.0,
        }[order_type]
        return max(1.0, base * self.rng.uniform(0.5, 1.8) + delay_propensity * 120)

    def _choose_technician(self, technicians: list[Row], fault: str, region: str) -> Row:
        desired = {
            "ELECTRICAL": "ELECTRICAL",
            "CONTROL_SYSTEM": "CONTROLS",
            "PRESSURE": "INSTRUMENTATION",
            "FLOW": "INSTRUMENTATION",
        }.get(fault, "ROTATING_EQUIPMENT")
        weights = []
        for technician in technicians:
            weight = 1.0
            if technician["specialisation"] == desired:
                weight += 4.0
            if technician["home_region"] == region:
                weight += 2.0
            if technician["technician_status"] == "INACTIVE":
                weight *= 0.05
            weights.append(weight)
        return self.rng.choices(technicians, weights=weights, k=1)[0]

    def _part_category_for_fault(self, fault: str) -> str:
        return {
            "BEARING": "BEARING",
            "VIBRATION": "BEARING",
            "OVERHEATING": "LUBRICATION",
            "LUBRICATION": "LUBRICATION",
            "SEAL": "SEAL",
            "ELECTRICAL": "ELECTRICAL",
            "CONTROL_SYSTEM": "CONTROL",
            "PRESSURE": "VALVE",
            "FLOW": "FILTER",
            "INSPECTION": "FASTENER",
            "OTHER": "OTHER",
        }.get(fault, "OTHER")

    def _alert_type_for_case_or_asset(self, case: Row | None, asset: Row) -> str:
        if case is not None:
            mapping = {
                "BEARING": "VIBRATION",
                "VIBRATION": "VIBRATION",
                "OVERHEATING": "TEMPERATURE",
                "LUBRICATION": "LUBRICATION",
                "SEAL": "PRESSURE",
                "ELECTRICAL": "ELECTRICAL",
                "CONTROL_SYSTEM": "CONTROL_SYSTEM",
                "PRESSURE": "PRESSURE",
                "FLOW": "FLOW",
            }
            if case["fault_category"] in mapping:
                return mapping[case["fault_category"]]
        defaults = {
            "GAS_TURBINE": ["TEMPERATURE", "VIBRATION", "CONTROL_SYSTEM", "ELECTRICAL"],
            "STEAM_TURBINE": ["VIBRATION", "TEMPERATURE", "LUBRICATION", "PRESSURE"],
            "COMPRESSOR": ["VIBRATION", "PRESSURE", "TEMPERATURE", "LUBRICATION"],
            "INDUSTRIAL_PUMP": ["FLOW", "PRESSURE", "VIBRATION", "ELECTRICAL"],
        }
        return self.rng.choice(defaults[asset["asset_type"]])

    def _alert_severity(self, asset: Row, case: Row | None) -> str:
        if case is not None and case["priority"] == "CRITICAL":
            return self.rng.choices(["WARNING", "CRITICAL"], weights=[0.25, 0.75], k=1)[0]
        weights = {
            "LOW": [0.62, 0.33, 0.05],
            "MEDIUM": [0.45, 0.45, 0.10],
            "HIGH": [0.25, 0.55, 0.20],
            "CRITICAL": [0.14, 0.50, 0.36],
        }[asset["criticality"]]
        return self.rng.choices(["INFO", "WARNING", "CRITICAL"], weights=weights, k=1)[0]

    def _measurement(self, alert_type: str, severity: str) -> tuple[float, float, str]:
        settings = {
            "VIBRATION": (7.1, "mm/s"),
            "TEMPERATURE": (95.0, "degC"),
            "PRESSURE": (18.0, "bar"),
            "FLOW": (420.0, "m3/h"),
            "LUBRICATION": (2.4, "bar"),
            "ELECTRICAL": (58.0, "A"),
            "CONTROL_SYSTEM": (1.0, "state"),
        }
        threshold, unit = settings[alert_type]
        factor_ranges = {
            "INFO": (0.75, 0.98),
            "WARNING": (1.00, 1.25),
            "CRITICAL": (1.25, 1.80),
        }
        low, high = factor_ranges[severity]
        return threshold, threshold * self.rng.uniform(low, high), unit

    def _alert_status(self, age_hours: float, severity: str) -> str:
        if age_hours < 24:
            return self.rng.choices(
                ["OPEN", "ACKNOWLEDGED", "CLEARED"],
                weights=[0.50, 0.35, 0.15],
                k=1,
            )[0]
        if severity == "CRITICAL":
            return self.rng.choices(
                ["OPEN", "ACKNOWLEDGED", "CLEARED"],
                weights=[0.08, 0.20, 0.72],
                k=1,
            )[0]
        return self.rng.choices(
            ["OPEN", "ACKNOWLEDGED", "CLEARED"],
            weights=[0.03, 0.12, 0.85],
            k=1,
        )[0]

    def _note_text(self, note_type: str, fault: str, asset_type: str, resolution_code: str) -> str:
        component = {
            "BEARING": "drive-end bearing",
            "VIBRATION": "rotor and bearing assembly",
            "OVERHEATING": "thermal protection circuit",
            "LUBRICATION": "lubrication system",
            "SEAL": "shaft seal",
            "ELECTRICAL": "motor terminal assembly",
            "CONTROL_SYSTEM": "control cabinet",
            "PRESSURE": "pressure regulation valve",
            "FLOW": "flow path and filter",
            "INSPECTION": "external casing and mounts",
            "OTHER": "serviceable assembly",
        }.get(fault, "serviceable assembly")
        fault_label = fault.replace("_", " ").lower()
        asset_label = asset_type.replace("_", " ").lower()
        resolution_label = resolution_code or "NOT_RECORDED"
        templates = {
            "INSPECTION": [
                (
                    f"Inspected the {component} on the {asset_label}. "
                    "No unsafe access conditions were found. "
                    f"The main observation was {fault_label} outside the usual "
                    "operating range."
                ),
                (
                    "Visual and functional inspection completed. "
                    f"The {component} showed signs consistent with {fault_label}; "
                    "readings were recorded for follow-up."
                ),
            ],
            "DIAGNOSIS": [
                (
                    f"The {fault_label} condition was reproduced during the test run. "
                    f"Checks point to the {component} rather than an upstream "
                    "process change."
                ),
                (
                    f"Measurements confirmed abnormal {fault_label}. "
                    f"The {component} should be serviced before the next extended "
                    "operating cycle."
                ),
            ],
            "REPAIR": [
                (
                    f"Serviced the {component}, replaced worn consumables where "
                    "required, and repeated the operating checks. "
                    f"The {fault_label} reading returned toward the expected range."
                ),
                (
                    f"Repair work completed on the {component}. Fasteners, "
                    "connections, and alignment were checked before restart."
                ),
            ],
            "COMPLETION": [
                (
                    f"Service order completed with resolution code {resolution_label}. "
                    "The equipment was returned to the agreed operating state and "
                    "the customer contact was informed."
                ),
                (
                    f"Final checks completed after work on the {component}. "
                    f"No immediate recurrence of the {fault_label} condition was "
                    "observed."
                ),
            ],
        }
        return self.rng.choice(templates[note_type])

    def _status_reason(self, status: str) -> str:
        reasons = {
            "OPEN": "Case created from source request.",
            "ASSIGNED": "Case assigned to the service team.",
            "IN_PROGRESS": "Technical work started.",
            "WAITING_PARTS": "Work paused while required parts are obtained.",
            "RESOLVED": "Technical resolution recorded.",
            "CLOSED": "Customer case closed after resolution.",
            "CANCELLED": "Request withdrawn or no longer required.",
        }
        return reasons[status]

    def _contract_for_date(self, contracts: list[Row], target_date: date) -> Row | None:
        eligible = [
            row
            for row in contracts
            if (
                date.fromisoformat(row["start_date"])
                <= target_date
                <= date.fromisoformat(row["end_date"])
            )
            and row["contract_status"] != "CANCELLED"
        ]
        return self.rng.choice(eligible) if eligible else None

    def _asset_event_weight(self, asset: Row) -> float:
        installed = date.fromisoformat(asset["installation_date"])
        age_years = max(0.0, (self.config.reporting_as_of.date() - installed).days / 365.25)
        criticality = {
            "LOW": 0.8,
            "MEDIUM": 1.1,
            "HIGH": 1.6,
            "CRITICAL": 2.2,
        }[asset["criticality"]]
        status = 0.35 if asset["asset_status"] == "RETIRED" else 1.0
        return (1.0 + age_years / 8.0) * criticality * status

    def _duration_hours(self, start: str, end: str) -> float:
        if not start or not end:
            return 0.0
        return max(
            0.0,
            (self._parse_timestamp(end) - self._parse_timestamp(start)).total_seconds() / 3600,
        )

    def _prepare_directory(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        for child in path.iterdir():
            if child.name == ".gitkeep":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

    def _resolve(self, path: Path) -> Path:
        return path if path.is_absolute() else self.project_root / path

    @staticmethod
    def _identifier(prefix: str, index: int) -> str:
        return f"{prefix}-{index:06d}"

    @staticmethod
    def _timestamp(value: datetime) -> str:
        return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError(f"Expected timezone-aware timestamp: {value}")
        return parsed.astimezone(UTC)

    def _random_datetime(self, start: datetime, end: datetime) -> datetime:
        if end <= start:
            return start
        seconds = int((end - start).total_seconds())
        return start + timedelta(seconds=self.rng.randint(0, seconds))

    def _random_date(self, start: date, end: date) -> date:
        if end <= start:
            return start
        return start + timedelta(days=self.rng.randint(0, (end - start).days))

    @staticmethod
    def _money(value: float) -> str:
        return str(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    @staticmethod
    def _decimal6(value: float) -> str:
        return str(Decimal(str(value)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))

    @staticmethod
    def _index(rows: Iterable[Row], field: str) -> dict[str, Row]:
        return {row[field]: row for row in rows}

    @staticmethod
    def _group(rows: Iterable[Row], field: str) -> dict[str, list[Row]]:
        grouped: dict[str, list[Row]] = {}
        for row in rows:
            grouped.setdefault(row[field], []).append(row)
        return grouped

    @staticmethod
    def _find(rows: Iterable[Row], field: str, value: str) -> Row:
        for row in rows:
            if row[field] == value:
                return row
        raise KeyError(f"No row found where {field}={value}")

    @staticmethod
    def _write_csv(path: Path, field_names: list[str], rows: list[Row]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=field_names, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    @staticmethod
    def _write_json(path: Path, content: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(content, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def customer_creation_date(customer: Row) -> date:
    """Return the UTC date on which a customer source record was created."""
    return datetime.fromisoformat(customer["created_at"].replace("Z", "+00:00")).date()
