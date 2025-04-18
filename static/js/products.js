document.addEventListener('DOMContentLoaded', function() {
    // Set up product detail charts
    initProductCharts();
    
    // Set up recommendation action buttons
    setupRecommendationButtons();
    
    // Set up form validation
    setupFormValidation();
});

function initProductCharts() {
    const productChartContainer = document.getElementById('productCharts');
    if (!productChartContainer) return;
    
    const productId = productChartContainer.dataset.productId;
    
    // Fetch product data
    fetch(`/api/product_data/${productId}`)
        .then(response => response.json())
        .then(data => {
            // Create price history chart
            createPriceHistoryChart(data.price_history, data.competitor_prices);
            
            // Create sales chart
            createSalesChart(data.sales);
        })
        .catch(error => {
            console.error('Error fetching product data:', error);
        });
}

function createPriceHistoryChart(priceHistory, competitorPrices) {
    const priceChartCtx = document.getElementById('priceHistoryChart');
    if (!priceChartCtx) return;
    
    // Group competitor prices by competitor
    const competitorGroups = {};
    competitorPrices.forEach(cp => {
        if (!competitorGroups[cp.competitor_name]) {
            competitorGroups[cp.competitor_name] = [];
        }
        competitorGroups[cp.competitor_name].push({
            date: cp.date,
            price: cp.price
        });
    });
    
    // Prepare datasets
    const datasets = [{
        label: 'Your Price',
        data: priceHistory.map(ph => ({
            x: ph.date,
            y: ph.price
        })),
        borderColor: 'rgba(0, 123, 255, 1)',
        backgroundColor: 'rgba(0, 123, 255, 0.1)',
        fill: false,
        borderWidth: 2,
        tension: 0.4
    }];
    
    // Add competitor datasets
    const colors = [
        'rgba(220, 53, 69, 1)',
        'rgba(255, 193, 7, 1)',
        'rgba(40, 167, 69, 1)',
        'rgba(111, 66, 193, 1)',
        'rgba(23, 162, 184, 1)',
    ];
    
    let colorIndex = 0;
    for (const [competitor, prices] of Object.entries(competitorGroups)) {
        datasets.push({
            label: competitor,
            data: prices.map(p => ({
                x: p.date,
                y: p.price
            })),
            borderColor: colors[colorIndex % colors.length],
            backgroundColor: 'transparent',
            borderWidth: 2,
            borderDash: [5, 5],
            tension: 0.4,
            pointRadius: 3
        });
        colorIndex++;
    }
    
    // Create chart
    new Chart(priceChartCtx, {
        type: 'line',
        data: {
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day',
                        displayFormats: {
                            day: 'MMM d'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Price ($)'
                    },
                    ticks: {
                        callback: function(value) {
                            return '$' + value;
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': $' + context.parsed.y.toFixed(2);
                        }
                    }
                }
            }
        }
    });
}

function createSalesChart(sales) {
    const salesChartCtx = document.getElementById('salesChart');
    if (!salesChartCtx || !sales.length) return;
    
    // Group sales by date
    const salesByDate = {};
    sales.forEach(sale => {
        if (!salesByDate[sale.date]) {
            salesByDate[sale.date] = {
                quantity: 0,
                revenue: 0
            };
        }
        salesByDate[sale.date].quantity += sale.quantity;
        salesByDate[sale.date].revenue += sale.revenue;
    });
    
    // Convert to arrays
    const dates = Object.keys(salesByDate).sort();
    const quantities = dates.map(date => salesByDate[date].quantity);
    const revenues = dates.map(date => salesByDate[date].revenue);
    
    // Create chart
    new Chart(salesChartCtx, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Units Sold',
                    data: quantities,
                    backgroundColor: 'rgba(0, 123, 255, 0.7)',
                    borderColor: 'rgba(0, 123, 255, 1)',
                    borderWidth: 1,
                    yAxisID: 'y'
                },
                {
                    label: 'Revenue',
                    data: revenues,
                    type: 'line',
                    backgroundColor: 'transparent',
                    borderColor: 'rgba(40, 167, 69, 1)',
                    borderWidth: 2,
                    pointRadius: 3,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Units Sold'
                    },
                    position: 'left'
                },
                y1: {
                    title: {
                        display: true,
                        text: 'Revenue ($)'
                    },
                    position: 'right',
                    grid: {
                        drawOnChartArea: false
                    },
                    ticks: {
                        callback: function(value) {
                            return '$' + value;
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            if (context.dataset.label === 'Revenue') {
                                return context.dataset.label + ': $' + context.parsed.y.toFixed(2);
                            }
                            return context.dataset.label + ': ' + context.parsed.y;
                        }
                    }
                }
            }
        }
    });
}

function setupRecommendationButtons() {
    // Apply recommendation buttons
    document.querySelectorAll('.apply-recommendation').forEach(button => {
        button.addEventListener('click', function() {
            const recommendationId = this.dataset.recommendationId;
            const recommendedPrice = this.dataset.recommendedPrice;
            
            // Set values in the form
            document.getElementById('new_price').value = recommendedPrice;
            document.getElementById('recommendation_id').value = recommendationId;
            
            // Show update modal
            const updatePriceModal = new bootstrap.Modal(document.getElementById('updatePriceModal'));
            updatePriceModal.show();
        });
    });
    
    // Reject recommendation buttons
    document.querySelectorAll('.reject-recommendation').forEach(button => {
        button.addEventListener('click', function() {
            // Mark recommendation as rejected via API call
            // This is not implemented in this version
            const recommendationItem = this.closest('.recommendation-item');
            recommendationItem.classList.add('recommendation-rejected');
            this.disabled = true;
            this.previousElementSibling.disabled = true;
        });
    });
}

function setupFormValidation() {
    // Product form validation
    const productForm = document.getElementById('productForm');
    if (productForm) {
        productForm.addEventListener('submit', function(event) {
            if (!productForm.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            productForm.classList.add('was-validated');
        });
    }
    
    // Sale form validation
    const saleForm = document.getElementById('saleForm');
    if (saleForm) {
        saleForm.addEventListener('submit', function(event) {
            if (!saleForm.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            saleForm.classList.add('was-validated');
        });
    }
    
    // Competitor form validation
    const competitorForm = document.getElementById('competitorForm');
    if (competitorForm) {
        competitorForm.addEventListener('submit', function(event) {
            if (!competitorForm.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            competitorForm.classList.add('was-validated');
        });
    }
}
