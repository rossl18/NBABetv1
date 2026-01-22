// Dashboard JavaScript - loads and displays betting data

// All-star players list (update as needed)
const ALL_STAR_PLAYERS = [
  'LeBron James', 'Stephen Curry', 'Kevin Durant', 'Giannis Antetokounmpo',
  'Luka Doncic', 'Jayson Tatum', 'Joel Embiid', 'Nikola Jokic',
  'Devin Booker', 'Damian Lillard', 'Anthony Davis', 'Kawhi Leonard',
  'Jimmy Butler', 'Paul George', 'Kyrie Irving', 'Donovan Mitchell',
  'Jaylen Brown', 'Pascal Siakam', 'Bam Adebayo', 'DeMar DeRozan',
  'Zach LaVine', 'Karl-Anthony Towns', 'Anthony Edwards', 'Ja Morant',
  'Trae Young', 'De\'Aaron Fox', 'Shai Gilgeous-Alexander', 'Tyrese Haliburton'
];

let allBets = [];
let filteredBets = [];

// Load bets from JSON file
async function loadBets() {
    try {
        const response = await fetch('data/latest-bets.json');
        if (!response.ok) {
            throw new Error('Failed to load bets data');
        }
        allBets = await response.json();
        
        // Populate prop type filter
        const propTypes = [...new Set(allBets.map(bet => bet.Prop).filter(Boolean))].sort();
        const propTypeSelect = document.getElementById('propTypeSelect');
        propTypes.forEach(prop => {
            const option = document.createElement('option');
            option.value = prop;
            option.textContent = prop;
            propTypeSelect.appendChild(option);
        });
        
        applyFilters();
        updateStats();
    } catch (error) {
        console.error('Error loading bets:', error);
        document.getElementById('betsGrid').innerHTML = 
            '<div class="no-bets">Error loading bets. Make sure data/latest-bets.json exists. Run: python export_to_json.py</div>';
    }
}

// Apply filters and sorting
function applyFilters() {
    const filter = document.getElementById('filterSelect').value;
    const allStarFilter = document.getElementById('allStarSelect').value;
    const propTypeFilter = document.getElementById('propTypeSelect').value;
    const sortBy = document.getElementById('sortSelect').value;
    
    // Filter
    filteredBets = allBets.filter(bet => {
        // EV filter
        if (filter === 'positive' && (bet.Expected_Value || 0) <= 0) return false;
        if (filter === 'high-value' && (bet.Expected_Value || 0) <= 0.10) return false;
        
        // All-star filter
        const playerName = bet.Player || '';
        if (allStarFilter === 'all-star') {
            if (!ALL_STAR_PLAYERS.some(star => playerName.includes(star) || star.includes(playerName))) return false;
        }
        if (allStarFilter === 'non-all-star') {
            if (ALL_STAR_PLAYERS.some(star => playerName.includes(star) || star.includes(playerName))) return false;
        }
        
        // Prop type filter
        const propType = bet.Prop || '';
        if (propTypeFilter !== 'all' && propType !== propTypeFilter) return false;
        
        return true;
    });
    
    // Sort
    filteredBets.sort((a, b) => {
        if (sortBy === 'ev') {
            return (b.Expected_Value || 0) - (a.Expected_Value || 0);
        }
        if (sortBy === 'confidence') {
            return (b.Confidence_Score || 0) - (a.Confidence_Score || 0);
        }
        if (sortBy === 'kelly') {
            return (b.Kelly_Fraction || 0) - (a.Kelly_Fraction || 0);
        }
        return 0;
    });
    
    // Update props count
    document.getElementById('propsCount').textContent = `Showing ${filteredBets.length} of ${allBets.length} props`;
    
    renderBets();
}

// Update statistics
function updateStats() {
    const stats = {
        total: allBets.length,
        positiveEV: allBets.filter(b => (b.Expected_Value || 0) > 0).length,
        highValue: allBets.filter(b => (b.Expected_Value || 0) > 0.10).length,
        avgEV: allBets.length > 0 
            ? (allBets.reduce((sum, b) => sum + (b.Expected_Value || 0), 0) / allBets.length).toFixed(3)
            : 0
    };
    
    document.getElementById('statsGrid').innerHTML = `
        <div class="stat-card">
            <div class="stat-value">${stats.total}</div>
            <div class="stat-label">Total Props</div>
        </div>
        <div class="stat-card positive">
            <div class="stat-value">${stats.positiveEV}</div>
            <div class="stat-label">Positive EV</div>
        </div>
        <div class="stat-card high-value">
            <div class="stat-value">${stats.highValue}</div>
            <div class="stat-label">High Value (10%+)</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${stats.avgEV > 0 ? '+' : ''}${stats.avgEV}%</div>
            <div class="stat-label">Average EV</div>
        </div>
    `;
}

