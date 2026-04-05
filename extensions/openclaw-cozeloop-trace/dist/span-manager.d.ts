import type { SpanData, SpanType } from "./types.js";
export declare class SpanManager {
    private activeSpans;
    private sessionTraceMap;
    private turnSpanMap;
    generateTraceId(): string;
    generateSpanId(): string;
    getOrCreateTraceId(sessionId: string): string;
    startSpan(sessionId: string, name: string, type: SpanType, attributes?: Record<string, string | number | boolean>, input?: unknown, parentSpanId?: string): SpanData;
    endSpan(spanId: string, output?: unknown, additionalAttributes?: Record<string, string | number | boolean>): SpanData | undefined;
    getSpan(spanId: string): SpanData | undefined;
    setTurnSpan(turnId: string, spanId: string): void;
    getTurnSpanId(turnId: string): string | undefined;
    clearSession(sessionId: string): void;
}
//# sourceMappingURL=span-manager.d.ts.map