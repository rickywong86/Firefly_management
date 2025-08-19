from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, sessions, jsonify, make_response, Response
)

from werkzeug.exceptions import abort

from app.db import get_db
import io, csv
import pandas as pd
from . import home
from .models import category as Category
import json
from .forms import CategoryForm
from . import database

bp = Blueprint('category', __name__)

@bp.route('/category')
def index():
    """
    Main page route, displaying a paginated and searchable list of categories.
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search_query = request.args.get('search', '', type=str)
    highlight_id = request.args.get('highlight_id', None, type=int)

    query = Category.query
    if search_query:
        query = query.filter(Category.key.ilike(f'%{search_query}%'))

    pagination = query.paginate(page=page, per_page=per_page)
    return render_template('category/index.html', pagination=pagination, search_query=search_query, highlight_id=highlight_id, per_page=per_page)

@bp.route('/category/create', methods=['POST'])
def create_category():
    """
    Handles the creation of a new category.
    """
    key = request.form.get('key')
    category = request.form.get('category')
    destinationAcc = request.form.get('destinationAcc')
    new_category = Category(key=key, category=category, destinationAcc=destinationAcc)
    database.session.add(new_category)
    database.session.commit()
    flash('Category created successfully!', 'success')
    return redirect(url_for('category.index', highlight_id=new_category.id))

@bp.route('/category/<int:category_id>/update', methods=['POST'])
def update_category(category_id):
    """
    Handles the update of an existing category.
    """
    category_record = Category.query.get_or_404(category_id)
    category_record.key = request.form.get('key')
    category_record.category = request.form.get('category')
    category_record.destinationAcc = request.form.get('destinationAcc')
    database.session.commit()
    flash('Category updated successfully!', 'success')
    return redirect(url_for('category.index', highlight_id=category_record.id))

@bp.route('/category/<int:category_id>/delete', methods=['POST'])
def delete_category(category_id):
    """
    Handles the deletion of a category.
    """
    category_record = Category.query.get_or_404(category_id)
    database.session.delete(category_record)
    database.session.commit()
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('category.index'))

@bp.route('/category/<int:category_id>/details', methods=['GET'])
def get_category_details(category_id):
    """
    API endpoint to get category details in JSON format.
    """
    category_record = Category.query.get_or_404(category_id)
    return jsonify({
        'id': category_record.id,
        'key': category_record.key,
        'category': category_record.category,
        'destinationAcc': category_record.destinationAcc
    })

@bp.route('/categories/list', methods=['GET'])
def get_categories():
    """
    API endpoint to get a list of all categories.
    """
    categories = Category.query.all()
    categories_data = [{
        'key': c.key,
        'category': c.category,
        'destinationAcc': c.destinationAcc
    } for c in categories]
    return jsonify(categories_data)

@bp.route('/categories/upload', methods=['POST'])
def upload_categories():
    """Handles CSV file uploads for categories."""
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    
    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.reader(stream)
        headers = [h.strip() for h in next(reader)]
        
        # Check for expected headers
        if not all(h in headers for h in ['key', 'category', 'destinationAcc']):
            return jsonify({'message': 'CSV must contain key, category, and destinationAcc columns'}), 400

        # Mapping for column order
        header_map = {h: headers.index(h) for h in headers}

        imported_count = 0
        for row in reader:
            if not row: continue
            
            new_cat = Category(
                key=row[header_map['key']],
                category=row[header_map['category']],
                destinationAcc=row[header_map['destinationAcc']]
            )
            database.session.add(new_cat)
            imported_count += 1
        
        database.session.commit()
        return jsonify({'message': f'{imported_count} categories imported successfully!'})
    except Exception as e:
        return jsonify({'message': f'Error processing file: {str(e)}'}), 500
    
@bp.route('/categories/export_csv', methods=['GET'])
def export_categories():
    """Exports all categories to a CSV file."""
    categories = Category.query.all()

    si = io.StringIO()
    cw = csv.writer(si)
    
    headers = ['key', 'category', 'destinationAcc']
    cw.writerow(headers)

    for c in categories:
        row = [
            c.key,
            c.category,
            c.destinationAcc,
        ]
        cw.writerow(row)

    output = si.getvalue()
    si.close()

    filename = "categories_export.csv"
    
    response = Response(output, mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response