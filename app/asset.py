from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, sessions, session
)

from werkzeug.exceptions import abort

from app.db import get_db

import pandas as pd
import json
import requests
from io import StringIO

from .forms import AccountColumnsMapForm, AccountsForm

bp = Blueprint('asset', __name__)

@bp.route('/api/asset/assetsdata', methods=['GET','POST','PUT','DELETE'])
def assetsdata():
     match request.method: 
        case 'GET':
            _id = request.args.get('id', None)
            sql_stmt = ''
            if _id is None:
                sql_stmt = 'SELECT * FROM accounts'
            else:
                sql_stmt = f'SELECT * FROM accounts a where a.id = {_id}'
            df = pd.read_sql(sql_stmt, get_db())
            _json = df.to_json(orient='records')
            _json_obj = json.loads(_json)
            return {'data': _json_obj}, 200
        case 'POST':
            _account_name = request.form['account_name']
            _has_header = request.form['has_header']
            sql_stmt = f'INSERT INTO accounts (account_name, has_header) VALUES ("{_account_name}",{_has_header});'

            db = get_db()

            db.execute(sql_stmt)
            db.commit()
            content = {'message':f'Insert record (account_name:"{_account_name}",has_header:{_has_header})'}
            return content, 201
        case 'PUT':
            _id = request.args.get('id','')
            if _id == '':
                return {'message':'Query parameter (ID) must be specified.'}, 400
            
            select_stmt = f'SELECT * FROM accounts where id = {_id}'
            df = pd.read_sql(select_stmt, get_db())
            if df.empty:
                return {'message':f'Provided ID {_id} not exists.'}, 400
            
            _account_name = request.form['account_name']
            _has_header = request.form['has_header']
            sql_stmt = f'UPDATE accounts SET account_name = "{_account_name}", has_header={_has_header} where id = {_id};'
            db = get_db()
            db.execute(sql_stmt)
            db.commit()
            content = {'message':f'Update record (account_name:"{_account_name}",has_header:{_has_header}, id: {_id})'}
            return content, 201
        case 'DELETE':
            _id = request.args.get('id','')
            if _id == '':
                return {'message':'Form data (ID) must be specified.'}, 400
            else:
                pass
            
            select_stmt = f'SELECT * FROM accounts where id = {_id}'
            df = pd.read_sql(select_stmt, get_db())
            if df.empty:
                return {'message':'No content'}, 400
            sql_stmt = f'DELETE FROM accounts where id = {_id};'
            db = get_db()
            db.execute(sql_stmt)
            db.commit()
            content = {'message':f'Delete record (account_name:{df.account_name},has_header:{df.has_header}, id: {_id})'}
            return content, 201

# @bp.route('/api/asset/assetcolumnsmap', defaults={'account_id':None}, methods=['DELETE'])
@bp.route('/api/asset/assetcolumnsmap/<string:account_id>', methods=['GET','POST','PUT', 'DELETE'])
def assetcolumnsmap(account_id):
    match request.method: 
        case 'GET':
            _id = request.args.get('id', None)
            sql_stmt = ''
            if _id is None:
                sql_stmt = f'SELECT * FROM account_columns_map m where m.account_id = {account_id}'
            else:
                sql_stmt = f'SELECT * FROM account_columns_map m where m.account_id = {account_id} and m.id = {_id}'

            df = pd.read_sql(sql_stmt, get_db())
            _json = df.to_json(orient='records')
            _json_obj = json.loads(_json)
            return {'data': _json_obj}, 200
        case 'POST':
            _src_column_name = request.form['src_column_name']
            _des_column_name = request.form['des_column_name']
            _is_drop = request.form['is_drop']
            _format = request.form['format']
            _custom = request.form['custom']
            _custom_formula = request.form['custom_formula']

            sql_stmt = f'INSERT INTO account_columns_map (account_id, src_column_name, des_column_name, is_drop, format, custom, custom_formula) ' + \
            f'VALUES ({account_id},"{_src_column_name}","{_des_column_name}",{_is_drop},"{_format}",{_custom},"{_custom_formula}");'
            print(sql_stmt)
            db = get_db()

            db.execute(sql_stmt)
            db.commit()
            content = {'message':f'Insert record successfully.)'}
            return content, 201
        case 'PUT':
            _id = request.args.get('id','')
            if _id == '':
                return {'message':'Query parameter (ID) must be specified.'}, 400
            
            select_stmt = f'SELECT * FROM account_columns_map m where m.account_id = {account_id} and m.id = {_id}'
            df = pd.read_sql(select_stmt, get_db())
            if df.empty:
                return {'message':f'Provided ID {_id} not exists.'}, 400
            
            _src_column_name = request.form['src_column_name']
            _des_column_name = request.form['des_column_name']
            _is_drop = request.form['is_drop']
            _format = request.form['format']
            _custom = request.form['custom']
            _custom_formula = request.form['custom_formula']

            sql_stmt = f'UPDATE account_columns_map ' + \
            f'SET account_id = {account_id}, ' + \
            f'src_column_name="{_src_column_name}", ' + \
            f'des_column_name="{_des_column_name}", ' + \
            f'is_drop={_is_drop}, ' + \
            f'format="{_format}", ' + \
            f'custom={_custom}, ' + \
            f'custom_formula="{_custom_formula}" ' + \
            f'where id = {_id};'

            db = get_db()
            db.execute(sql_stmt)
            db.commit()
            content = {'message':f'Update record successfully.'}
            return content, 201
        case 'DELETE':
            _id = request.args.get('id','')
            if _id == '':
                return {'message':'Form data (ID) must be specified.'}, 400
            else:
                pass
            
            select_stmt = f'SELECT * FROM account_columns_map m where m.account_id = {account_id} and m.id = {_id}'
            df = pd.read_sql(select_stmt, get_db())
            if df.empty:
                return {'message':'No content'}, 400
            sql_stmt = f'DELETE FROM account_columns_map where id = {_id};'
            db = get_db()
            db.execute(sql_stmt)
            db.commit()
            content = {'message':f'Delete record seccessfully.'}
            return content, 201

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