#!/bin/sh
echo "📦 Installed packages:"
pip list
echo "🚀 Starting Flask app..."
flask --app app run --host 0.0.0.0