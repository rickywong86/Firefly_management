from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, sessions, jsonify, make_response
)

from werkzeug.exceptions import abort

from app.db import get_db

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
