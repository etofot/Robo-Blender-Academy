/**
 * Blender MCP Server - Configuration
 */

export interface Config {
    blender: {
        host: string;
        port: number;
    };
    server: {
        name: string;
        version: string;
    };
    logging: {
        level: string;
    };
}

export function loadConfig(): Config {
    return {
        blender: {
            host: process.env.BLENDER_HOST || '127.0.0.1',
            port: parseInt(process.env.BLENDER_PORT || '9876', 10),
        },
        server: {
            name: 'blender-mcp',
            version: '2.0.0',
        },
        logging: {
            level: process.env.LOG_LEVEL || 'info',
        },
    };
}

export const config = loadConfig();
