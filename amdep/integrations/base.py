"""Shared integration adapter types.

The Community Edition does not ship authenticated production connectors.
It ships stable contracts and export shapes that make the optimizer easy to
wire into Procore, ServiceTitan, HCSS, Sage, Trimble, Autodesk, AccuLynx, BI
tools, or a customer's internal data lake.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class FieldMapping:
    """Map a contractor-system field into AmDep's normalized ontology."""

    source_field: str
    amdep_field: str
    required: bool = False
    notes: str = ""


@dataclass(frozen=True)
class StackManifest:
    """Integration posture for a known contractor software stack."""

    stack_id: str
    display_name: str
    category: str
    best_first_use: str
    import_surfaces: tuple[str, ...]
    export_surfaces: tuple[str, ...]
    auth_model: str
    data_notes: str
    field_mappings: tuple[FieldMapping, ...] = field(default_factory=tuple)
    source_url: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["field_mappings"] = [asdict(mapping) for mapping in self.field_mappings]
        return payload


class IntegrationAdapterError(RuntimeError):
    """Raised when an adapter cannot produce its export contract."""
