import { TpaServer, TpaSession, ViewType } from '@augmentos/sdk';
import * as path from 'path';
import { Request, Response } from 'express';

// Load configuration from environment variables
const PACKAGE_NAME = process.env.PACKAGE_NAME || 'com.johnson.runningrhythm';
const AUGMENTOS_API_KEY = process.env.AUGMENTOS_API_KEY || process.env.MENTRAOS_API_KEY;
const PORT = parseInt(process.env.PORT || '3001');

if (!AUGMENTOS_API_KEY) {
    console.error("AUGMENTOS_API_KEY (or MENTRAOS_API_KEY) environment variable is required");
    process.exit(1);
}

/**
 * RunningRhythmApp - A running rhythm visual demo for AugmentOS
 * Provides automatic visual metronome demonstration for smart glasses
 */
class RunningRhythmApp extends TpaServer {
    private activeMetronomes: Map<string, NodeJS.Timeout> = new Map();
    private sessionStats: Map<string, { startTime: Date, beatCount: number, userId: string }> = new Map();
    private totalConnections = 0;

    constructor() {
        super({
            packageName: PACKAGE_NAME,
            apiKey: AUGMENTOS_API_KEY || "", // Provide empty string as fallback
            port: PORT,
        });
        
        this.setupStaticRoutes();
        this.setupLogging();
    }

    /**
     * Setup enhanced logging and monitoring
     */
    private setupLogging() {
        console.log('🏃‍♂️ Running Rhythm Demo started on port', PORT);
        console.log('📱 Package:', PACKAGE_NAME);
        console.log('🔗 Access demo at: http://localhost:' + PORT);
        console.log('📊 Auto-demo mode: No voice input required');
        console.log('📝 Monitoring: /api/status | /api/logs | /health');

        // Setup periodic status logging
        setInterval(() => {
            this.logServerStatus();
        }, 60000); // Log every minute
    }

    /**
     * Log comprehensive server status
     */
    private logServerStatus() {
        const uptime = process.uptime();
        const memUsage = process.memoryUsage();
        
        console.log('📊 Server Status Report', {
            uptime: `${Math.floor(uptime / 60)}m ${Math.floor(uptime % 60)}s`,
            memory: `${Math.round(memUsage.heapUsed / 1024 / 1024)}MB`,
            activeSessions: this.activeMetronomes.size,
            totalConnections: this.totalConnections,
            timestamp: new Date().toISOString()
        });
    }

    /**
     * Setup static file serving and API routes
     */
    private setupStaticRoutes() {
        const app = this.getExpressApp(); // Use the correct method
        
        // Add request logging middleware
        app.use((req: Request, res: Response, next: any) => {
            console.log('🌐 HTTP Request', {
                method: req.method,
                url: req.url,
                userAgent: req.get('User-Agent'),
                timestamp: new Date().toISOString()
            });
            next();
        });

        // Serve static files
        app.use('/static', require('express').static(path.join(__dirname, '..')));
        
        // Main demo page
        app.get('/', (req: Request, res: Response) => {
            console.log('📄 Serving demo page');
            res.sendFile(path.join(__dirname, '..', 'demo.html'));
        });

        app.get('/demo.html', (req: Request, res: Response) => {
            console.log('📄 Serving demo page');
            res.sendFile(path.join(__dirname, '..', 'demo.html'));
        });

        // Monitor page
        app.get('/monitor', (req: Request, res: Response) => {
            console.log('📊 Serving monitor page');
            res.sendFile(path.join(__dirname, '..', 'monitor.html'));
        });

        app.get('/monitor.html', (req: Request, res: Response) => {
            console.log('📊 Serving monitor page');
            res.sendFile(path.join(__dirname, '..', 'monitor.html'));
        });

        // API endpoints
        app.get('/api/status', (req: Request, res: Response) => {
            console.log('📊 Status API called');
            const uptime = process.uptime();
            const memUsage = process.memoryUsage();
            
            res.json({
                status: 'online',
                uptime: `${Math.floor(uptime / 60)}m ${Math.floor(uptime % 60)}s`,
                memory: `${Math.round(memUsage.heapUsed / 1024 / 1024)}MB`,
                activeSessions: this.activeMetronomes.size,
                totalConnections: this.totalConnections,
                sessions: Array.from(this.sessionStats.entries()).map(([id, stats]) => ({
                    sessionId: id,
                    userId: stats.userId,
                    startTime: stats.startTime,
                    beatCount: stats.beatCount,
                    duration: Date.now() - stats.startTime.getTime()
                })),
                timestamp: new Date().toISOString()
            });
        });

        app.get('/health', (req: Request, res: Response) => {
            res.json({ status: 'healthy', timestamp: new Date().toISOString() });
        });

        app.get('/api/logs', (req: Request, res: Response) => {
            console.log('📄 Logs API called');
            res.json({
                message: 'Logs are displayed in the server console',
                activeSessions: this.activeMetronomes.size,
                totalConnections: this.totalConnections,
                timestamp: new Date().toISOString()
            });
        });
    }

