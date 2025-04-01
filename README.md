# AI News Aggregator

A web application that aggregates and displays articles from various publishers, organizing articles by subject areas. The application provides a clean interface to browse articles and view detailed summaries.

## Features

- Displays AI-related articles in a grid layout
- Each article card shows:
  - Article title
  - Brief summary
  - Featured image
- Click on any article to view:
  - Author information
  - Publisher details
  - Publication date
  - Detailed bullet-point summary
  - Link to the full article

## Setup

1. Clone this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory and add your News API key:
   ```
   NEWS_API_KEY=your_api_key_here
   ```
   You can get a free API key from [News API](https://newsapi.org/)

4. Run the application:
   ```bash
   python app.py
   ```
5. Open your browser and navigate to `http://localhost:5000`

## Technologies Used

- Python/Flask
- News API
- Bootstrap 5
- HTML/CSS/JavaScript

## Note

The application requires an active internet connection to fetch articles from the News API. 
