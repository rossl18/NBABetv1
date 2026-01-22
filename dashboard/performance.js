// Performance page JavaScript

let performanceData = null;

async function loadPerformance() {
    try {
        const response = await fetch('data/performance.json');
        if (!response.ok) {
            throw new Error('Failed to load performance data');
        }
        performanceData = await response.json();
        // Only render if there's actual data
        if (performanceData && performanceData.totalBets > 0) {
            renderPerformance();
        } else {
            renderEmptyState();
        }
    } catch (error) {
        console.error('Error loading performance:', error);
        renderEmptyState();
    }
}

function renderEmptyState() {
    document.getElementById('statsGrid').innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: #666;">
            <p style="font-size: 1.2rem; margin-bottom: 1rem;">No performance data available yet.</p>
            <p>Performance tracking will appear here once predictions have been made and outcomes have been recorded.</p>
        </div>
    `;
    // Hide charts section
    const chartsSection = document.querySelector('.charts-section');
    if (chartsSection) {
        chartsSection.style.display = 'none';
    }
    // Clear any existing charts
    const profitChart = document.getElementById('profitChart');
    const propChart = document.getElementById('propChart');
    if (profitChart) profitChart.style.display = 'none';
    if (propChart) propChart.style.display = 'none';
}

function renderPerformance() {
    if (!performanceData || performanceData.totalBets === 0) {
        renderEmptyState();
        return;
    }
    
    // Show charts section
    const chartsSection = document.querySelector('.charts-section');
    if (chartsSection) {
        chartsSection.style.display = 'grid';
    }
    
    // Update stats
    document.getElementById('statsGrid').innerHTML = `
        <div class="stat-card">
            <div class="stat-value">${performanceData.totalBets}</div>
            <div class="stat-label">Total Bets</div>
        </div>
        <div class="stat-card positive">
            <div class="stat-value">${performanceData.wins}</div>
            <div class="stat-label">Wins</div>
        </div>
        <div class="stat-card negative">
            <div class="stat-value">${performanceData.losses}</div>
            <div class="stat-label">Losses</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${performanceData.winRate}%</div>
            <div class="stat-label">Win Rate</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${performanceData.roi}%</div>
            <div class="stat-label">ROI</div>
        </div>
    `;
    
    // Render charts
    renderProfitChart();
    renderPropChart();
}

function renderProfitChart() {
    const ctx = document.getElementById('profitChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: performanceData.overTime.map(d => d.date),
            datasets: [{
                label: 'Cumulative Profit',
                data: performanceData.overTime.map(d => d.cumulative),
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function renderPropChart() {
    const ctx = document.getElementById('propChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: performanceData.byProp.map(d => d.prop),
            datasets: [
                {
                    label: 'Wins',
                    data: performanceData.byProp.map(d => d.wins),
                    backgroundColor: '#10b981'
                },
                {
                    label: 'Losses',
                    data: performanceData.byProp.map(d => d.losses),
                    backgroundColor: '#ef4444'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true
                }
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    loadPerformance();
});
