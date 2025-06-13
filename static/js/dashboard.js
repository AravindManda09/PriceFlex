document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard charts
    initDashboardCharts();
    
    // Set up event listeners
    document.querySelectorAll('.date-range-selector').forEach(function(element) {
        element.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all buttons
            document.querySelectorAll('.date-range-selector').forEach(function(el) {
                el.classList.remove('active');
            });
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Get selected days
            const days = parseInt(this.dataset.days);
            
            // Update charts
            updateDashboardData(days);
        });
    });
});

function initDashboardCharts() {
    // Initialize sales chart
    const salesCtx = document.getElementById('salesChart');
    if (salesCtx) {
        const salesData = JSON.parse(salesCtx.dataset.sales || '[]');
        
        // Extract dates and revenues
        const dates = salesData.map(item => item.date);
        const revenues = salesData.map(item => item.revenue);
        
        window.salesChart = new Chart(salesCtx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Daily Revenue',
                    data: revenues,
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    borderColor: 'rgba(0, 123, 255, 1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Revenue: ₹${context.raw.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxTicksLimit: 7
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '₹' + value;
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Initialize recommendations distribution chart
    const recommendationsCtx = document.getElementById('recommendationsChart');
    if (recommendationsCtx) {
        window.recommendationsChart = new Chart(recommendationsCtx, {
            type: 'doughnut',
            data: {
                labels: ['Price Increase', 'Price Decrease', 'No Change'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: [
                        'rgba(40, 167, 69, 0.8)',
                        'rgba(220, 53, 69, 0.8)',
                        'rgba(108, 117, 125, 0.8)'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                },
                cutout: '70%'
            }
        });
        
        // Update recommendations chart with initial data
        updateRecommendationsChart();
    }
}

function updateDashboardData(days) {
    // Fetch dashboard data for the selected date range
    fetch(`/api/dashboard_data?days=${days}`)
        .then(response => response.json())
        .then(data => {
            // Update sales chart
            if (window.salesChart) {
                window.salesChart.data.labels = data.daily_sales.map(item => item.date);
                window.salesChart.data.datasets[0].data = data.daily_sales.map(item => item.revenue);
                window.salesChart.update();
            }
        })
        .catch(error => {
            console.error('Error fetching dashboard data:', error);
        });
}

function updateRecommendationsChart() {
    // Get all recommendation elements
    const recommendations = document.querySelectorAll('.recommendation-item');
    
    // Count recommendations by type
    let increases = 0;
    let decreases = 0;
    let noChange = 0;
    
    recommendations.forEach(rec => {
        const currentPrice = parseFloat(rec.dataset.currentPrice);
        const recommendedPrice = parseFloat(rec.dataset.recommendedPrice);
        
        if (recommendedPrice > currentPrice) {
            increases++;
        } else if (recommendedPrice < currentPrice) {
            decreases++;
        } else {
            noChange++;
        }
    });
    
    // Update chart
    if (window.recommendationsChart) {
        window.recommendationsChart.data.datasets[0].data = [increases, decreases, noChange];
        window.recommendationsChart.update();
    }
}
