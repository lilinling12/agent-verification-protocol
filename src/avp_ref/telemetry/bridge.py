"""OpenTelemetry implementation of AVP telemetry correlation."""
from __future__ import annotations
from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable
from avp_ref.models import AVPEvent
from .models import TelemetryArtifact,TelemetryCompleteness,TelemetryDescription,TelemetryPolicy
_TERMINAL_EVENTS=frozenset({"episode.completed","episode.invalid","episode.resources.released"})
_SAFE_PAYLOAD_KEYS=frozenset({"manifest_digest","scenario_instance_digest","agent_system_digest","environment_adapter_digest","subject_adapter_digest","mcp_gateway_config_digest","telemetry_config_digest","gateway_digest","server_digest","catalog_digest","protocol_version","adapter","handle_id","target","equivalent_to_initial","status","steps","error_type","claim_id","dimension","verdict","severity","method","evaluator_version","task_verdict","validity","snapshot_id","consistency","equivalence","fault_id","type","occurrence","visibility","name","protocol","correlation_id","schema_digest","result_digest"})

@runtime_checkable
class TelemetrySession(Protocol):
    @property
    def artifact(self)->TelemetryArtifact|None: ...
    def record_event(self,event:AVPEvent)->None: ...
    def inject_headers(self)->Mapping[str,str]: ...
    def finalize(self,*,complete:bool=True)->TelemetryArtifact: ...
@runtime_checkable
class TelemetryBridge(Protocol):
    def describe(self)->TelemetryDescription: ...
    def start_episode(self,episode_id:str,manifest_digest:str)->TelemetrySession: ...

class _NoopSession:
    def __init__(self,episode_id,required): self._episode_id=episode_id; self._required=required; self._events=0; self._artifact=None
    @property
    def artifact(self): return self._artifact
    def record_event(self,event): self._events+=1
    def inject_headers(self): return {}
    def finalize(self,*,complete=True):
        if self._artifact is None:
            c=TelemetryCompleteness.REQUIRED_MISSING if self._required else TelemetryCompleteness.BEST_EFFORT
            self._artifact=TelemetryArtifact(self._episode_id,None,None,self._events,0,c,0)
        return self._artifact
class NoopTelemetryBridge:
    def __init__(self,policy=None): self._policy=policy or TelemetryPolicy(); self._description=TelemetryDescription("noop-telemetry","0.1.0","none",self._policy)
    def describe(self): return self._description
    def start_episode(self,episode_id,manifest_digest): return _NoopSession(episode_id,self._policy.required)

class _OpenTelemetrySession:
    def __init__(self,episode_id,manifest_digest,tracer,exporter,policy):
        from opentelemetry import trace
        self._trace=trace; self._episode_id=episode_id; self._tracer=tracer; self._exporter=exporter; self._policy=policy
        self._root=tracer.start_span("avp.episode",attributes={"avp.episode.id":episode_id,"avp.manifest.digest":manifest_digest}); self._context=trace.set_span_in_context(self._root)
        self._events=0; self._propagated=0; self._artifact=None; self._open_spans={}
    @property
    def artifact(self): return self._artifact
    def _safe(self,v):
        if isinstance(v,(bool,int,float)): return v
        return str(v)[:self._policy.max_attribute_length]
    def _attrs(self,event):
        a={"avp.event.id":event.event_id,"avp.event.type":event.event_type,"avp.event.sequence":event.sequence,"avp.plane":event.plane,"avp.logical_time":event.logical_time}
        for k,v in event.payload.items():
            if k in _SAFE_PAYLOAD_KEYS and v is not None and not isinstance(v,(Mapping,list,tuple)): a[f"avp.{k}"]=self._safe(v)
        return a
    def record_event(self,event):
        if self._artifact is not None:return
        self._events+=1; attrs=self._attrs(event); self._root.add_event(f"avp.{event.event_type}",attrs); cid=str(event.payload.get("correlation_id") or "")
        if event.event_type=="tool.call" and cid:
            from opentelemetry.trace import SpanKind
            self._open_spans[cid]=self._tracer.start_span(f"avp.tool {event.payload.get('name','unknown')}",context=self._context,kind=SpanKind.CLIENT,attributes={"avp.correlation_id":cid,"avp.tool.name":str(event.payload.get("name","unknown")),"avp.tool.protocol":str(event.payload.get("protocol","unknown"))})
        elif event.event_type in {"tool.result","tool.error"} and cid:
            span=self._open_spans.pop(cid,None)
            if span is not None:
                if event.event_type=="tool.error":
                    from opentelemetry.trace import Status,StatusCode
                    span.set_status(Status(StatusCode.ERROR,str(event.payload.get("error_type") or "tool error")))
                span.end()
        if event.event_type in _TERMINAL_EVENTS:self.finalize(complete=True)
    def inject_headers(self):
        from opentelemetry.propagate import inject
        carrier={}; inject(carrier,context=self._context); self._propagated+=1; return carrier
    def finalize(self,*,complete=True):
        if self._artifact is not None:return self._artifact
        for s in self._open_spans.values():s.end()
        self._open_spans.clear(); ctx=self._root.get_span_context(); self._root.end()
        all_spans=tuple(self._exporter.get_finished_spans()) if self._exporter is not None else ()
        spans=tuple(s for s in all_spans if s.context.trace_id==ctx.trace_id)
        c=TelemetryCompleteness.COMPLETE if complete else TelemetryCompleteness.INCOMPLETE
        if self._policy.required and (not ctx.is_valid or not spans):c=TelemetryCompleteness.REQUIRED_MISSING
        self._artifact=TelemetryArtifact(self._episode_id,f"{ctx.trace_id:032x}" if ctx.is_valid else None,f"{ctx.span_id:016x}" if ctx.is_valid else None,self._events,self._propagated,c,len(spans)); return self._artifact

class OpenTelemetryBridge:
    def __init__(self,policy=None):
        self._policy=policy or TelemetryPolicy()
        try:
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import SimpleSpanProcessor
            from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
        except ImportError as exc: raise RuntimeError("Install avp-reference[otel] to use OpenTelemetryBridge") from exc
        self._exporter=InMemorySpanExporter(); self._provider=TracerProvider(resource=Resource.create({"service.name":"avp-reference"})); self._provider.add_span_processor(SimpleSpanProcessor(self._exporter)); self._tracer=self._provider.get_tracer("avp.reference","0.2.0-alpha.5"); self._description=TelemetryDescription("opentelemetry","0.2.0-alpha.5","otel-sdk",self._policy)
    def describe(self): return self._description
    def start_episode(self,episode_id,manifest_digest): return _OpenTelemetrySession(episode_id,manifest_digest,self._tracer,self._exporter,self._policy)
    def finished_spans(self): return tuple(self._exporter.get_finished_spans())
