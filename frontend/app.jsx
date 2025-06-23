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
        connectWebSocket();
        return () => ws.current?.close();
    }, []);

    const connectWebSocket = () => {
        ws.current = new WebSocket(`ws://localhost:8567`);
        
        ws.current.onopen = () => {
            setWsConnected(true);
            setMessages([{ type: 'system', text: 'Connected to Wynn Resort Forecast AI!' }]);
        };
        
        ws.current.onmessage = (event) => {
            const message = JSON.parse(event.data);
            switch (message.type) {
                case 'initial_data':
                    setForecast(message.data.forecast);
                    setModifications(message.data.modifications || []);
                    break;
                case 'agent_response':
                    setMessages(prev => [...prev, { type: 'ai', text: message.data.response }]);
                    setIsLoading(false);
                    break;
                case 'forecast_update':
                    setForecast(message.data.forecast);
                    setModifications(message.data.modifications || []);
                    break;
            }
        };
        
        ws.current.onclose = () => {
            setWsConnected(false);
            setMessages(prev => [...prev, { type: 'system', text: 'Disconnected. Reconnecting...' }]);
            setTimeout(connectWebSocket, 3000);
        };
    };

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    useEffect(() => {
        if (forecast && chartRef.current) updateChart(forecast);
    }, [forecast]);

    const updateChart = (data) => {
        if (!chartRef.current) return;
        
        chartInstance.current?.destroy();
        
        const historical = data.filter(d => d.type === 'historical');
        const forecastOnly = data.filter(d => d.type === 'forecast');
        const labels = data.map(d => {
            const date = new Date(d.date);
            return date.getHours() === 0 
                ? date.toLocaleDateString('en-US', { month: '2-digit', day: '2-digit' })
                : date.getHours() % 6 === 0 ? `${date.getHours()}:00` : '';
        });
        
        chartInstance.current = new Chart(chartRef.current.getContext('2d'), {
            type: 'line',
            data: {
                labels,
                datasets: [
                    // Historical - solid
                    {
                        label: 'Rooms (Historical)',
                        data: [...historical.map(d => d.rooms), ...new Array(forecastOnly.length).fill(null)],
                        borderColor: 'goldenrod',
                        borderWidth: 2,
                        tension: 0,
                        pointRadius: 0
                    },
                    {
                        label: 'Cleaning (Historical)',
                        data: [...historical.map(d => d.cleaning), ...new Array(forecastOnly.length).fill(null)],
                        borderColor: 'royalblue',
                        borderWidth: 2,
                        tension: 0,
                        pointRadius: 0
                    },
                    {
                        label: 'Security (Historical)',
                        data: [...historical.map(d => d.security), ...new Array(forecastOnly.length).fill(null)],
                        borderColor: 'crimson',
                        borderWidth: 2,
                        tension: 0,
                        pointRadius: 0
                    },
                    // Forecast - dashed
                    {
                        label: 'Rooms (Forecast)',
                        data: [...new Array(historical.length).fill(null), ...forecastOnly.map(d => d.rooms)],
                        borderColor: 'goldenrod',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        tension: 0,
                        pointRadius: 0
                    },
                    {
                        label: 'Cleaning (Forecast)',
                        data: [...new Array(historical.length).fill(null), ...forecastOnly.map(d => d.cleaning)],
                        borderColor: 'royalblue',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        tension: 0,
                        pointRadius: 0
                    },
                    {
                        label: 'Security (Forecast)',
                        data: [...new Array(historical.length).fill(null), ...forecastOnly.map(d => d.security)],
                        borderColor: 'crimson',
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
                    title: { display: true, text: 'Hotel Staff Forecast - All Metrics', font: { size: 16 } },
                    legend: { display: true, position: 'top' }
                },
                scales: {
                    y: { title: { display: true, text: 'Count / Percentage' } },
                    x: { ticks: { maxRotation: 0, autoSkip: false } }
                }
            }
        });
    };

    const sendMessage = () => {
        if (!inputValue.trim() || !wsConnected) return;
        
        setMessages(prev => [...prev, { type: 'user', text: inputValue }]);
        ws.current.send(JSON.stringify({ type: 'chat_message', data: { message: inputValue } }));
        setInputValue('');
        setIsLoading(true);
    };

    const clearModifications = () => {
        if (!wsConnected) return;
        ws.current.send(JSON.stringify({ type: 'clear_modifications' }));
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
                        <div key={idx} className={`message ${msg.type}-message`}>{msg.text}</div>
                    ))}
                    {isLoading && <div className="message ai-message loading">Thinking...</div>}
                    <div ref={messagesEndRef} />
                </div>
                <div className="chat-input">
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                        placeholder="Ask about events, conventions, or operations..."
                        disabled={!wsConnected || isLoading}
                    />
                    <button onClick={sendMessage} disabled={!wsConnected || isLoading || !inputValue.trim()}>
                        Send
                    </button>
                </div>
            </div>
            <div className="chart-panel">
                <div className="chart-container">
                    <div className="chart-header">
                        <h2>Resort Operations Forecast</h2>
                        <button onClick={clearModifications} disabled={!wsConnected || modifications.length === 0}>
                            Reset to Original Forecast
                        </button>
                    </div>
                    {modifications.length > 0 && (
                        <div className="modifications-panel">
                            <h3>Active Modifications</h3>
                            {modifications.map((mod, idx) => (
                                <div key={idx} className="modification-item">
                                    <strong>{mod.metric}</strong>: {mod.type} by {mod.value}
                                    <span className="mod-dates"> ({mod.start_date} to {mod.end_date})</span>
                                    <div className="mod-reason">{mod.reason}</div>
                                </div>
                            ))}
                        </div>
                    )}
                    <div style={{ height: '400px', position: 'relative' }}>
                        <canvas ref={chartRef}></canvas>
                    </div>
                    {!forecast && <div className="placeholder">Waiting for forecast data...</div>}
                </div>
            </div>
        </div>
    );
}

ReactDOM.render(<App />, document.getElementById('root'));