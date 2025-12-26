# rust-green Web Dashboard

A modern, responsive web interface for the Rust code safety analysis platform described in the architectural documents.

## Overview

This frontend dashboard provides an intuitive interface for researchers, developers, and system administrators to interact with the Rust code safety analysis system. It implements the key features outlined in the architectural specification:

- Multi-format code submission (paste, upload, Git)
- Real-time analysis dashboard
- Interactive code viewer with safety findings
- Research management tools interface
- System performance monitoring

## Features Implemented

### 1. Code Submission Panel
- Three submission methods: Paste Code, Upload File, Git Repository
- Live code editor with syntax highlighting
- Quick scan functionality for immediate feedback
- Configurable analysis parameters (AI model, severity threshold, analysis depth)

### 2. Real-time Dashboard
- Active session monitoring with progress tracking
- Live performance metrics (parse time, accuracy, workers, uptime)
- Interactive session management (view reports, export data)

### 3. Safety Findings Display
- Visual severity indicators (Critical, High, Medium)
- Side-by-side code comparison (unsafe vs. safe alternatives)
- Actionable findings (apply fixes, mark false positives, add notes)
- Confidence scoring for AI-generated suggestions

### 4. Research & Analytics
- Model performance tracking
- System status monitoring
- Research partner integration
- Data export capabilities

## Technical Implementation

### HTML Structure
- Semantic HTML5 with proper accessibility attributes
- Responsive grid layout using CSS Grid and Flexbox
- Modular component architecture

### CSS Features
- CSS Custom Properties (variables) for consistent theming
- Modern design system with cohesive color palette
- Responsive breakpoints for mobile, tablet, and desktop
- Smooth animations and transitions
- Custom scrollbar styling

### JavaScript Functionality
- Tab switching and dynamic content loading
- Real-time code analysis simulation
- Interactive session management
- Live data updates with simulated API calls
- Responsive navigation menu

## Architecture Alignment

This frontend aligns with the backend architecture described in the documents:

1. **Session Management**: Mirrors the Session aggregate from the domain model
2. **CodeBlock Analysis**: Displays findings consistent with CodeBlockAnalysis entities
3. **AI Model Integration**: Supports multiple AI models (SmolLM, DeepSeek, rule-based)
4. **Research Focus**: Includes tools for research experimentation and data collection

## Getting Started

### Quick Start
1. Open `index.html` in a modern web browser
2. The dashboard will load with example data and functionality
3. Try pasting Rust code into the editor and clicking "Quick Scan"
4. Explore the different panels and interactive elements

### Development
The frontend uses only vanilla HTML, CSS, and JavaScript with no build step required. All dependencies are loaded from CDN:
- Font Awesome for icons
- Google Fonts (Inter, JetBrains Mono)
- Highlight.js for code syntax highlighting

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Future Enhancements

Based on the architectural documents, future enhancements could include:

1. **Real API Integration**: Connect to the actual Rust analysis backend
2. **WebSocket Support**: Real-time updates for analysis progress
3. **Advanced Code Editor**: Monaco Editor or CodeMirror integration
4. **User Authentication**: Multi-role access control
5. **Data Visualization**: Charts and graphs for research analytics
6. **Export Functionality**: PDF/JSON/CSV export of analysis results

## Project Structure

```
frontend/
├── index.html          # Main HTML document
├── style.css           # All CSS styles
├── script.js           # JavaScript functionality
└── README.md           # This documentation
```

## Design Philosophy

The interface follows these design principles:

1. **Clarity**: Clear visual hierarchy and information architecture
2. **Efficiency**: Minimize clicks to accomplish common tasks
3. **Feedback**: Provide immediate feedback for user actions
4. **Consistency**: Uniform styling and interaction patterns
5. **Accessibility**: Semantic HTML and keyboard navigation support

## Color Scheme

- **Primary**: Green (#2e8555) - Represents safety and Rust ecosystem
- **Secondary**: Gray (#4a5568) - Professional and neutral
- **Accent**: Blue (#4299e1) - Interactive elements
- **Status Colors**: Red (critical), Orange (high), Blue (medium)

## Responsive Design

The dashboard adapts to different screen sizes:
- **Desktop**: Two-column layout with full navigation
- **Tablet**: Single column with adjusted spacing
- **Mobile**: Stacked layout with collapsible navigation

## License

This frontend implementation is for demonstration purposes as part of the rust-green architectural analysis project.
