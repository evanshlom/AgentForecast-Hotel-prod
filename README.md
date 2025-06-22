# Wynn Resort Forecast AI

Real-time hotel operations forecasting using AI agent and WebSocket communication.

## Quick Demo

1. **Set your Anthropic API key in `.env` file:**
   ```
   ANTHROPIC_API_KEY=your-key-here
   ```

2. **Run the application:**
   ```bash
   docker-compose up --build
   ```

3. **Open browser:**
   - Frontend: http://localhost:3567

4. **Try these commands:**
   - "Big UFC fight this Saturday"
   - "Convention next Monday morning"
   - "Pool party season starting"

## Project Structure

```
AgentForecast-Hotel/
│   .env                    # Your Anthropic API key
│   .gitignore
│   LICENSE
│   README.md              # This file
│   docker-compose.yml     # Runs everything
│
├───backend/
│       agent.py           # Anthropic AI agent (ForecastAgent)
│       data.py            # Data generation utilities
│       Dockerfile         # Backend container
│       main.py            # WebSocket server (glue code)
│       model.py           # RNN forecast model (ForecastModel)
│       requirements.txt   # Python dependencies
│
└───frontend/
        app.jsx            # React application
        Dockerfile         # Frontend container
        index.html         # Main HTML
        styles.css         # Styling
```

## How It Works

1. **RNN Model** generates a 7-day hourly forecast at startup
2. **WebSocket** connects frontend to backend in real-time
3. **AI Agent** interprets natural language and modifies forecast
4. **Live Updates** broadcast changes to all connected clients

## Architecture

- **Backend**: Python WebSocket server on port 8567
- **Frontend**: React app served by nginx on port 3567
- **AI**: Anthropic Claude for natural language understanding
- **State**: Single shared forecast modified by agent

## Troubleshooting

- **Connection failed?** Check if Docker is running
- **Port conflict?** Change ports in docker-compose.yml
- **API key error?** Verify .env file has correct key
- **Import errors?** All backend files should be in flat structure

## License

MIT