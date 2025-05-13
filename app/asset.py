from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, sessions, session, jsonify
)

from werkzeug.exceptions import abort

from app.db import get_db

import pandas as pd
import json
import requests
from io import StringIO

from .models import accounts, account_columns_map
from .forms import AccountColumnsMapForm, AccountsForm
from . import database

bp = Blueprint('asset', __name__)

def asset_insert(_form):
    _account = accounts(account_name = _form.account_name.data, has_header = _form.has_header.data)
    database.session.add(_account)
    database.session.commit()
    return

def asset_edit(_form, _account):
    _form.populate_obj(_account)
    database.session.commit()
    return

def assetcolumnsmap_insert(form, _account):
    _model = account_columns_map(
        account = _account,
        seq = form.seq.data,
        src_column_name = form.src_column_name.data,
        des_column_name = form.des_column_name.data,
        is_drop = form.is_drop.data,
        format = form.format.data,
        custom = form.custom.data,
        custom_formula = form.custom_formula.data,
    )
    database.session.add(_model)
    database.session.commit()
    return

def assetcolumnsmap_edit(_form, _model):
    _form.populate_obj(_model)
    database.session.commit()
    return

@bp.route('/api/asset/assetsdata', methods=['GET','POST','PUT','DELETE'])
def assetsdata():
     match request.method: 
        case 'GET':
            _id = request.args.get('id', None)
            if _id is None:
                _accounts = accounts.query.all()
                return {"data": [x.to_dict(show=['account_name','has_header']) for x in _accounts]}, 200
            else:
                _accounts = accounts.query.filter_by(id=_id).first()
                return _accounts.to_dict(show=['account_name','has_header']), 200
        case 'POST':
            _account_name = request.form['account_name']
            _has_header = request.form['has_header']
            _form = AccountsForm(request.form)
            if _form.validate():
                asset_insert(_form)
            else:
                return jsonify(_form.errors), 400
            
            content = jsonify({'message':f'Insert record (account_name:"{_account_name}",has_header:{_has_header})'})
        
            return content, 201
        case 'PUT':
            _id = request.args.get('id','')
            if _id == '':
                return jsonify({'message':'Query parameter (ID) must be specified.'}), 400
            
            _account = accounts.query.get(_id)
            if _account is None:
                return jsonify({'message':f'Provided ID {_id} not exists.'}), 400
            
            _account_name = request.form['account_name']
            _has_header = request.form['has_header']
            _form = AccountsForm(request.form)
            if _form.validate():
                asset_edit(_form, _account)
            else:
                return jsonify(_form.errors), 400
            content = {'message':f'Update record (account_name:"{_account_name}",has_header:{_has_header}, id: {_id})'}
            return content, 201
        case 'DELETE':
            _id = request.args.get('id','')
            if _id == '':
                return {'message':'Form data (ID) must be specified.'}, 400
            else:
                pass
            
            _account = accounts.query.get(_id)
            database.session.delete(_account)
            database.session.commit()
            content = {'message':f'Delete record (account_name:{_account.account_name},has_header:{_account.has_header}, id: {_id})'}
            return content, 201