// Render bet cards
function renderBets() {
    const grid = document.getElementById('betsGrid');
    
    if (filteredBets.length === 0) {
        grid.innerHTML = '<div class="no-bets">No bets found. Try adjusting your filters.</div>';
        return;
    }
    
    grid.innerHTML = filteredBets.map(bet => createBetCard(bet)).join('');
}

// Create a bet card HTML
function createBetCard(bet) {
    const ev = bet.Expected_Value || 0;
    const prob = bet.Model_Probability || 0;
    const confidence = bet.Confidence_Score || 0;
    const kelly = bet.Kelly_Fraction || 0;
    
    const evClass = ev > 0.10 ? 'positive' : ev > 0 ? 'neutral' : 'negative';
    const evColor = ev > 0.10 ? '#10b981' : ev > 0 ? '#f59e0b' : '#ef4444';
    const confColor = confidence > 0.7 ? '#10b981' : confidence > 0.5 ? '#f59e0b' : '#ef4444';
    
    // Calculate EV meter position (-20% to +20% range)
    const normalizedEV = Math.max(-0.20, Math.min(0.20, ev));
    const meterPercent = ((normalizedEV + 0.20) / 0.40) * 100;
    
    return `
        <div class="bet-card">
            <div class="bet-header">
                <div class="player-name">${bet.Player}</div>
                <div class="prop-type">${bet.Prop}</div>
            </div>
            
            <div class="bet-details">
                <div class="detail-row">
                    <span class="label">Line:</span>
                    <span class="value">${bet.Line} ${bet['Over/Under']}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Odds:</span>
                    <span class="value">${bet.Odds > 0 ? '+' : ''}${bet.Odds}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Probability:</span>
                    <span class="value">${(prob * 100).toFixed(1)}%</span>
                </div>
            </div>
            
            <div class="ev-section">
                <div class="ev-meter-container">
                    <div class="ev-meter-track">
                        <div class="ev-meter-fill" style="width: ${meterPercent}%; left: ${meterPercent < 50 ? 50 : 50}%; transform: ${meterPercent < 50 ? 'scaleX(-1)' : 'none'}; background-color: ${evColor};"></div>
                        <div class="ev-meter-center"></div>
                    </div>
                    <div class="ev-meter-labels">
                        <span>-20%</span>
                        <span>0%</span>
                        <span>+20%</span>
                    </div>
                </div>
                <div class="ev-details">
                    <div class="ev-value ${evClass}">${ev > 0 ? '+' : ''}${(ev * 100).toFixed(2)}%</div>
                    <div class="ev-label">Expected Value</div>
                    ${bet.EV_CI_Lower !== null && bet.EV_CI_Upper !== null ? 
                        `<div class="ev-ci">95% CI: [${((bet.EV_CI_Lower || 0) * 100).toFixed(1)}%, ${((bet.EV_CI_Upper || 0) * 100).toFixed(1)}%]</div>` : ''}
                </div>
            </div>
            
            <div class="metrics-row">
                <div class="metric">
                    <div class="metric-label">Confidence</div>
                    <div class="metric-bar">
                        <div class="metric-fill" style="width: ${confidence * 100}%; background-color: ${confColor};"></div>
                    </div>
                    <div class="metric-value">${(confidence * 100).toFixed(0)}%</div>
                </div>
                ${kelly > 0 ? `
                <div class="metric">
                    <div class="metric-label">Kelly</div>
                    <div class="metric-value kelly">${(kelly * 100).toFixed(1)}%</div>
                </div>
                ` : ''}
            </div>
            
            ${bet.Edge ? `
            <div class="edge-badge">
                Edge: ${bet.Edge > 0 ? '+' : ''}${(bet.Edge * 100).toFixed(1)}%
            </div>
            ` : ''}
        </div>
    `;
}

// Reload bets (triggers data refresh) - Admin only
function reloadBets() {
    // Password protection - only admin can reload
    const password = prompt('Enter admin password to reload bets:');
    if (password !== 'admin123') { // Change this password!
        alert('Access denied. Only admin can reload bets.');
        return;
    }
    
    const btn = document.querySelector('.reload-btn');
    btn.disabled = true;
    btn.textContent = 'Reloading...';
    
    // In a real implementation, this would call an API
    // For static site, just reload the page after a delay
    setTimeout(() => {
        location.reload();
    }, 1000);
}

// Check if admin mode is enabled via URL parameter
function checkAdminMode() {
    const urlParams = new URLSearchParams(window.location.search);
    const isAdmin = urlParams.get('admin') === 'true';
    const reloadBtn = document.getElementById('reloadBtn');
    if (reloadBtn) {
        reloadBtn.style.display = isAdmin ? 'block' : 'none';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    checkAdminMode();
    loadBets();
});
