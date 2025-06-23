const { useState, useEffect, useRef } = React;

function App() {
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [forecast, setForecast] = useState(null);
    const [modifications, setModifications] = useState([]);
    const [wsConnected, setWsConnected] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    
    const ws = useRef(null);
    const chartRef = useRef(null);
    const chartInstance = useRef(null);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        // Initialize WebSocket connection
        connectWebSocket();
        
        return () => {
            if (ws.current) {
                ws.current.close();
            }
        };
    }, []);

    const connectWebSocket = () => {
        // Connect to backend WebSocket server
        const wsUrl = window.location.hostname === 'localhost' 
            ? 'ws://localhost:8567' 
            : `ws://${window.location.hostname}:8567`;
        
        ws.current = new WebSocket(wsUrl);
        
        ws.current.onopen = () => {
            console.log('WebSocket connected');
            setWsConnected(true);
            setMessages([{
                type: 'system',
                text: 'Connected to Wynn Resort Forecast AI!'
            }]);
        };
        
        ws.current.onmessage = (event) => {
            const message = JSON.parse(event.data);
            handleWebSocketMessage(message);
        };
        
        ws.current.onerror = (error) => {
            console.error('WebSocket error:', error);
            setMessages(prev => [...prev, {
                type: 'system',
                text: 'Connection error. Please refresh the page.'
            }]);
        };
        
        ws.current.onclose = () => {
            console.log('WebSocket disconnected');
            setWsConnected(false);
            setMessages(prev => [...prev, {
                type: 'system',
                text: 'Disconnected from server. Attempting to reconnect...'
            }]);
            
            // Attempt to reconnect after 3 seconds
            setTimeout(() => {
                connectWebSocket();
            }, 3000);
        };
    };

    const handleWebSocketMessage = (message) => {
        switch (message.type) {
            case 'initial_data':
                setForecast(message.data.forecast);
                setModifications(message.data.modifications || []);
                break;
                
            case 'agent_response':
                setMessages(prev => [...prev, {
                    type: 'ai',
                    text: message.data.response
                }]);
                setIsLoading(false);
                break;
                
            case 'forecast_update':
                setForecast(message.data.forecast);
                if (message.data.modifications !== undefined) {
                    setModifications(message.data.modifications);
                }
                setMessages(prev => [...prev, {
                    type: 'system',
                    text: 'Forecast updated with new modifications!'
                }]);
                break;
                
            default:
                console.log('Unknown message type:', message.type);
        }
    };

    useEffect(() => {
        // Scroll to bottom when messages change
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    useEffect(() => {
        // Update chart when forecast data changes
        if (forecast && chartRef.current) {
            updateChart(forecast);
        }
    }, [forecast]);

    const updateChart = (forecastData) => {
        if (!chartRef.current || !forecastData) return;

        const ctx = chartRef.current.getContext('2d');
        
        // Destroy existing chart
        if (chartInstance.current) {
            chartInstance.current.destroy();
        }

        // Prepare labels with custom formatting
        const labels = forecastData.map(d => {
            const date = new Date(d.date);
            const hours = date.getHours();
            const dateStr = date.toLocaleDateString('en-US', { month: '2-digit', day: '2-digit' });
            
            // Show date at midnight, hours otherwise
            if (hours === 0) {
                return dateStr;
            } else if (hours % 6 === 0) {
                return hours.toString().padStart(2, '0') + ':00';
            }
            return '';
        });
        
        chartInstance.current = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Rooms (Forecast)',
                        data: forecastData.map(d => d.rooms),
                        borderColor: 'goldenrod',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        tension: 0,
                        pointRadius: 0
                    },
                    {
                        label: 'Cleaning (Forecast)',
                        data: forecastData.map(d => d.cleaning),
                        borderColor: 'royalblue',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        tension: 0,
                        pointRadius: 0
                    },
                    {
                        label: 'Security (Forecast)',
                        data: forecastData.map(d => d.security),
                        borderColor: 'crimson',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        tension: 0,
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Hotel Staff Forecast - All Metrics',
                        font: {
                            size: 16
                        }
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        title: {
                            display: true,
                            text: 'Count / Percentage'
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 0,
                            autoSkip: false,
                            font: function(context) {
                                const label = context.tick.label;
                                // Bold font for dates
                                if (label && label.includes('/')) {
                                    return {
                                        size: 10,
                                        weight: 'bold'
                                    };
                                }
                                return {
                                    size: 8
                                };
                            }
                        },
                        grid: {
                            display: true,
                            drawOnChartArea: true,
                            drawTicks: true,
                            color: function(context) {
                                const label = context.tick.label;
                                if (label && label.includes('/')) {
                                    return 'rgba(0, 0, 0, 0.2)';
                                }
                                return 'rgba(0, 0, 0, 0.05)';
                            }
                        }
                    }
                }
            }
        });
    };

    const sendMessage = () => {
        if (!inputValue.trim() || !wsConnected) return;

        // Add user message
        setMessages(prev => [...prev, {
            type: 'user',
            text: inputValue
        }]);

        // Send through WebSocket
        ws.current.send(JSON.stringify({
            type: 'chat_message',
            data: {
                message: inputValue
            }
        }));

        setInputValue('');
        setIsLoading(true);
    };

    const clearModifications = () => {
        if (!wsConnected) return;
        
        ws.current.send(JSON.stringify({
            type: 'clear_modifications'
        }));
        
        setMessages(prev => [...prev, {
            type: 'system',
            text: 'Resetting to original forecast...'
        }]);
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    return (
        <div className="container">
            <div className="chat-panel">
                <div className="chat-header">
                    <div>Wynn Resort Forecast AI</div>
                    <div className={`connection-status ${wsConnected ? 'connected' : 'disconnected'}`}>
                        {wsConnected ? '●' : '○'}
                    </div>
                </div>
                <div className="chat-messages">
                    {messages.map((msg, idx) => (
                        <div key={idx} className={`message ${msg.type}-message`}>
                            {msg.text}
                        </div>
                    ))}
                    {isLoading && (
                        <div className="message ai-message loading">
                            <span className="loading-dots">Thinking</span>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
                <div className="chat-input">
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Ask about events, conventions, or operations..."
                        disabled={!wsConnected || isLoading}
                    />
                    <button 
                        onClick={sendMessage}
                        disabled={!wsConnected || isLoading || !inputValue.trim()}
                    >
                        Send
                    </button>
                </div>
            </div>
            <div className="chart-panel">
                <div className="chart-container">
                    <div className="chart-header">
                        <h2>Resort Operations Forecast</h2>
                        <div className="chart-controls">
                            <button onClick={clearModifications} disabled={!wsConnected || modifications.length === 0}>
                                Reset to Original Forecast
                            </button>
                        </div>
                    </div>
                    {modifications.length > 0 && (
                        <div className="modifications-panel">
                            <h3>Active Modifications</h3>
                            <div className="modifications-list">
                                {modifications.map((mod, idx) => (
                                    <div key={idx} className="modification-item">
                                        <strong>{mod.metric}</strong>: {mod.type} by {mod.value}
                                        <span className="mod-dates">
                                            ({mod.start_date} to {mod.end_date})
                                        </span>
                                        <span className="mod-reason">{mod.reason}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                    <div style={{ height: '400px', position: 'relative' }}>
                        <canvas ref={chartRef}></canvas>
                    </div>
                    {!forecast && (
                        <div className="placeholder">
                            <p>Waiting for forecast data...</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

ReactDOM.render(<App />, document.getElementById('root'));