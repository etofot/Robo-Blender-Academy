/**
 * Blender MCP Server - WebSocket Bridge Protocol
 * 
 * Defines message formats for communication with Blender addon.
 */

import { z } from 'zod';

// Request schema
export const BlenderRequestSchema = z.object({
    id: z.string(),
    type: z.enum([
        'ping',
        'get_version',
        'run_script',
        'create_primitive',
        'apply_texture',
        'set_material',
        'get_scene_info',
        'export_model',
        'render_preview',
        'optimize_mesh',
        'generate_procedural',
        'bake_textures',
    ]),
    params: z.record(z.unknown()).optional(),
});

export type BlenderRequest = z.infer<typeof BlenderRequestSchema>;

// Response schema - supports both verbose and compact format
// Verbose: {id, success, data, error}
// Compact: {id, ok, d, e}
export const BlenderResponseSchema = z.object({
    id: z.string(),
    // Support both success (verbose) and ok (compact)
    success: z.boolean().optional(),
    ok: z.union([z.literal(0), z.literal(1)]).optional(),
    // Support both data (verbose) and d (compact)
    data: z.unknown().optional(),
    d: z.unknown().optional(),
    // Support both error formats
    error: z.object({
        code: z.string(),
        message: z.string(),
        suggestion: z.string().optional(),
    }).optional(),
    e: z.object({
        c: z.string(),
        m: z.string(),
    }).optional(),
    _meta: z.object({
        duration_ms: z.number().optional(),
        truncated: z.boolean().optional(),
    }).optional(),
}).transform((raw) => {
    // Normalize to standard format for internal use
    return {
        id: raw.id,
        success: raw.success ?? (raw.ok === 1),
        data: raw.data ?? raw.d,
        error: raw.error ?? (raw.e ? { code: raw.e.c, message: raw.e.m } : undefined),
        _meta: raw._meta,
    };
});

export type BlenderResponse = {
    id: string;
    success: boolean;
    data?: unknown;
    error?: { code: string; message: string; suggestion?: string };
    _meta?: { duration_ms?: number; truncated?: boolean };
};

// Helper to create request
export function createRequest(
    type: BlenderRequest['type'],
    params?: Record<string, unknown>
): BlenderRequest {
    return {
        id: `req_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
        type,
        params,
    };
}

// Helper to create success response
export function createSuccessResponse(
    requestId: string,
    data: unknown,
    meta?: { duration_ms?: number; truncated?: boolean }
): BlenderResponse {
    return {
        id: requestId,
        success: true,
        data,
        _meta: meta,
    };
}

// Helper to create error response
export function createErrorResponse(
    requestId: string,
    code: string,
    message: string,
    suggestion?: string
): BlenderResponse {
    return {
        id: requestId,
        success: false,
        error: {
            code,
            message,
            suggestion,
        },
    };
}
