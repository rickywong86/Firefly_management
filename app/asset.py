# project/routes.py
# This file defines all the web routes for the application.

from flask import render_template, request, redirect, url_for, jsonify, Blueprint
from . import database
from .models import accounts, account_columns_map

# Create a Blueprint instance. The `template_folder` is set to find templates.
bp = Blueprint('asset', __name__)

@bp.route('/asset', methods=['GET'])
def index():
    """
    Renders the main interactive table page.
    Handles searching and pagination.
    """
    # Get current page number from URL, default to 1.
    page = request.args.get('page', 1, type=int)
    # Get search query from URL, default to empty string.
    search_query = request.args.get('search', '', type=str)
    # Get the ID of the last edited record for highlighting.
    highlight_id = request.args.get('highlight_id', None, type=str)

    per_page = request.args.get('per_page', 10, type=int)
    
    # Base query for all assets.
    query = accounts.query
    
    # If a search query is present, filter the results.
    if search_query:
        query = query.filter(accounts.account_name.contains(search_query))
    
    # Paginate the results. `per_page=10` displays 10 records per page.
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'asset/index.html',
        pagination=pagination,
        search_query=search_query,
        highlight_id=highlight_id,
        per_page=per_page
    )

@bp.route('/asset/create', methods=['POST'])
def create_asset():
    """
    Handles the creation of a new asset.
    """
    account_name = request.form.get('account_name', '')
    has_header = request.form.get('has_header') == 'on'
    
    new_asset = accounts(account_name=account_name, has_header=has_header)
    database.session.add(new_asset)
    database.session.commit()
    
    # Redirect to the main page and pass the new asset's ID for highlighting.
    return redirect(url_for('asset.index', highlight_id=new_asset.id))

@bp.route('/asset/<id>/update', methods=['POST'])
def update_asset(id):
    """
    Handles the update of an existing asset.
    """
    asset = accounts.query.get_or_404(id)
    asset.account_name = request.form.get('account_name', '')
    asset.has_header = request.form.get('has_header') == 'on'
    database.session.commit()
    
    # Redirect to the main page and pass the updated asset's ID for highlighting.
    return redirect(url_for('asset.index', highlight_id=asset.id))

@bp.route('/asset/<id>/delete', methods=['POST'])
def delete_asset(id):
    """
    Handles the deletion of an asset.
    """
    asset = accounts.query.get_or_404(id)
    database.session.delete(asset)
    database.session.commit()
    
    # Redirect to the main page after deletion.
    return redirect(url_for('asset.index'))

@bp.route('/assets/list', methods=['GET'])
def get_assets():
    """
    API endpoint to get a list of all assets.
    """
    assets = accounts.query.all()
    assets_data = [{
        'id': a.id,
        'name': a.account_name,
    } for a in assets]
    return jsonify(assets_data)

@bp.route('/asset/<id>/details', methods=['GET'])
def get_asset_details(id):
    """
    API endpoint to get an asset and its mappings for viewing.
    """
    asset = accounts.query.get_or_404(id)
    mappings = [{
        'id': m.id,
        'seq': m.seq,
        'src_column_name': m.src_column_name,
        'des_column_name': m.des_column_name,
        'is_drop': m.is_drop,
        'format': m.format,
        'custom': m.custom,
        'custom_formula': m.custom_formula
    } for m in asset.columns]

    asset_details = {
        'id': asset.id,
        'account_name': asset.account_name,
        'has_header': asset.has_header,
        'mappings': mappings
    }
    return jsonify(asset_details)

@bp.route('/asset/<int:asset_id>/mappings/create', methods=['POST'])
def create_mapping(asset_id):
    """
    API endpoint to create a new column mapping for a specific asset.
    """
    data = request.json
    new_mapping = account_columns_map(
        account_id=asset_id,
        seq=data.get('seq'),
        src_column_name=data.get('src_column_name'),
        des_column_name=data.get('des_column_name'),
        is_drop=data.get('is_drop', False),
        format=data.get('format'),
        custom=data.get('custom', False),
        custom_formula=data.get('custom_formula')
    )
    database.session.add(new_mapping)
    database.session.commit()
    return jsonify({'message': 'Mapping created successfully!'}), 201

@bp.route('/asset/<int:asset_id>/mappings/<int:mapping_id>/update', methods=['PUT'])
def update_mapping(asset_id, mapping_id):
    """
    API endpoint to update an existing column mapping.
    """
    mapping = account_columns_map.query.filter_by(id=mapping_id, account_id=asset_id).first_or_404()
    data = request.json
    
    mapping.seq = data.get('seq')
    mapping.src_column_name = data.get('src_column_name')
    mapping.des_column_name = data.get('des_column_name')
    mapping.is_drop = data.get('is_drop', mapping.is_drop)
    mapping.format = data.get('format')
    mapping.custom = data.get('custom', mapping.custom)
    mapping.custom_formula = data.get('custom_formula')
    
    database.session.commit()
    return jsonify({'message': 'Mapping updated successfully!'})

@bp.route('/asset/<int:asset_id>/mappings/<int:mapping_id>/delete', methods=['DELETE'])
def delete_mapping(asset_id, mapping_id):
    """
    API endpoint to delete a column mapping.
    """
    mapping = account_columns_map.query.filter_by(id=mapping_id, account_id=asset_id).first_or_404()
    database.session.delete(mapping)
    database.session.commit()
    return jsonify({'message': 'Mapping deleted successfully!'})