# @bp.route('/api/asset/assetcolumnsmap', defaults={'account_id':None}, methods=['DELETE'])
@bp.route('/api/asset/assetcolumnsmap/<string:account_id>', methods=['GET','POST','PUT', 'DELETE'])
def assetcolumnsmap(account_id):
    _account = accounts.query.get(account_id)
    if _account is None:
        return jsonify({'message':'Account ID is incorrect.'}), 400
    
    show = ['seq','src_column_name','des_column_name','is_drop','format','custom','custom_formula']
    match request.method: 
        case 'GET':
            _id = request.args.get('id', None)
            if _id is None:
                _accountColsMap = account_columns_map.query.filter_by(account_id=account_id).all()
                return {"data": [x.to_dict(show=show) for x in _accountColsMap]}, 200
            else:
                _accountColsMap = account_columns_map.query.filter_by(account_id=account_id, id=_id).first()
                return _accountColsMap.to_dict(show=show), 200
        case 'POST':
            _src_column_name = request.form['src_column_name']
            _des_column_name = request.form['des_column_name']
            _is_drop = request.form['is_drop']
            _format = request.form['format']
            _custom = request.form['custom']
            _custom_formula = request.form['custom_formula']

            _form = AccountColumnsMapForm(request.form)
            if _form.validate():
                assetcolumnsmap_insert(_form, _account)
            else:
                return jsonify(_form.errors), 400
            content = jsonify({'message':f'Insert record successfully.)'})
            return content, 201
        case 'PUT':
            _id = request.args.get('id','')
            if _id == '':
                return {'message':'Query parameter (ID) must be specified.'}, 400
            
            _model = account_columns_map.query.filter_by(account_id=account_id, id=_id).first()
            if _model is None:
                return {'message':f'Provided ID {_id} not exists.'}, 400
            
            _src_column_name = request.form['src_column_name']
            _des_column_name = request.form['des_column_name']
            _is_drop = request.form['is_drop']
            _format = request.form['format']
            _custom = request.form['custom']
            _custom_formula = request.form['custom_formula']

            _form = AccountColumnsMapForm(request.form)

            if _form.validate():
                assetcolumnsmap_edit(_form, _model)
            else:
                return jsonify(_form.errors), 400
            
            content = jsonify({'message':f'Update record successfully.'})
            return content, 201
        case 'DELETE':
            _id = request.args.get('id','')
            if _id == '':
                return {'message':'Form data (ID) must be specified.'}, 400
            else:
                pass
            
            _model = account_columns_map.query.filter_by(account_id=account_id, id=_id).first()
            database.session.delete(_model)
            database.session.commit()
            content = {'message':f'Delete record seccessfully.'}
            return content, 201

@bp.route('/assetcolumnsmap_dialog/<account_id>/<id>', methods=['GET'])
@bp.route('/assetcolumnsmap_dialog/<account_id>', methods=['GET','POST','PUT'], defaults={'id': None})
def assetcolumnsmap_dialog(account_id, id):
    if id is not None:
        model = account_columns_map.query.filter_by(account_id=account_id, id=id).first()
        formid = 'assetcolumnsmap_edit_dialog'
        form = AccountColumnsMapForm(obj=model)
    else:
        formid = 'assetcolumnsmap_create_dialog'
        form = AccountColumnsMapForm(account_id=account_id) 
    if request.method == 'POST':
        if form.validate():
            assetcolumnsmap_insert(form)
            return {'message':'Insert successful.'}, 201
        return jsonify(form.errors), 400
        
    return render_template('asset/assetcolumnsmap_dialog.html', formid=formid, form=form), 200

@bp.route('/asset_dialog/<id>', methods=['GET'])
@bp.route('/asset_dialog', methods=['GET','POST','PUT'], defaults={'id': None})
def asset_dialog(id):
    if id is not None:
        model = accounts.query.get(id)
        formid = 'asset_edit_dialog'
        form = AccountsForm(obj=model)
    else:
        formid = 'asset_create_dialog'
        form = AccountsForm() 
    if request.method == 'POST':
        if form.validate():
            asset_insert(form)
            return {'message':'Insert successful.'}, 201
        return jsonify(form.errors), 400
        
    return render_template('asset/asset_dialog.html', formid=formid, form=form), 200

# @bp.route('/asset', defaults={'message':None})
# @bp.route('/asset/<string:message>')
@bp.route('/asset')
def index():
    message = None
    if session.get('message') and session['message'] is not None:
        message = session['message']
        session['message'] = None
    return render_template('asset/index.html', message=message)

