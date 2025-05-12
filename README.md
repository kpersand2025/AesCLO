# AesCLO

Overview:

AesCLO is a fashion-based web application designed to streamline outfit selection and wardrobe management. The platform allows users to upload images of their clothing items, organize them in a digital wardrobe, and receive AI-powered outfit recommendations based on various factors including color coordination, occasion, and weather conditions.


Key Features:

  Virtual Wardrobe Management
  
  - Upload and Categorize: Upload images of clothing items with automatic AI-powered categorization (tops, bottoms, shoes, accessories)
  - AI-Powered Detection: Automatic detection of dominant colors, suitable occasions, and weather suitability
  - Subcategory Classification: Identifies "complete" tops (dresses, jumpsuits) vs. standard tops, and accessory subcategories
  - Availability Tracking: Mark items as unavailable/dirty to prevent them from being suggested in outfits

  Intelligent Outfit Generation
  
  - Color-Coordinated Outfits: Generate outfits based on color harmony and complementary color theory
  - Occasion-Based Outfits: Create outfits suitable for specific occasions (casual, work/professional, formal, athletic/sport, lounge/sleepwear)
  - Weather-Based Recommendations: Suggest appropriate outfits based on current weather conditions, with support for different temperature ranges (cold, cool, warm, hot) and weather types (sunny, cloudy, rain, snow)
  - Smart Matching Algorithm: Prioritizes items that share common occasions, appropriate temperature ranges, and complementary colors

  User Experience
  
  - Saved Outfits: Save favorite outfit combinations for future reference
  - Individual Item Details: View detailed information about each clothing item, including colors, occasions, and weather suitability
  - Image Preview: Enlarge and view clothing items individually
  - Context Menu: Right-click on items for quick actions (view details, mark as unavailable, remove)
  - Responsive Design: Works seamlessly across desktop and mobile devices


Technology Stack:

  Frontend
  
  - HTML/CSS/JavaScript: Core web technologies for UI implementation
  - Responsive Design: Mobile-friendly interface with adaptive layouts
  - Custom CSS: Hand-crafted styles for a consistent and appealing user experience

  Backend
  
  - Python: Core programming language
  - Flask: Web framework
  - Jinja2: Templating engine for dynamic HTML rendering
  - MongoDB: NoSQL database for storing user data and clothing items
  - Flask-PyMongo: MongoDB integration for Flask

  AI & Machine Learning
  
  - Google Cloud Vision API: Image analysis for color extraction and basic categorization
  - Google Gemini 2.0 Flash API: Advanced clothing categorization, occasion detection, and weather suitability analysis
  - Custom Algorithms: Color matching, outfit generation, and weather-appropriate outfit selection algorithms

  External Services
  
  - OpenWeather API: Real-time weather data for location-based outfit recommendations
  - Google Cloud Storage: Cloud storage for clothing item images


Installation & Setup:

  Prerequisites
  
  - Python 3.8+
  - MongoDB
  - Google Cloud account (for Vision API and Storage)
  - Gemini API key
  - OpenWeather API key

  Environment Variables
  The following environment variables are required:
  
  - MONGODB_URI: MongoDB connection string
  - GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_CREDENTIALS_JSON: Google Cloud credentials
  - GEMINI_API_KEY: API key for Google's Gemini model
  - OPENWEATHER_API_KEY: API key for OpenWeather API

  Installation Steps
  
  - Clone the repository
  - Install dependencies: pip install -r requirements.txt
  - Set up environment variables (see above)
  - Run the application: python backend/app.py


Possible Future Enhancements:
  
- Event Planning: Sync with calendars to plan outfits for upcoming occasions
- Shopping Integration: Recommend complementary items for purchase to enhance wardrobe
- Style-Based Matching: Identify and suggest outfits based on specific fashion styles
