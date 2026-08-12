# Reference Adapter Boundary

`adapters/` defines the distribution boundary for open-source integrations between AVP and external systems.

During Alpha, implementations remain under `src/avp_ref/` to keep packaging changes separate from repository-boundary work.

Examples include Subject adapters, Environment adapters, MCP verification integrations, and future database/browser/container/network adapters.

Adapters implement AVP contracts. Vendor-specific integration needs must not silently become AVP Core semantics. Commercial Environment Fabric implementations may stay outside this repository while implementing the same public contracts and conformance requirements.
