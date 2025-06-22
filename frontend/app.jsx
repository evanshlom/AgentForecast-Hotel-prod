const { useState, useEffect, useRef } = React;

function App() {
    const [messages, setMessages] = useState([
        {
            type: 'ai',
            text: 'Welcome to Wynn Resort Forecast AI! (Not connected - skeleton only)'
        }
    ]);
    const [inputValue, setInputValue] = useState('');
    const chartRef = useRef(null);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        // Scroll to bottom when messages change
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    useEffect(() => {
        // Create empty chart
        if (chartRef.current) {
            const ctx = chartRef.current.getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Hour 1', 'Hour 2', 'Hour 3', '...', 'Hour 168'],
                    datasets: [
                        {
                            label: 'Room Occupancy (%)',
                            data: [],
                            borderColor: '#DAA520',
                            backgroundColor: 'rgba(218, 165, 32, 0.1)'
                        },
                        {
                            label: 'Cleaning Staff Needed',
                            data: [],
                            borderColor: '#4169E1',
                            backgroundColor: 'rgba(65, 105, 225, 0.1)'
                        },
                        {
                            label: 'Security Staff Needed',
                            data: [],
                            borderColor: '#DC143C',
                            backgroundColor: 'rgba(220, 20, 60, 0.1)'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Wynn Resort 7-Day Hourly Forecast (No Data Yet)'
                        }
                    },
                    scales: {
                        y: {
                            title: {
                                display: true,
                                text: 'Units / Percentage'
                            }
                        }
                    }
                }
            });
        }
    }, []);

    const sendMessage = () => {
        if (!inputValue.trim()) return;

        // Add user message
        setMessages(prev => [...prev, {
            type: 'user',
            text: inputValue
        }]);

        // Simulate AI response (no backend yet)
        setTimeout(() => {
            setMessages(prev => [...prev, {
                type: 'ai',
                text: 'Backend not connected. This is just the UI skeleton for the tutorial.'
            }]);
        }, 500);

        setInputValue('');
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    };

    return (
        <div className="container">
            <div className="chat-panel">
                <div className="chat-header">
                    Wynn Resort Forecast AI 🎰
                </div>
                <div className="chat-messages">
                    {messages.map((msg, idx) => (
                        <div key={idx} className={`message ${msg.type}-message`}>
                            {msg.text}
                        </div>
                    ))}
                    <div ref={messagesEndRef} />
                </div>
                <div className="chat-input">
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Type a message..."
                    />
                    <button onClick={sendMessage}>
                        Send
                    </button>
                </div>
            </div>
            <div className="chart-panel">
                <div className="chart-container">
                    <h2>Resort Operations Forecast</h2>
                    <div style={{ height: '400px', position: 'relative' }}>
                        <canvas ref={chartRef}></canvas>
                    </div>
                    <div className="placeholder">
                        <p>Chart will display 168-hour forecast once backend is connected</p>
                    </div>
                </div>
            </div>
        </div>
    );
}

ReactDOM.render(<App />, document.getElementById('root'));