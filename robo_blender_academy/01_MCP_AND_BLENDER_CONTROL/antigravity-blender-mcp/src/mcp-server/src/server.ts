/**
 * Blender MCP Server - Main Server Setup
 * 
 * Creates and configures the MCP server with all tools.
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import { log } from './utils/logger.js';
import { config } from './utils/config.js';
import { blenderBridge } from './bridge/client.js';
import { createPrimitiveSchema, handleCreatePrimitive } from './tools/primitives.js';
import { exportModelSchema, handleExportModel } from './tools/export.js';
import { applyTextureSchema, handleApplyTexture, setMaterialSchema, handleSetMaterial } from './tools/texture.js';
import { generateProceduralSchema, handleGenerateProcedural } from './tools/procedural.js';
import { optimizeMeshSchema, handleOptimizeMesh } from './tools/optimize.js';
import { renderPreviewSchema, handleRenderPreview } from './tools/render.js';
import { bakeTexturesSchema, handleBakeTextures } from './tools/bake.js';
import { genTexSchema, handleGenTex } from './tools/gentex.js';
import { pipelineSchema, handlePipeline } from './tools/pipeline.js';
import { parseSchema, handleParse } from './tools/parse.js';
import { blueprintSchema, handleBlueprint } from './tools/blueprint.js';
import { sculptSchema, handleSculpt } from './tools/sculpt.js';
import { previewSchema, handlePreview } from './tools/preview.js';

export function createServer(): McpServer {
    log.info('Creating MCP server...', {
        name: config.server.name,
        version: config.server.version
    });

    const server = new McpServer({
        name: config.server.name,
        version: config.server.version,
    });

    // Register tools
    registerTools(server);

    log.info('MCP server created successfully');
    return server;
}

function registerTools(server: McpServer): void {
    log.info('Registering tools...');

    // Tool 1: status - Check Blender connection
    server.tool(
        'status',
        'Check Blender connection. Returns version and status.',
        {},
        async () => {
            log.debug('Executing: status');
            return handleGetBlenderStatus();
        }
    );

    // Tool 2: scene - List objects in scene
    server.tool(
        'scene',
        'List objects in Blender scene with pagination.',
        {
            limit: z.number().min(1).max(100).default(20).describe('Max objects'),
            offset: z.number().min(0).default(0).describe('Offset'),
            type: z.enum(['ALL', 'MESH', 'LIGHT', 'CAMERA', 'EMPTY']).default('ALL').describe('Filter type'),
            v: z.enum(['min', 'std', 'full']).default('std').describe('Verbosity'),
        },
        async (params) => {
            log.debug('Executing: scene', params);
            return handleGetSceneInfo({
                limit: params.limit,
                offset: params.offset,
                filter_type: params.type,
                verbosity: params.v === 'min' ? 'minimal' : params.v === 'full' ? 'detailed' : 'standard',
            });
        }
    );

    // Tool 3: prim - Create primitive shapes
    server.tool(
        'prim',
        'Create 3D primitive (CUBE/SPHERE/CYLINDER/CONE/PLANE/TORUS/MONKEY/CIRCLE/GRID).',
        createPrimitiveSchema,
        async (params) => {
            return handleCreatePrimitive(params);
        }
    );

    // Tool 4: export - Export model to file
    server.tool(
        'export',
        'Export model to FBX/GLB/GLTF/OBJ format.',
        exportModelSchema,
        async (params) => {
            return handleExportModel(params);
        }
    );

    // Tool 5: tex - Apply texture to object
    server.tool(
        'tex',
        'Apply image texture to object. Auto-generates UVs if needed.',
        applyTextureSchema,
        async (params) => {
            return handleApplyTexture(params);
        }
    );

    // Tool 6: mat - Apply material preset
    server.tool(
        'mat',
        'Apply material preset (METALLIC/PLASTIC/GLASS/WOOD/STONE/FABRIC/EMISSIVE/MATTE) with color.',
        setMaterialSchema,
        async (params) => {
            return handleSetMaterial(params);
        }
    );

    // Tool 7: proc - Generate procedural objects
    server.tool(
        'proc',
        'Generate procedural TREE/ROCK/TERRAIN/BUILDING with style (LOW_POLY/REALISTIC/STYLIZED).',
        generateProceduralSchema,
        async (params) => {
            return handleGenerateProcedural(params);
        }
    );

    // Tool 8: opt - Optimize mesh (reduce polys)
    server.tool(
        'opt',
        'Reduce polygon count. Params: object_name, target_ratio (0.1-1.0).',
        optimizeMeshSchema,
        async (params) => {
            return handleOptimizeMesh(params);
        }
    );

    // Tool 9: render - Render scene preview
    server.tool(
        'render',
        'Render scene to image. Angles: FRONT/TOP/SIDE/ISOMETRIC/CURRENT.',
        renderPreviewSchema,
        async (params) => {
            return handleRenderPreview(params);
        }
    );

    // Tool 10: bake - Bake textures for game engine
    server.tool(
        'bake',
        'Bake textures for Unity/Unreal. Types: DIFFUSE/NORMAL/AO/ROUGHNESS/METALLIC/COMBINED/EMIT/SHADOW. Requires UV map.',
        bakeTexturesSchema,
        async (params) => {
            return handleBakeTextures(params);
        }
    );

    // Tool 11: gentex - Generate/Apply texture from AI or URL
    server.tool(
        'gentex',
        `Apply texture from path/URL. WORKFLOW: 1) Use generate_image to create texture 2) Use gentex with artifacts path.
Params: n=object, src=path/URL, uv=AUTO/BOX/SPHERE/CYLINDER, tile=[x,y]`,
        genTexSchema,
        async (params) => {
            return handleGenTex(params);
        }
    );

    // Tool 12: pipeline - Step-by-step workflow orchestrator
    server.tool(
        'pipe',
        `IMPORTANT: Use this FIRST for complex tasks! Creates step-by-step workflow.
Actions: start(task="description"), next(id="pipe_xxx"), back, status, cancel.
Returns: current step + tool to use + instruction. ALWAYS call next after completing each step.
Example: pipe({action:"start",task:"rock with texture and bake"}) → tells you step 1, then call next to proceed.`,
        pipelineSchema,
        async (params) => {
            return handlePipeline(params);
        }
    );

    // Tool 13: parse - Analyze prompt and return structured breakdown
    server.tool(
        'parse',
        `Analyze user prompt and extract structured information. Returns:
- objects: detected objects to create (type, style, size, color)
- materials: detected material presets (METAL, GLASS, WOOD, etc)
- textures: detected texture keywords (mossy, rusty, wooden, etc)
- optimize: whether optimization requested
- bake: baking settings (types, resolution)
- export: export settings (format, engine)
- plan: suggested execution steps

Use this to understand complex prompts before executing.`,
        parseSchema,
        async (params) => {
            return handleParse(params);
        }
    );

    // Tool 14: blueprint - Get structural breakdown for complex models
    server.tool(
        'blueprint',
        `Get STRUCTURAL BREAKDOWN for complex models. Returns component list with exact mesh types, sizes, positions, and materials.
Types: BUILDING, WEAPON, VEHICLE, ROBOT
Styles: CYBERPUNK, MEDIEVAL, SCIFI, MODERN, FANTASY
Detail: LOW, MEDIUM, HIGH
Returns: components list + generated Python code to execute via run().

ALWAYS use this for complex models instead of guessing mesh structure!`,
        blueprintSchema,
        async (params) => {
            return handleBlueprint(params);
        }
    );

    // Tool 15: sculpt - AI-assisted mesh modification
    server.tool(
        'sculpt',
        `Modify mesh geometry with AI-assisted operations.
Operations: smooth, horn/spike, nose/snout, eye socket, stretch, pinch waist, flatten, bevel, noise
Intensity: subtle, normal, extreme
Example: sculpt({object_name:"Sphere", operation:"add horns and make taller", intensity:"normal"})`,
        sculptSchema,
        async (params) => {
            return handleSculpt(params);
        }
    );

    // Tool 16: preview - Quick viewport capture for AI vision
    server.tool(
        'preview',
        `Quick viewport render for AI to SEE the scene. Returns image path.
Angles: FRONT, BACK, LEFT, RIGHT, TOP, PERSPECTIVE
After calling, use Antigravity's view_file on the returned path to actually see the image.
Use this to verify models and decide if revisions are needed.`,
        previewSchema,
        async (params) => {
            return handlePreview(params);
        }
    );

    // Tool 16: run - Execute Python script DIRECTLY in Blender (DO NOT create .py files!)
    server.tool(
        'run',
        `IMPORTANT: Execute Python code DIRECTLY in Blender. DO NOT create separate .py files!
This tool runs the script immediately in Blender's Python environment.

L LIBRARY AVAILABLE (token-efficient helpers):
Shapes: L.cube(l,s,n) L.sphere(l,r,n) L.cyl(l,r,h,n) L.cone(l,r,h,n) L.plane(l,s,n)
Props: L.table(l,s,n) L.chair(l,s,n) L.shelf(l,s,shelves,n) L.cauldron(l,s,n)
Scene: L.room(size,l,n) L.tree(l,s,style,n) L.rock(l,s,n) L.clear()
Material: L.mat(obj,preset,c) presets: MATTE/METAL/GLASS/PLASTIC/WOOD/GLOW
Transform: L.move(obj,l) L.rot(obj,r) L.scale(obj,s) L.dup(obj,l)

ALSO AVAILABLE: bpy, math, random

EXAMPLE: run({s:"c=L.cube([0,0,0],2,'MyCube');L.mat(c,'METAL',[0.8,0.2,0.2]);result='Created red metal cube'"})`,
        {
            s: z.string().describe('Python code to execute. Use L.func() or bpy. Set result="msg" for output.'),
        },
        async (params) => {
            log.debug('Executing: run', { len: params.s.length });
            const response = await blenderBridge.send('run_script', { script: params.s });
            if (response.success) {
                return {
                    content: [{
                        type: 'text',
                        text: JSON.stringify({ ok: 1, out: (response.data as any)?.output || 'done' }),
                    }],
                };
            }
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({ ok: 0, err: response.error }),
                }],
            };
        }
    );

    log.info('Tools registered', { count: 17 });
}

/**
 * Handler for get_blender_status
 */
