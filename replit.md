# Angela - 非劳务收入路径设计师

## Overview

Angela is a Flask-based web application that serves as a non-labor income pathway designer. The application helps users input project information and receive AI-generated suggestions for creating alternative income streams. Users can describe their projects, add key personnel with their roles and resources, and get customized recommendations based on their specific situation.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templating with Flask for server-side rendering
- **UI Framework**: Bootstrap 5 with dark theme for responsive design
- **JavaScript**: Vanilla JavaScript for dynamic form interactions (adding/removing person cards)
- **Styling**: Custom CSS combined with Bootstrap and Font Awesome icons
- **Language**: Chinese (zh-CN) interface with bilingual support considerations

### Backend Architecture
- **Web Framework**: Flask with minimal configuration for rapid development
- **Routing Structure**: Simple route-based architecture with form processing endpoints
- **Data Processing**: Form data collection and JSON structuring for AI processing
- **Session Management**: Flask sessions with configurable secret keys
- **Error Handling**: Flash messaging system for user feedback

### Form Processing System
- **Dynamic Forms**: JavaScript-powered dynamic addition/removal of person cards
- **Data Validation**: Both client-side and server-side validation
- **Multi-step Data Collection**: Modular form sections for project info, key persons, and external resources
- **JSON Serialization**: Structured data preparation for downstream AI processing

### File Organization
- **Static Assets**: Separated CSS and JavaScript files for maintainability
- **Templates**: Modular HTML templates for different views (index, result)
- **Application Logic**: Clean separation between main application logic and execution entry point

## External Dependencies

### Frontend Libraries
- **Bootstrap 5**: UI component library via CDN
- **Font Awesome 6**: Icon library via CDN
- **Custom Bootstrap Theme**: Replit agent dark theme for consistent styling

### Backend Dependencies
- **Flask**: Core web framework
- **Python Standard Library**: JSON, logging, and OS modules for basic functionality

### Development Environment
- **Python Runtime**: Flask development server configuration
- **Environment Variables**: Session secret key management
- **Logging**: Built-in Python logging for debugging and monitoring

### Potential AI Integration Points
- **Form Data Structure**: Prepared JSON format suggests integration with AI services for income pathway generation
- **Result Processing**: Template structure indicates AI-generated content display capabilities