document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('footprintChart');
    if (!canvas) return;

    // Fetch JSON blocks printed from Jinja templates
    const metricsDataEl = document.getElementById('metrics-data');
    const logsDataEl = document.getElementById('logs-data');
    
    const metrics = metricsDataEl ? JSON.parse(metricsDataEl.textContent) : [];
    const logs = logsDataEl ? JSON.parse(logsDataEl.textContent) : [];

    // Parse variables for target line plots
    let labels = [];
    let dataPoints = [];

    if (logs && logs.length > 0) {
        // Reverse logs array to display oldest to newest (chronological left-to-right)
        const chronologicalLogs = [...logs].reverse();
        chronologicalLogs.forEach((log) => {
            const date = new Date(log.timestamp);
            const dateLabel = date.toLocaleDateString(undefined, { 
                month: 'short', 
                day: 'numeric' 
            }) + ' ' + date.toLocaleTimeString(undefined, { 
                hour: '2-digit', 
                minute: '2-digit',
                hour12: false
            });
            labels.push(dateLabel);
            dataPoints.push(log.total_emissions);
        });
    } else {
        // Expose static beautiful mock curve trend line data if database holds no entries
        labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        dataPoints = [12.4, 15.8, 9.2, 14.5, 22.1, 18.4, 11.2];
    }

    const ctx = canvas.getContext('2d');
    
    // Generate smooth vertical linear gradient stretching down to background mask
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(16, 185, 129, 0.45)');  // High Emerald Green
    gradient.addColorStop(0.5, 'rgba(16, 185, 129, 0.15)'); // Soft Sage fading
    gradient.addColorStop(1, 'rgba(16, 185, 129, 0.0)');    // Transparent mask at base

    // Instantiate premium Curved Line Chart
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Carbon Emitted',
                data: dataPoints,
                borderColor: '#10B981',
                borderWidth: 3,
                backgroundColor: gradient,
                fill: true,
                tension: 0.4, // High tension produces smooth curves
                pointBackgroundColor: '#34D399',
                pointBorderColor: '#0d0d0d',
                pointBorderWidth: 2.5,
                pointRadius: 4,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: '#10B981',
                pointHoverBorderColor: '#F3F4F6',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false // Suppress legends to keep layout clean
                },
                tooltip: {
                    backgroundColor: 'rgba(13, 13, 13, 0.95)',
                    titleColor: '#F3F4F6',
                    titleFont: {
                        family: 'Plus Jakarta Sans',
                        weight: 'bold'
                    },
                    bodyColor: '#F3F4F6',
                    bodyFont: {
                        family: 'Plus Jakarta Sans'
                    },
                    borderColor: 'rgba(16, 185, 129, 0.3)',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return ` ${context.parsed.y.toFixed(2)} kg CO₂`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false // Disable aggressive gridlines
                    },
                    ticks: {
                        color: 'rgba(243, 244, 246, 0.4)',
                        font: {
                            family: 'Plus Jakarta Sans',
                            size: 10
                        }
                    },
                    border: {
                        display: false
                    }
                },
                y: {
                    grid: {
                        display: false // Disable aggressive gridlines
                    },
                    ticks: {
                        color: 'rgba(243, 244, 246, 0.4)',
                        font: {
                            family: 'Plus Jakarta Sans',
                            size: 10
                        }
                    },
                    border: {
                        display: false
                    }
                }
            }
        }
    });
});
