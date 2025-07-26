# 🏃‍♂️ Running Rhythm Demo for MentraOS

A smart running cadence demonstration application designed for MentraOS smart glasses. This app provides automatic visual metronome demonstration, perfect for showcasing running rhythm concepts without requiring any user input.

## 📱 Features

### Core Functionality
- **Automatic Visual Demo**: Self-running rhythm demonstration
- **Cadence Cycling**: Automatic transitions between different running speeds
- **Step Tracking**: Left/right foot step visualization
- **Real-time Feedback**: Visual indicators for different pace zones
- **Zero Input Required**: Perfect for glasses without input capabilities

### Display Optimization
- Optimized for **576×136 pixel 1-bit BMP** display
- High contrast monochrome graphics
- Clear visual hierarchy and minimal eye strain
- Simplified interface for small displays

## 🏃‍♂️ Demo Phases

The application automatically cycles through different running cadences to demonstrate various pacing scenarios:

### Automatic Cadence Cycle
- **Phase 1 (180 SPM)**: Optimal running pace - ✅ PERFECT
- **Phase 2 (160 SPM)**: Slower jogging pace - ⬇️ TOO SLOW  
- **Phase 3 (200 SPM)**: Fast running pace - ⬆️ TOO FAST
- **Phase 4 (180 SPM)**: Return to optimal - ✅ PERFECT

Each phase lasts for 20 steps (~10-15 seconds) before automatically transitioning to the next.

## 🎯 Target Zones

### Optimal Cadence Guidelines
- **170-190 SPM**: Perfect running cadence zone
- **< 170 SPM**: Too slow - increase pace
- **> 190 SPM**: Too fast - reduce pace

### Visual Feedback
- **✅ PERFECT**: Optimal cadence range
- **⬇️ TOO SLOW**: Below optimal range  
- **⬆️ TOO FAST**: Above optimal range

## 🛠️ Technical Setup

### Prerequisites
- Node.js/Bun runtime
- MentraOS SDK v1.1.10+
- ngrok (for external access)

### Installation
```bash
# Clone and setup
cd my-first-mentraos-app
bun install

# Configure environment
cp .env.example .env
# Edit .env with your MentraOS API key

# Build and run
bun run build
bun run start
```

### Environment Variables
```env
PORT=3000
PACKAGE_NAME=com.johnson.runningrhythm
MENTRAOS_API_KEY=your_api_key_here
```

## 🔧 Development

### Project Structure
```
my-first-mentraos-app/
├── src/
│   └── index.ts          # Main application logic
├── dist/                 # Compiled JavaScript  
├── demo.html            # Web demo simulation
├── package.json          # Dependencies and scripts
├── tsconfig.json         # TypeScript configuration
├── .env                  # Environment variables
└── README.md            # This file
```

### Key Components
1. **RunningRhythmApp**: Main server class with auto-demo
2. **Auto Phase Manager**: Handles cadence transitions
3. **Visual Display**: Creates optimized glasses interface
4. **Session Management**: User connection handling

## 📊 Display Interface

### Main Display (576×136 pixels)
```
╔══════════════════════════════════════════════════════════════════════╗
║                      RUNNING RHYTHM DEMO                            ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  L●○  Step 045     Cadence: 180 SPM  ║
║  LEFT FOOT                 Status: OPTIMAL      ║
║                                                                      ║
║  Rhythm: ▁▃▅▇▅▃▁▃▅▇▅▃▁▃▅▇  ║
║                                                                      ║
║  Target Zone: 170-190 SPM  │  Current: ✅ PERFECT   ║
╚══════════════════════════════════════════════════════════════════════╝
```

### Visual Elements
- **Step Counter**: L●○ / ○●R indicators for left/right foot
- **Rhythm Bar**: Moving wave pattern showing beat timing
- **Status Display**: Current pace evaluation
- **Cadence Info**: Real-time SPM display

## 🚀 Deployment

### Local Testing
```bash
# Start application
bun run start

# Access locally
http://localhost:3000

# View demo simulation
http://localhost:3000/demo.html
```

### Public Access (ngrok)
```bash
# Install ngrok
winget install Ngrok.Ngrok

# Configure auth token
ngrok config add-authtoken YOUR_TOKEN

# Create tunnel
ngrok http 3000
```

### MentraOS Integration
1. Upload app to MentraOS console
2. Configure package name: `com.johnson.runningrhythm`
3. No special permissions required (no input needed)
4. Deploy to smart glasses

## 🎯 Use Cases

### For Demonstration
- **Trade Shows**: Showcase smart glasses capabilities
- **Training Sessions**: Teach running rhythm concepts
- **Product Demos**: Display visual feedback systems
- **Educational Tools**: Running technique instruction

### For Development
- **Display Testing**: Validate 576×136 monochrome output
- **Performance Testing**: Check smooth animation rendering
- **Battery Testing**: Monitor power consumption during continuous use
- **Visibility Testing**: Outdoor lighting conditions

## 📱 Web Demo

The included `demo.html` provides a browser-based simulation of the smart glasses display:

- **Real-time Animation**: Matches actual glasses output
- **Phase Indicators**: Shows current demo phase
- **Interactive Controls**: Start/stop/reset functionality
- **Responsive Design**: Works on desktop and mobile

Access at: `http://localhost:3000/demo.html`

## 🔄 Automatic Operation

### No User Input Required
- **Auto-start**: Begins demonstration immediately upon connection
- **Self-cycling**: Automatically transitions between cadence phases  
- **Continuous Loop**: Runs indefinitely until disconnection
- **Zero Configuration**: No setup or calibration needed

### Session Management
- **Automatic Cleanup**: Properly handles disconnections
- **Multiple Users**: Supports concurrent demo sessions
- **Resource Management**: Efficient timer and memory usage

## 📞 Support

- **MentraOS Documentation**: [console.mentra.glass](https://console.mentra.glass)
- **SDK Reference**: `@mentra/sdk` package
- **Display Specs**: 576×136 pixels, 1-bit BMP, Monochrome

## 📄 License

MIT License - Feel free to modify and distribute.

---

**Perfect for Smart Glasses Demonstrations! 🏃‍♂️👓** 