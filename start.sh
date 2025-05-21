#!/bin/sh
echo "📦 Installed packages:"
pip list
echo "🚀 Starting Flask app..."
flask --app app --host 0.0.0.0 -p $1