    /**
     * Handle new AugmentOS session
     */
    protected async onSession(session: TpaSession, sessionId: string, userId: string): Promise<void> {
        this.totalConnections++;
        console.log('🎯 New running demo session started', {
            sessionId,
            userId,
            totalConnections: this.totalConnections,
            activeSessions: this.activeMetronomes.size + 1,
            timestamp: new Date().toISOString()
        });

        this.sessionStats.set(sessionId, {
            startTime: new Date(),
            beatCount: 0,
            userId
        });

        // Show welcome message
        session.layouts.showTextWall("🏃‍♂️ Running Rhythm Demo Ready!", {
            view: ViewType.MAIN,
            durationMs: 3000
        });

        // Start automatic rhythm demo after welcome
        setTimeout(() => {
            this.startDemo(session, 180, sessionId); // Start with 180 SPM
        }, 3000);

        // Setup event handlers
        const transcriptionCleanup = session.events.onTranscription((data: any) => {
            console.log('🎤 Transcription received (ignored in auto-demo mode):', data.text);
        });

        const phoneNotificationCleanup = session.events.onPhoneNotifications((data: any) => {
            console.log('📱 Phone notification:', data);
        });

        const batteryCleanup = session.events.onGlassesBattery((data: any) => {
            console.log('🔋 Glasses battery:', data);
        });

        const errorCleanup = session.events.onError((error: any) => {
            console.error('❌ Session error:', error);
        });

        // Handle session disconnection
        session.events.onDisconnected(() => {
            console.log('👋 Session disconnected', {
                sessionId,
                userId,
                duration: this.sessionStats.get(sessionId)?.startTime ? Date.now() - this.sessionStats.get(sessionId)!.startTime.getTime() : 0,
                timestamp: new Date().toISOString()
            });
            
            this.stopDemo(sessionId);
            this.sessionStats.delete(sessionId);
        });

        // Add cleanup handlers
        this.addCleanupHandler(() => {
            if (transcriptionCleanup) transcriptionCleanup();
            if (phoneNotificationCleanup) phoneNotificationCleanup();
            if (batteryCleanup) batteryCleanup();
            if (errorCleanup) errorCleanup();
        });
    }

    /**
     * Start automatic running rhythm demonstration
     */
    private startDemo(session: TpaSession, cadence: number, sessionId: string) {
        console.log('🎵 Starting rhythm demo', { sessionId, cadence });
        
        let beatCount = 0;
        let phaseCount = 0;
        const cadences = [180, 160, 200, 180]; // SPM cycle
        let currentCadenceIndex = 0;
        
        const runDemo = () => {
            const stats = this.sessionStats.get(sessionId);
            if (!stats) return;

            beatCount++;
            stats.beatCount = beatCount;
            
            // Create rhythm display
            const leftFoot = beatCount % 2 === 1;
            const display = this.createRunningDisplay(cadence, beatCount, leftFoot);
            
            // Show on glasses
            session.layouts.showTextWall(display, {
                view: ViewType.MAIN,
                durationMs: 500
            });

            // Switch cadence every 20 beats
            if (beatCount % 20 === 0) {
                phaseCount++;
                currentCadenceIndex = (currentCadenceIndex + 1) % cadences.length;
                cadence = cadences[currentCadenceIndex];
                
                console.log('🔄 Cadence change', { 
                    sessionId, 
                    newCadence: cadence, 
                    phase: phaseCount,
                    totalBeats: beatCount 
                });
            }

            // Calculate interval for next beat (60000ms / SPM)
            const interval = Math.round(60000 / cadence);
            
            // Schedule next beat
            const timeout = setTimeout(runDemo, interval);
            this.activeMetronomes.set(sessionId, timeout);
        };

        // Start the demo
        runDemo();
    }

    /**
     * Create visual running display optimized for smart glasses
     */
    private createRunningDisplay(cadence: number, beatCount: number, leftFoot: boolean): string {
        const footIcon = leftFoot ? "🦶L" : "🦶R";
        const rhythmBar = this.generateRhythmBar(beatCount);
        
        return `
🏃‍♂️ RUNNING RHYTHM 🏃‍♂️

${footIcon}  ${cadence} SPM  ${footIcon}

${rhythmBar}

Beat: ${beatCount}
Phase: ${Math.floor(beatCount / 20) + 1}

${this.getCadenceDescription(cadence)}
        `.trim();
    }

    /**
     * Generate visual rhythm bar
     */
    private generateRhythmBar(beatCount: number): string {
        const position = (beatCount - 1) % 8;
        const bar = Array(8).fill('○');
        bar[position] = '●';
        return bar.join(' ');
    }

    /**
     * Get description for current cadence
     */
    private getCadenceDescription(cadence: number): string {
        if (cadence === 180) return "🎯 OPTIMAL PACE";
        if (cadence === 160) return "🐌 SLOW PACE";
        if (cadence === 200) return "🏃‍♂️ FAST PACE";
        return "🏃‍♂️ CUSTOM PACE";
    }

    /**
     * Stop running demonstration
     */
    private stopDemo(sessionId: string) {
        const timeout = this.activeMetronomes.get(sessionId);
        if (timeout) {
            clearTimeout(timeout);
            this.activeMetronomes.delete(sessionId);
            console.log('⏹️ Demo stopped', { sessionId });
        }
    }
}

// Start the server
console.log('🚀 Starting AugmentOS Running Rhythm Demo...');
const app = new RunningRhythmApp();
app.start().catch(console.error); 