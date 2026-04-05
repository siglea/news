import { trace, context, SpanKind, SpanStatusCode } from "@opentelemetry/api";
import { BasicTracerProvider, BatchSpanProcessor } from "@opentelemetry/sdk-trace-base";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-proto";
import { Resource } from "@opentelemetry/resources";
import { ATTR_SERVICE_NAME, ATTR_SERVICE_INSTANCE_ID } from "@opentelemetry/semantic-conventions";
import { hostname } from "os";
import { basename } from "path";
export class CozeloopExporter {
    config;
    api;
    provider = null;
    tracer = null;
    initialized = false;
    initPromise = null;
    currentRootSpan = null;
    currentRootContext = null;
    currentAgentSpan = null;
    currentAgentContext = null;
    openSpans = new Map();
    constructor(api, config) {
        this.api = api;
        this.config = config;
    }
    async ensureInitialized() {
        if (this.initialized)
            return;
        if (this.initPromise)
            return this.initPromise;
        this.initPromise = this.initialize();
        await this.initPromise;
    }
    async initialize() {
        this.api.logger.info(`[CozeloopTrace] Initializing exporter...`);
        const instanceName = this.config.serviceName || basename(process.cwd()) || "openclaw-agent";
        const instanceId = `${instanceName}@${hostname()}:${process.pid}`;
        const resource = new Resource({
            [ATTR_SERVICE_NAME]: this.config.serviceName,
            [ATTR_SERVICE_INSTANCE_ID]: instanceId,
            "host.name": hostname(),
        });
        const authorization = this.config.authorization;
        const workspaceId = this.config.workspaceId;
        this.api.logger.info(`[CozeloopTrace] Using authorization, workspaceId=${workspaceId}, tokenLength=${authorization?.length}`);
        const exporter = new OTLPTraceExporter({
            url: `${this.config.endpoint}/v1/traces`,
            headers: {
                "Authorization": authorization,
                "cozeloop-workspace-id": workspaceId,
            },
        });
        this.provider = new BasicTracerProvider({ resource });
        this.provider.addSpanProcessor(new BatchSpanProcessor(exporter, {
            maxQueueSize: 100,
            maxExportBatchSize: this.config.batchSize || 10,
            scheduledDelayMillis: this.config.batchInterval || 5000,
        }));
        this.provider.register();
        this.tracer = trace.getTracer("openclaw-cozeloop-trace", "0.1.0");
        this.initialized = true;
        this.api.logger.info(`[CozeloopTrace] Exporter initialized with Authorization, workspaceId=${workspaceId}`);
    }
    async startSpan(spanData, spanId) {
        try {
            await this.ensureInitialized();
            this.doStartSpan(spanData, spanId);
        }
        catch (err) {
            this.api.logger.error(`[CozeloopTrace] Failed to start span: ${err}`);
        }
    }
    doStartSpan(spanData, spanId) {
        if (!this.tracer)
            return;
        const spanKind = this.getSpanKind(spanData.type);
        const isRoot = !spanData.parentSpanId;
        const isAgent = spanData.type === "agent";
        let parentContext;
        if (isRoot) {
            this.currentRootSpan = null;
            this.currentRootContext = null;
            this.currentAgentSpan = null;
            this.currentAgentContext = null;
            parentContext = context.active();
        }
        else if (isAgent) {
            parentContext = this.currentRootContext || context.active();
        }
        else {
            parentContext = this.currentAgentContext || this.currentRootContext || context.active();
        }
        const runtimeTag = {
            language: "nodejs",
            library: "openclaw",
        };
        if (process.env.COZELOOP_SCENE) {
            runtimeTag.scene = process.env.COZELOOP_SCENE;
        }
        const systemTagRuntime = JSON.stringify(runtimeTag);
        const span = this.tracer.startSpan(spanData.name, {
            kind: spanKind,
            startTime: spanData.startTime,
            attributes: {
                "cozeloop.span_type": spanData.type,
                "cozeloop.system_tag_runtime": systemTagRuntime,
                ...this.flattenAttributes(spanData.attributes),
            },
        }, parentContext);
        if (isRoot) {
            this.currentRootSpan = span;
            this.currentRootContext = trace.setSpan(context.active(), span);
            if (this.config.debug) {
                const sc = span.spanContext();
                this.api.logger.info(`[CozeloopTrace] Created ROOT span: name=${spanData.name}, traceId=${sc.traceId}, spanId=${sc.spanId}`);
            }
        }
        if (isAgent) {
            this.currentAgentSpan = span;
            this.currentAgentContext = trace.setSpan(this.currentRootContext || context.active(), span);
            if (this.config.debug) {
                const sc = span.spanContext();
                this.api.logger.info(`[CozeloopTrace] Created AGENT span: name=${spanData.name}, traceId=${sc.traceId}, spanId=${sc.spanId}`);
            }
        }
        this.setSpanInputOutput(span, spanData);
        this.openSpans.set(spanId, span);
        if (this.config.debug && !isRoot && !isAgent) {
            const spanContext = span.spanContext();
            this.api.logger.info(`[CozeloopTrace] Started span: name=${spanData.name}, type=${spanData.type}, ` +
                `traceId=${spanContext.traceId}, spanId=${spanContext.spanId}`);
        }
    }
    endSpanById(spanId, endTime, additionalAttrs, output, input) {
        const span = this.openSpans.get(spanId);
        if (!span) {
            if (this.config.debug) {
                this.api.logger.info(`[CozeloopTrace] Span not found for ending: spanId=${spanId}`);
            }
            return;
        }
        if (additionalAttrs) {
            for (const [key, value] of Object.entries(additionalAttrs)) {
                if (value !== undefined && value !== null) {
                    span.setAttribute(key, value);
                }
            }
        }
        if (input !== undefined) {
            const inputStr = typeof input === "string" ? input : JSON.stringify(input);
            span.setAttribute("cozeloop.input", inputStr.substring(0, 3200000));
        }
        if (output !== undefined) {
            const outputStr = typeof output === "string" ? output : JSON.stringify(output);
            span.setAttribute("cozeloop.output", outputStr.substring(0, 3200000));
        }
        span.setStatus({ code: SpanStatusCode.OK });
        span.end(endTime || Date.now());
        this.openSpans.delete(spanId);
        if (this.config.debug) {
            const sc = span.spanContext();
            this.api.logger.info(`[CozeloopTrace] Ended span: spanId=${spanId}, traceId=${sc.traceId}`);
        }
    }
    async export(spanData) {
        await this.ensureInitialized();
        if (!this.tracer)
            return;
        const spanKind = this.getSpanKind(spanData.type);
        const isRoot = !spanData.parentSpanId;
        const isAgent = spanData.type === "agent";
        let parentContext;
        if (isRoot) {
            this.currentRootSpan = null;
            this.currentRootContext = null;
            parentContext = context.active();
        }
        else if (isAgent) {
            parentContext = this.currentRootContext || context.active();
        }
        else {
            parentContext = this.currentAgentContext || this.currentRootContext || context.active();
        }
        const runtimeTag = {
            language: "nodejs",
            library: "openclaw",
        };
        if (process.env.COZELOOP_SCENE) {
            runtimeTag.scene = process.env.COZELOOP_SCENE;
        }
        const systemTagRuntime = JSON.stringify(runtimeTag);
        const span = this.tracer.startSpan(spanData.name, {
            kind: spanKind,
            startTime: spanData.startTime,
            attributes: {
                "cozeloop.span_type": spanData.type,
                "cozeloop.system_tag_runtime": systemTagRuntime,
                ...this.flattenAttributes(spanData.attributes),
            },
        }, parentContext);
        if (isRoot) {
            this.currentRootSpan = span;
            this.currentRootContext = trace.setSpan(context.active(), span);
            if (this.config.debug) {
                const sc = span.spanContext();
                this.api.logger.info(`[CozeloopTrace] Created ROOT span: name=${spanData.name}, traceId=${sc.traceId}, spanId=${sc.spanId}`);
            }
        }
        this.setSpanInputOutput(span, spanData);
        const hasError = spanData.attributes["error"] === true || spanData.attributes["tool.error"] === true;
        if (hasError) {
            span.setStatus({ code: SpanStatusCode.ERROR });
        }
        else {
            span.setStatus({ code: SpanStatusCode.OK });
        }
        span.end(spanData.endTime || Date.now());
        if (this.config.debug) {
            const spanContext = span.spanContext();
            this.api.logger.info(`[CozeloopTrace] Created span: name=${spanData.name}, type=${spanData.type}, ` +
                `traceId=${spanContext.traceId}, spanId=${spanContext.spanId}, isRoot=${isRoot}`);
        }
    }
    setSpanInputOutput(span, spanData) {
        if (spanData.input !== undefined) {
            const inputStr = typeof spanData.input === "string"
                ? spanData.input
                : JSON.stringify(spanData.input);
            span.setAttribute("cozeloop.input", inputStr.substring(0, 3200000));
        }
        if (spanData.output !== undefined) {
            const outputStr = typeof spanData.output === "string"
                ? spanData.output
                : JSON.stringify(spanData.output);
            span.setAttribute("cozeloop.output", outputStr.substring(0, 3200000));
        }
    }
    endTrace() {
        this.currentRootSpan = null;
        this.currentRootContext = null;
        this.currentAgentSpan = null;
        this.currentAgentContext = null;
        this.openSpans.clear();
        if (this.config.debug) {
            this.api.logger.info(`[CozeloopTrace] Trace ended, context cleared`);
        }
    }
    getSpanKind(type) {
        switch (type) {
            case "entry":
            case "gateway":
                return SpanKind.SERVER;
            case "model":
                return SpanKind.CLIENT;
            case "tool":
                return SpanKind.CLIENT;
            default:
                return SpanKind.INTERNAL;
        }
    }
    flattenAttributes(attrs) {
        const result = {};
        for (const [key, value] of Object.entries(attrs)) {
            if (value !== undefined && value !== null) {
                result[key] = value;
            }
        }
        return result;
    }
    async flush() {
        if (this.provider) {
            await this.provider.forceFlush();
        }
    }
    async dispose() {
        if (this.provider) {
            await this.provider.shutdown();
        }
    }
}
//# sourceMappingURL=cozeloop-exporter.js.map