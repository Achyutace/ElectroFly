"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const sdk_1 = require("@mentra/sdk");
const dotenv = __importStar(require("dotenv"));
const path = __importStar(require("path"));
// Load environment variables from .env file
dotenv.config();
// Load configuration from environment variables
const PACKAGE_NAME = process.env.PACKAGE_NAME || "com.johnson.runningrhythm";
const PORT = parseInt(process.env.PORT || "3001");
const MENTRAOS_API_KEY = process.env.MENTRAOS_API_KEY;
if (!MENTRAOS_API_KEY) {
    console.error("MENTRAOS_API_KEY environment variable is required");
    process.exit(1);
}
/**
 * RunningRhythmApp - A running rhythm visual demo for MentraOS
 * Provides automatic visual metronome demonstration for smart glasses
 */
class RunningRhythmApp extends sdk_1.TpaServer {
    constructor(config) {
        super(config);
        this.activeMetronomes = new Map();
        this.sessionStats = new Map();
        this.totalConnections = 0;
        this.setupStaticRoutes();
        this.setupLogging();
    }
    /**
     * Setup enhanced logging and monitoring
     */
    setupLogging() {
        // Log server startup
        this.logger.info('🏃‍♂️ Running Rhythm Demo Server initializing...', {
            package: PACKAGE_NAME,
            port: PORT,
            timestamp: new Date().toISOString(),
            service: 'tpa-server'
        });
        // Setup periodic status logging
        setInterval(() => {
            this.logServerStatus();
        }, 60000); // Log every minute
    }
    /**
     * Log current server status
     */
    logServerStatus() {
        const activeSessionCount = this.activeMetronomes.size;
        const memoryUsage = process.memoryUsage();
        this.logger.info('📊 Server Status Report', {
            activeSessions: activeSessionCount,
            totalConnections: this.totalConnections,
            memoryUsage: {
                rss: `${Math.round(memoryUsage.rss / 1024 / 1024)}MB`,
                heapUsed: `${Math.round(memoryUsage.heapUsed / 1024 / 1024)}MB`,
                heapTotal: `${Math.round(memoryUsage.heapTotal / 1024 / 1024)}MB`
            },
            uptime: `${Math.round(process.uptime())}s`,
            timestamp: new Date().toISOString(),
            service: 'tpa-server'
        });
        // Log individual session stats
        this.sessionStats.forEach((stats, sessionId) => {
            const duration = Date.now() - stats.startTime.getTime();
            this.logger.info('📱 Active Session Status', {
                sessionId,
                userId: stats.userId,
                duration: `${Math.round(duration / 1000)}s`,
                beatCount: stats.beatCount,
                service: 'app-session'
            });
        });
    }
    /**
     * Setup static file serving and demo routes
     */
    setupStaticRoutes() {
        const app = this.getExpressApp();
        // Add request logging middleware
        app.use((req, res, next) => {
            const startTime = Date.now();
            res.on('finish', () => {
                const duration = Date.now() - startTime;
                this.logger.info('🌐 HTTP Request', {
                    method: req.method,
                    url: req.url,
                    statusCode: res.statusCode,
                    duration: `${duration}ms`,
                    userAgent: req.get('User-Agent'),
                    ip: req.ip,
                    timestamp: new Date().toISOString(),
                    service: 'http-server'
                });
            });
            next();
        });
        // Serve static files from the project root
        app.use('/static', require('express').static(path.join(__dirname, '..')));
        // Serve demo.html at root path
        app.get('/', (req, res) => {
            this.logger.info('📄 Serving demo page', {
                path: '/',
                timestamp: new Date().toISOString(),
                service: 'http-server'
            });
            res.sendFile(path.join(__dirname, '../demo.html'));
        });
        // Serve demo.html explicitly
        app.get('/demo.html', (req, res) => {
            res.sendFile(path.join(__dirname, '../demo.html'));
        });
        // Serve monitor page
        app.get('/monitor', (req, res) => {
            this.logger.info('📊 Serving monitor page', {
                path: '/monitor',
                timestamp: new Date().toISOString(),
                service: 'http-server'
            });
            res.sendFile(path.join(__dirname, '../monitor.html'));
        });
        app.get('/monitor.html', (req, res) => {
            res.sendFile(path.join(__dirname, '../monitor.html'));
        });
        // Enhanced API endpoint for demo status
        app.get('/api/status', (req, res) => {
            const status = {
                status: 'running',
                app: 'Running Rhythm Demo',
                package: PACKAGE_NAME,
                port: PORT,
                activeSessions: this.activeMetronomes.size,
                totalConnections: this.totalConnections,
                uptime: process.uptime(),
                memoryUsage: process.memoryUsage(),
                timestamp: new Date().toISOString(),
                sessions: Array.from(this.sessionStats.entries()).map(([sessionId, stats]) => ({
                    sessionId,
                    userId: stats.userId,
                    startTime: stats.startTime,
                    beatCount: stats.beatCount,
                    duration: Date.now() - stats.startTime.getTime()
                }))
            };
            this.logger.info('📊 Status API called', {
                requestedBy: req.ip,
                activeSessions: this.activeMetronomes.size,
                service: 'api'
            });
            res.json(status);
        });
        // Enhanced health check endpoint
        app.get('/health', (req, res) => {
            const health = {
                status: 'healthy',
                timestamp: new Date().toISOString(),
                uptime: process.uptime(),
                activeSessions: this.activeMetronomes.size
            };
            res.json(health);
        });
        // Add logs endpoint for monitoring
        app.get('/api/logs', (req, res) => {
            const logs = {
                serverStatus: {
                    activeSessions: this.activeMetronomes.size,
                    totalConnections: this.totalConnections,
                    uptime: process.uptime(),
                    memoryUsage: process.memoryUsage()
                },
                sessions: Array.from(this.sessionStats.entries()).map(([sessionId, stats]) => ({
                    sessionId,
                    userId: stats.userId,
                    startTime: stats.startTime,
                    beatCount: stats.beatCount,
                    duration: Date.now() - stats.startTime.getTime()
                })),
                timestamp: new Date().toISOString()
            };
            res.json(logs);
        });
    }
    /**
     * Handle new session connections with enhanced logging
     * @param session - The TPA session instance
     * @param sessionId - Unique identifier for this session
     * @param userId - The user ID for this session
     */
    async onSession(session, sessionId, userId) {
        this.totalConnections++;
        // Enhanced session connection logging
        session.logger.info('🎯 New running demo session started', {
            sessionId,
            userId,
            totalConnections: this.totalConnections,
            activeSessions: this.activeMetronomes.size + 1,
            clientInfo: {
                userAgent: 'MentraOS-Device',
                deviceType: 'smart-glasses'
            },
            timestamp: new Date().toISOString(),
            service: 'app-session'
        });
        // Initialize session stats
        this.sessionStats.set(sessionId, {
            startTime: new Date(),
            beatCount: 0,
            userId
        });
        // Demo configuration
        let cadence = 180; // Standard running cadence
        let beatCount = 0;
        // Show welcome message with logging
        session.logger.info('📱 Displaying welcome message', {
            sessionId,
            userId,
            message: 'Running Rhythm Demo starting',
            initialCadence: cadence,
            service: 'app-session'
        });
        session.layouts.showTextWall(`🏃‍♂️ Running Rhythm Demo\n\nStarting automatic demonstration...\nOptimal Cadence: ${cadence} SPM`);
        // Start demo after 3 seconds with logging
        setTimeout(() => {
            session.logger.info('🚀 Starting rhythm demonstration', {
                sessionId,
                userId,
                initialCadence: cadence,
                delay: '3000ms',
                service: 'app-session'
            });
            this.startDemo(session, cadence, sessionId);
        }, 3000);
        // Enhanced disconnection logging
        session.events.onDisconnected(() => {
            const stats = this.sessionStats.get(sessionId);
            const duration = stats ? Date.now() - stats.startTime.getTime() : 0;
            session.logger.info('👋 Demo session disconnected', {
                sessionId,
                userId,
                duration: `${Math.round(duration / 1000)}s`,
                totalBeats: stats?.beatCount || 0,
                avgCadence: stats?.beatCount ? Math.round((stats.beatCount * 60000) / duration) : 0,
                activeSessions: Math.max(0, this.activeMetronomes.size - 1),
                service: 'app-session'
            });
            this.stopDemo(sessionId);
            this.sessionStats.delete(sessionId);
        });
        // Log any errors during session
        session.events.onError?.((error) => {
            session.logger.error('❌ Session error occurred', {
                sessionId,
                userId,
                error: error.message,
                stack: error.stack,
                service: 'app-session'
            });
        });
    }
    /**
     * Start the automatic running rhythm demonstration with enhanced logging
     */
    startDemo(session, cadence, sessionId) {
        let beatCount = 0;
        let currentCadence = cadence;
        let phaseCount = 0; // Track demo phases
        session.logger.info('⏱️ Demo loop initialized', {
            sessionId,
            initialCadence: currentCadence,
            expectedPhases: 4,
            service: 'app-session'
        });
        // Calculate interval in milliseconds (cadence is steps per minute)
        const updateInterval = () => (60 / currentCadence) * 1000;
        const demoLoop = () => {
            beatCount++;
            const leftFoot = beatCount % 2 === 1;
            // Update session stats
            const stats = this.sessionStats.get(sessionId);
            if (stats) {
                stats.beatCount = beatCount;
            }
            // Demo phases: change cadence every 20 beats to show different rhythms
            if (beatCount % 20 === 0) {
                phaseCount++;
                const oldCadence = currentCadence;
                switch (phaseCount % 4) {
                    case 0:
                        currentCadence = 180;
                        break; // Normal
                    case 1:
                        currentCadence = 160;
                        break; // Slow
                    case 2:
                        currentCadence = 200;
                        break; // Fast
                    case 3:
                        currentCadence = 180;
                        break; // Back to normal
                }
                session.logger.info('🔄 Phase transition', {
                    sessionId,
                    phase: (phaseCount % 4) + 1,
                    oldCadence,
                    newCadence: currentCadence,
                    beatCount,
                    status: currentCadence < 170 ? 'TOO SLOW' : currentCadence > 190 ? 'TOO FAST' : 'PERFECT',
                    service: 'app-session'
                });
            }
            // Create visual beat display optimized for 576x136 glasses
            const display = this.createRunningDisplay(currentCadence, beatCount, leftFoot);
            session.layouts.showTextWall(display);
            // Log every 10th beat for monitoring
            if (beatCount % 10 === 0) {
                session.logger.info('👟 Rhythm progress', {
                    sessionId,
                    beatCount,
                    currentCadence,
                    leftFoot,
                    phase: Math.floor(phaseCount % 4) + 1,
                    service: 'app-session'
                });
            }
            // Schedule next beat
            const nextInterval = updateInterval();
            const timeout = setTimeout(demoLoop, nextInterval);
            this.activeMetronomes.set(sessionId, timeout);
        };
        // Start the demo loop
        demoLoop();
        session.logger.info(`🎵 Running demo started successfully`, {
            sessionId,
            initialCadence: cadence,
            interval: `${(60 / cadence) * 1000}ms`,
            service: 'app-session'
        });
    }
    /**
     * Create the running display optimized for smart glasses
     */
    createRunningDisplay(cadence, beatCount, leftFoot) {
        const feedback = cadence < 170 ? "SLOW PACE" : cadence > 190 ? "FAST PACE" : "OPTIMAL";
        const rhythmBar = this.generateRhythmBar(beatCount);
        const stepIndicator = leftFoot ? "L●○" : "○●R";
        // Optimized for 576x136 display - simple and clear
        return `
╔══════════════════════════════════════════════════════════════════════╗
║                      RUNNING RHYTHM DEMO                            ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  ${stepIndicator}  Step ${beatCount.toString().padStart(3, '0')}     Cadence: ${cadence} SPM  ║
║  ${leftFoot ? 'LEFT ' : 'RIGHT'} FOOT                 Status: ${feedback}      ║
║                                                                      ║
║  Rhythm: ${rhythmBar}  ║
║                                                                      ║
║  Target Zone: 170-190 SPM  │  Current: ${cadence < 170 ? '⬇️ TOO SLOW' : cadence > 190 ? '⬆️ TOO FAST' : '✅ PERFECT'}   ║
╚══════════════════════════════════════════════════════════════════════╝
        `.trim();
    }
    /**
     * Generate a visual rhythm bar using ASCII characters
     */
    generateRhythmBar(beatCount) {
        const bars = ['▁', '▃', '▅', '▇'];
        let rhythmBar = '';
        for (let i = 0; i < 16; i++) {
            // Create a wave pattern that moves with the beat
            const phase = (beatCount + i) * 0.4;
            const barHeight = Math.abs(Math.sin(phase)) * 3;
            rhythmBar += bars[Math.floor(barHeight)];
        }
        return rhythmBar;
    }
    /**
     * Stop the demo for a session with enhanced logging
     */
    stopDemo(sessionId) {
        const timeout = this.activeMetronomes.get(sessionId);
        const stats = this.sessionStats.get(sessionId);
        if (timeout) {
            clearTimeout(timeout);
            this.activeMetronomes.delete(sessionId);
            this.logger.info('⏹️ Demo stopped for session', {
                sessionId,
                userId: stats?.userId || 'unknown',
                totalBeats: stats?.beatCount || 0,
                duration: stats ? `${Math.round((Date.now() - stats.startTime.getTime()) / 1000)}s` : 'unknown',
                remainingSessions: this.activeMetronomes.size,
                service: 'tpa-server'
            });
        }
    }
}
// Create and start the app server
const server = new RunningRhythmApp({
    packageName: PACKAGE_NAME,
    apiKey: MENTRAOS_API_KEY,
    port: PORT,
    publicDir: false // Disable default static serving, we'll handle it ourselves
});
server.start().then(() => {
    console.log(`🏃‍♂️ Running Rhythm Demo started on port ${PORT}`);
    console.log(`📱 Package: ${PACKAGE_NAME}`);
    console.log(`🔗 Access demo at: http://localhost:${PORT}`);
    console.log(`🌐 ngrok URL: https://kingfish-humble-factually.ngrok-free.app`);
    console.log(`📊 Auto-demo mode: No voice input required`);
    console.log(`📝 Monitoring: /api/status | /api/logs | /health`);
}).catch(err => {
    console.error("Failed to start server:", err);
});