async function handleGetBlenderStatus(): Promise<{
    content: Array<{ type: 'text'; text: string }>;
}> {
    const startTime = Date.now();

    // Check if we can connect
    if (!blenderBridge.isConnected) {
        try {
            await blenderBridge.connect();
        } catch {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({
                        connected: false,
                        error: {
                            code: 'CONNECTION_FAILED',
                            message: 'Cannot connect to Blender',
                            suggestion: 'Start Blender and enable the MCP addon, then click "Start Server"',
                        },
                    }),
                }],
            };
        }
    }

    // Try to get version
    const response = await blenderBridge.send('get_version');
    const durationMs = Date.now() - startTime;

    if (response.success) {
        return {
            content: [{
                type: 'text',
                text: JSON.stringify({
                    connected: true,
                    version: response.data,
                    latency_ms: durationMs,
                }),
            }],
        };
    }

    return {
        content: [{
            type: 'text',
            text: JSON.stringify({
                connected: false,
                error: response.error,
            }),
        }],
    };
}

/**
 * Handler for get_scene_info
 */
async function handleGetSceneInfo(params: {
    limit: number;
    offset: number;
    filter_type: string;
    verbosity: string;
}): Promise<{
    content: Array<{ type: 'text'; text: string }>;
}> {
    const response = await blenderBridge.send('get_scene_info', params);

    return {
        content: [{
            type: 'text',
            text: JSON.stringify(response.success ? response.data : { error: response.error }),
        }],
    };
}

/**
 * Graceful shutdown handler
 */
export function setupGracefulShutdown(): void {
    const shutdown = () => {
        log.info('Shutting down...');
        blenderBridge.disconnect();
        process.exit(0);
    };

    process.on('SIGINT', shutdown);
    process.on('SIGTERM', shutdown);
}
