function generateId(length = 16) {
    const chars = "0123456789abcdef";
    let result = "";
    for (let i = 0; i < length; i++) {
        result += chars[Math.floor(Math.random() * chars.length)];
    }
    return result;
}
export class SpanManager {
    activeSpans = new Map();
    sessionTraceMap = new Map();
    turnSpanMap = new Map();
    generateTraceId() {
        return generateId(32);
    }
    generateSpanId() {
        return generateId(16);
    }
    getOrCreateTraceId(sessionId) {
        let traceId = this.sessionTraceMap.get(sessionId);
        if (!traceId) {
            traceId = this.generateTraceId();
            this.sessionTraceMap.set(sessionId, traceId);
        }
        return traceId;
    }
    startSpan(sessionId, name, type, attributes = {}, input, parentSpanId) {
        const traceId = this.getOrCreateTraceId(sessionId);
        const spanId = this.generateSpanId();
        const span = {
            name,
            type,
            startTime: Date.now(),
            attributes: {
                ...attributes,
                "session.id": sessionId,
            },
            input,
            parentSpanId,
            traceId,
            spanId,
        };
        this.activeSpans.set(spanId, span);
        return span;
    }
    endSpan(spanId, output, additionalAttributes) {
        const span = this.activeSpans.get(spanId);
        if (!span)
            return undefined;
        span.endTime = Date.now();
        span.output = output;
        if (additionalAttributes) {
            Object.assign(span.attributes, additionalAttributes);
        }
        this.activeSpans.delete(spanId);
        return span;
    }
    getSpan(spanId) {
        return this.activeSpans.get(spanId);
    }
    setTurnSpan(turnId, spanId) {
        this.turnSpanMap.set(turnId, spanId);
    }
    getTurnSpanId(turnId) {
        return this.turnSpanMap.get(turnId);
    }
    clearSession(sessionId) {
        this.sessionTraceMap.delete(sessionId);
        for (const [turnId, spanId] of this.turnSpanMap.entries()) {
            const span = this.activeSpans.get(spanId);
            if (span && span.attributes["session.id"] === sessionId) {
                this.turnSpanMap.delete(turnId);
                this.activeSpans.delete(spanId);
            }
        }
    }
}
//# sourceMappingURL=span-manager.js.map