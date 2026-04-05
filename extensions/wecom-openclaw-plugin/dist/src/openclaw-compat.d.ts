/**
 * openclaw plugin-sdk 高版本方法兼容层
 *
 * 部分方法（如 loadOutboundMediaFromUrl、detectMime、getDefaultMediaLocalRoots）
 * 仅在较新版本的 openclaw plugin-sdk 中才导出。
 *
 * 本模块在加载时一次性探测 SDK 导出，存在则直接 re-export SDK 版本，
 * 不存在则导出 fallback 实现。其他模块统一从本文件导入，无需关心底层兼容细节。
 */
/** 与 openclaw plugin-sdk 中 WebMediaResult 兼容的类型 */
export type WebMediaResult = {
    buffer: Buffer;
    contentType?: string;
    kind?: string;
    fileName?: string;
};
export type OutboundMediaLoadOptions = {
    maxBytes?: number;
    mediaLocalRoots?: readonly string[];
};
export type DetectMimeOptions = {
    buffer?: Buffer;
    headerMime?: string | null;
    filePath?: string;
};
/**
 * 检测 MIME 类型（兼容入口）
 *
 * 支持两种调用签名以兼容不同使用场景：
 * - detectMime(buffer)           → 旧式调用
 * - detectMime({ buffer, headerMime, filePath }) → 完整参数
 *
 * 优先使用 SDK 版本，不可用时使用 fallback。
 */
export declare function detectMime(bufferOrOpts: Buffer | DetectMimeOptions): Promise<string | undefined>;
/**
 * 从 URL 或本地路径加载媒体文件（兼容入口）
 *
 * 优先使用 SDK 版本，不可用时使用 fallback。
 * SDK 版本抛出的业务异常（如 LocalMediaAccessError）会直接透传。
 */
export declare function loadOutboundMediaFromUrl(mediaUrl: string, options?: OutboundMediaLoadOptions): Promise<WebMediaResult>;
/**
 * 获取默认媒体本地路径白名单（兼容入口）
 *
 * 优先使用 SDK 版本，不可用时手动构建白名单（与 weclaw/src/media/local-roots.ts 逻辑一致）。
 */
export declare function getDefaultMediaLocalRoots(): Promise<readonly string[]>;
