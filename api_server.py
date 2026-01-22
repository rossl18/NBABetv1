"""
Simple API server for dashboard
Can be deployed to Vercel, Netlify, or run locally
For GitHub Pages, you'll need a serverless function or use static JSON files
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from save_to_database import get_latest_props_from_database
from export_to_json import export_for_dashboard
import os

app = Flask(__name__)
CORS(app)

@app.route('/api/bets', methods=['GET'])
def get_bets():
    """Get latest bets from database"""
    try:
        limit = request.args.get('limit', 1000, type=int)
        df = get_latest_props_from_database(limit=limit)
        # Convert to dict format
        bets = df.to_dict('records')
        return jsonify(bets)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reload', methods=['POST'])
def reload_bets():
    """Trigger reload of betting data"""
    try:
        # This would run the export script
        # In production, you might want to queue this as a background job
        df = export_for_dashboard()
        return jsonify({
            'success': True,
            'count': len(df) if df is not None else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/performance', methods=['GET'])
def get_performance():
    """Get performance tracking data"""
    # TODO: Implement performance tracking queries
    return jsonify({
        'totalBets': 0,
        'wins': 0,
        'losses': 0,
        'winRate': 0,
        'totalProfit': 0,
        'roi': 0
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
