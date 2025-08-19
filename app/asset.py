# project/routes.py
# This file defines all the web routes for the application.

from flask import render_template, request, redirect, url_for, jsonify, Blueprint, Response
from . import database
from .models import accounts, account_columns_map
import io, csv
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
        'custom_formula': m.custom_formula,
        'column_name':m.column_name,
        'type':m.type
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
        custom_formula=data.get('custom_formula'),
        column_name=data.get('column_name'),
        type=data.get('type')
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
    mapping.column_name = data.get('column_name')
    mapping.type = data.get('type')
    
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

@bp.route('/assets/upload', methods=['POST'])
def upload_assets():
    """Handles CSV upload for accounts and their column maps."""
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.DictReader(stream)
        
        imported_accounts = 0
        current_account = None

        for row in reader:
            # Check for a new account entry (assuming account_name is present on a new account row)
            if row.get('account_name'):
                account_name = row['account_name']
                has_header = row.get('has_header', 'False').lower() == 'true'
                
                # Check for existing account
                current_account = accounts.query.filter_by(account_name=account_name).first()
                if not current_account:
                    current_account = accounts(account_name=account_name, has_header=has_header)
                    database.session.add(current_account)
                    database.session.flush() # To get the account_id
                    imported_accounts += 1
            
            # If we have an account, process the column map
            if current_account:
                new_column_map = account_columns_map(
                    account_id=current_account.id,
                    seq=int(row.get('seq', 0)),
                    type=row.get('type', ''),
                    column_name=row.get('column_name', ''),
                    src_column_name=row.get('src_column_name', ''),
                    des_column_name=row.get('des_column_name', ''),
                    is_drop=row.get('is_drop', 'False').lower() == 'true',
                    format=row.get('format', ''),
                    custom=row.get('custom', 'False').lower() == 'true',
                    custom_formula=row.get('custom_formula', '')
                )
                database.session.add(new_column_map)

        database.session.commit()
        return jsonify({'message': f'{imported_accounts} new accounts and their column maps imported successfully!'})
    except Exception as e:
        database.session.rollback()
        return jsonify({'message': f'Error processing file: {str(e)}'}), 500

@bp.route('/asset/export_csv', methods=['GET'])
def export_assets():
    """Exports all accounts and their column maps to a single CSV file."""
    accounts_list = accounts.query.all()
    si = io.StringIO()
    cw = csv.writer(si)

    # Headers for the combined CSV file
    headers = [
        'account_name', 'has_header', 'seq', 'type', 'column_name', 
        'src_column_name', 'des_column_name', 'is_drop', 'format', 
        'custom', 'custom_formula'
    ]
    cw.writerow(headers)

    for account in accounts_list:
        for column in account.columns:
            row = [
                account.account_name,
                'True' if account.has_header else 'False',
                column.seq,
                column.type,
                column.column_name,
                column.src_column_name,
                column.des_column_name,
                'True' if column.is_drop else 'False',
                column.format,
                'True' if column.custom else 'False',
                column.custom_formula
            ]
            cw.writerow(row)
    
    output = si.getvalue()
    si.close()

    response = Response(output, mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=accounts_export.csv'
    return response
