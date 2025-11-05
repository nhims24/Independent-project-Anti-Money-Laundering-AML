let dailyChartInstance = null;
let categoryChartInstance = null;

// Load users on page load
document.addEventListener('DOMContentLoaded', () => {
    loadUsers();
    
    document.getElementById('analyzeBtn').addEventListener('click', analyzeUser);
});

async function loadUsers() {
    try {
        const response = await fetch('/api/users');
        const users = await response.json();
        
        const select = document.getElementById('userSelect');
        select.innerHTML = '<option value="">Select a user...</option>';
        
        users.forEach(user => {
            const option = document.createElement('option');
            option.value = JSON.stringify({id: user.id, pattern: user.pattern});
            option.textContent = user.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

async function analyzeUser() {
    const select = document.getElementById('userSelect');
    const selectedValue = select.value;
    
    if (!selectedValue) {
        alert('Please select a user first!');
        return;
    }
    
    const userData = JSON.parse(selectedValue);
    const userId = userData.id;
    const pattern = userData.pattern;
    
    // Show loading spinner
    document.getElementById('loadingSpinner').classList.remove('hidden');
    document.getElementById('resultsSection').classList.add('hidden');
    
    try {
        const response = await fetch(`/api/analyze/${userId}?pattern=${pattern}`);
        const data = await response.json();
        
        // Hide loading, show results
        document.getElementById('loadingSpinner').classList.add('hidden');
        document.getElementById('resultsSection').classList.remove('hidden');
        
        // Update risk assessment
        updateRiskAssessment(data.detection);
        
        // Update statistics
        updateStatistics(data.features);
        
        // Update charts
        updateCharts(data.charts);
        
        // Update transactions table
        updateTransactionsTable(data.transactions);
        
    } catch (error) {
        console.error('Error analyzing user:', error);
        document.getElementById('loadingSpinner').classList.add('hidden');
        alert('Error analyzing transactions. Please try again.');
    }
}

function updateRiskAssessment(detection) {
    document.getElementById('riskScore').textContent = detection.risk_score;
    document.getElementById('riskLevel').textContent = detection.risk_level;
    
    const flagsList = document.getElementById('flagsList');
    flagsList.innerHTML = '';
    
    if (detection.flags.length === 0) {
        flagsList.innerHTML = '<div class="flag-item">✅ No suspicious activity detected</div>';
    } else {
        detection.flags.forEach(flag => {
            const flagDiv = document.createElement('div');
            flagDiv.className = 'flag-item';
            flagDiv.textContent = '⚠️ ' + flag;
            flagsList.appendChild(flagDiv);
        });
    }
}

function updateStatistics(features) {
    document.getElementById('totalTxn').textContent = features.total_transactions;
    document.getElementById('avgAmount').textContent = '$' + features.avg_amount.toFixed(2);
    document.getElementById('txnPerDay').textContent = features.transactions_per_day.toFixed(2);
    document.getElementById('nearThreshold').textContent = features.near_threshold_count;
}

function updateCharts(charts) {
    // Update daily spending chart
    const dailyCtx = document.getElementById('dailyChart').getContext('2d');
    
    if (dailyChartInstance) {
        dailyChartInstance.destroy();
    }
    
    dailyChartInstance = new Chart(dailyCtx, {
        type: 'line',
        data: {
            labels: charts.daily_spending.map(d => d.date),
            datasets: [{
                label: 'Daily Spending ($)',
                data: charts.daily_spending.map(d => d.total_amount),
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(0);
                        }
                    }
                }
            }
        }
    });
    
    // Update category breakdown chart
    const categoryCtx = document.getElementById('categoryChart').getContext('2d');
    
    if (categoryChartInstance) {
        categoryChartInstance.destroy();
    }
    
    categoryChartInstance = new Chart(categoryCtx, {
        type: 'doughnut',
        data: {
            labels: charts.category_breakdown.map(c => c.category),
            datasets: [{
                data: charts.category_breakdown.map(c => c.amount),
                backgroundColor: [
                    '#667eea',
                    '#764ba2',
                    '#f093fb',
                    '#4facfe'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function updateTransactionsTable(transactions) {
    const tbody = document.getElementById('transactionsBody');
    tbody.innerHTML = '';
    
    transactions.forEach(txn => {
        const row = document.createElement('tr');
        
        const amountClass = txn.amount > 9000 ? 'amount-high' : '';
        
        row.innerHTML = `
            <td>${txn.id}</td>
            <td>${txn.date}</td>
            <td>${txn.type}</td>
            <td class="${amountClass}">$${txn.amount.toFixed(2)}</td>
            <td>${txn.description}</td>
        `;
        
        tbody.appendChild(row);
    });
}