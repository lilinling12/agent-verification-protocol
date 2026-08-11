"""AVP → OpenTelemetry correlation helpers.

No hard dependency on the OTel SDK is required for the reference core.
"""
def avp_attributes(*, episode_id: str, scenario_digest: str | None = None,
                   environment_digest: str | None = None) -> dict[str, str]:
    attrs = {"avp.episode.id": episode_id}
    if scenario_digest:
        attrs["avp.scenario.digest"] = scenario_digest
    if environment_digest:
        attrs["avp.environment.digest"] = environment_digest
    return attrs

def state_attributes(before: str | None, after: str | None) -> dict[str, str]:
    attrs = {}
    if before:
        attrs["avp.state.before.digest"] = before
    if after:
        attrs["avp.state.after.digest"] = after
    return attrs