@bp.route('/asset/create', methods=('GET', 'POST'))
def create():
    form = AccountsForm()
    if form.validate_on_submit():
        url = url_for('asset.assetsdata', _external=True)
        payload = {
            'account_name': f"{form.account_name.data}",
            'has_header': f"{form.has_header.data}",
        }
        resp = requests.post(url, data=payload)
        resp_j = json.loads(resp.content)

        session['message'] = resp_j['message']

        return redirect(url_for('asset.index'))
    
    return render_template('asset/create.html', form=form)

@bp.route('/asset/<int:id>/update', methods=('GET', 'POST'))
def update(id):
    select_url = url_for('asset.assetsdata', _external=True)
    resp = requests.get(select_url, params={'id':id})
    resp_j = resp.json()
    account = resp_j['data'][0]

    if request.method == 'POST':
        if 'has_header' in request.form:
            _has_header = True
        else:
            _has_header = False
        _account_name = request.form['account_name']

        url = url_for('asset.assetsdata', _external=True)
        payload = {
            'account_name': f"'{_account_name}'",
            'has_header': f'{_has_header}'
        }
        resp = requests.put(url, params={'id':id}, data=payload)
        resp_j = json.loads(resp.content)

        session['message'] = resp_j['message']

        return redirect(url_for('asset.index'))
    
    return render_template('asset/update.html', account=account)

@bp.route('/asset/assetsdata/delete', methods=['POST'])
def assetsdata_delete():
    _id = ''
    if 'hidden_id' in request.form:
        _id = request.form['hidden_id']
        if _id == '':
            message='Form data (ID) must be specified.'
        else:
            pass
    else:
        message='Form data (ID) must be specified.'

    url = url_for('asset.assetsdata', _external=True)
    payload = {
        'id':_id
    }
    resp = requests.delete(url, params=payload)
    resp_j = json.loads(resp.content)
    message = resp_j['message']

    session['message'] = message

    return redirect(url_for('asset.index')) 

@bp.route('/asset/assetcolumnsmap/<string:account_id>/create', methods=('GET', 'POST'))
def assetcolumnsmap_create(account_id):     
    form = AccountColumnsMapForm()
    if form.validate_on_submit():
        url = url_for('asset.assetcolumnsmap', account_id=account_id, _external=True)
        payload = {
            'src_column_name': f"{form.src_column_name.data}",
            'des_column_name': f"{form.des_column_name.data}",
            'is_drop': f"{form.is_drop.data}",
            'format': f"{form.format.data}",
            'custom': f"{form.custom.data}",
            'custom_formula': f"{form.custom_formula.data}",
        }
        resp = requests.post(url, data=payload)
        resp_j = json.loads(resp.content)

        session['message'] = resp_j['message']

        return redirect(url_for('asset.index'))
    
    return render_template('asset/assetcolumnsmap_create.html', form=form)

@bp.route('/asset/assetcolumnsmap/<string:account_id>/<string:id>/update', methods=('GET', 'POST'))
def assetcolumnsmap_update(account_id,id):
    url = url_for('asset.assetcolumnsmap', account_id=account_id, id=id, _external=True)
    resp = requests.get(url, params={'id':id})
    resp_j = resp.json()
    form = AccountColumnsMapForm(data=resp_j['data'][0])

    if form.validate_on_submit():
        url = url_for('asset.assetcolumnsmap', account_id=account_id, id=id, _external=True)
        payload = {
            'src_column_name': f"{form.src_column_name.data}",
            'des_column_name': f"{form.des_column_name.data}",
            'is_drop': f"{form.is_drop.data}",
            'format': f"{form.format.data}",
            'custom': f"{form.custom.data}",
            'custom_formula': f"{form.custom_formula.data}",
        }
        resp = requests.put(url, data=payload)
        resp_j = json.loads(resp.content)

        session['message'] = resp_j['message']

        return redirect(url_for('asset.index'))
    return render_template('asset/assetcolumnsmap_update.html', form=form)