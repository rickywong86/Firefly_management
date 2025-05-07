from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, sessions, jsonify
)

from werkzeug.exceptions import abort

from app.db import get_db

import pandas as pd
from . import home
from .models import category as c
import json
from .forms import CategoryForm
from . import database

bp = Blueprint('category', __name__)

def insert(key, category, destinationAcc):
    _insert = c(key=key,category=category,destinationAcc = destinationAcc)
    database.session.add(_insert)
    database.session.commit()

def edit(c, key, category, destinationAcc):
    c.key = key
    c.category = category
    c.destinationAcc = destinationAcc
    database.session.commit()

def delete(id):
    _to_delete = c.query.get(id)
    database.session.delete(_to_delete)
    database.session.commit()

def get_category_list():
    list = []
    for x in c.query.distinct(c.category):
        list.append(x.category)
    return list

def get_destinationAcc_list():
    list = []
    for x in c.query.distinct(c.destinationAcc):
        list.append(x.destinationAcc)
    return list

def get_category(id):
    result = get_db().execute(
        'SELECT id, key, category, destinationAcc FROM __category WHERE id = ?',
        (id,)
    ).fetchone()

    if result is None:
        abort(404, f"Category id {id} doesn't exist.")

    return result

@bp.route('/api/category', methods=['GET','POST','PUT','DELETE'])
def category():
    match request.method: 
        case 'GET':
            _id = request.args.get('id', None)
            if _id is None:
                result = c.query.all()
                return {"data": [x.to_dict(show=['key','category','destinationAcc']) for x in result]}, 200
            else:
                result = c.query.filter_by(id=_id).first()
                return result.to_dict(show=['key','category','destinationAcc']), 200
        case 'POST':
            _key = request.form['account_name']
            _category = request.form['has_header']
            _destinationAcc = request.form['destinationAcc']

            insert(_key,_category,_destinationAcc)

            return {'message', 'create success.'}, 201
        case 'PUT':
            _id = request.args.get('id','')
            if _id == '':
                return {'message':'Query parameter (ID) must be specified.'}, 400
            
            result = c.query.get(_id)
            if result is None:
                return {'message':f'Provided ID {_id} not exists.'}, 400
            else:
                _key = request.form['src_column_name']
                _category = request.form['des_column_name']
                _destinationAcc = request.form['is_drop']

                edit(_key,_category,_destinationAcc)
            
                content = {'message':f'Update record successfully.'}
                return content, 201 
        case 'DELETE':
            _id = request.args.get('id','')
            if _id == '':
                return {'message':'Form data (ID) must be specified.'}, 400
            else:
                pass
            
            result = c.query.get(_id)
            if result is None:
                return {'message':'No content'}, 400
            else:
                delete(_id)
                flash('Record deleted.','alert alert-success')
                content = {'message':f'Delete record successfully.'}
                return content, 201

        

@bp.route('/category')
def index():
    form = CategoryForm()
    
    return render_template('category/index.html', form=form)

@bp.route('/category/create', methods=('GET', 'POST'))
def create():
    form = CategoryForm()
    if form.validate_on_submit():
        insert(form.key.data, form.category.data, form.destinationAcc.data)
        flash('Create successful.','alert alert-success')
        return redirect(url_for('category.index'))

    return render_template('category/create.html', form=form, destinationAcc_list = get_destinationAcc_list(), category_list = get_category_list())

@bp.route('/category/<string:id>/update', methods=('GET', 'POST'))
def update(id):
    result = c.query.get(id)
    form = CategoryForm(obj=result)
    if form.validate_on_submit():
        key = request.form['key']
        cat = request.form['category']
        destinationAcc = request.form['destinationAcc']

        edit(result,key,cat,destinationAcc)
        flash('Update successful.','alert alert-success')
        return redirect(url_for('category.index'))

    return render_template('category/update.html', form=form, destinationAcc_list = get_destinationAcc_list(), category_list = get_category_list())

@bp.route('/category/selection/<string:desc>/<int:index>', methods=['GET','POST'])
def category_selection(desc,index):
    if request.method == 'POST':
        db = get_db()
    
        _category = request.form.get('__category')
        _destinationAcc = request.form.get('__destinationAcc')

        stmt = f'UPDATE __transactions SET category = "{_category}", destinationAcc = "{_destinationAcc}", score = "-" where id = "{index}"; '

        db.execute(stmt)

        db.commit()

        return redirect(url_for("transactions.index"))
    else:
        
        df_result = home.scoring(desc,5)
        df_result['Action'] = f'<input type="radio" name="category_rdo" /> <button onClick="select(this)"> Select </button>'

        df_result.rename(columns={'key':'Description',
                       'category':'Category',
                       'destinationAcc':'Destination account',
                       'score':'Score'}, inplace=True)
        
        _html = df_result.to_html(header='true', columns=[
            'Description',
            'Category',
            'Destination account',
            'Score'
            ],table_id="table", classes=['table','table-sm'], border=False, render_links=True, escape=False, index=False)
        return render_template('category/category_selection.html', tables=[_html], titles = [''],  desc=desc, index=index)
    
@bp.route('/category/createAndAssign/<string:desc>/<int:index>', methods=['GET','POST'])
def category_createAndAssign(desc,index):
    if request.method == 'POST':
        db = get_db()
    
        _category = request.form.get('category')
        _destinationAcc = request.form.get('destinationAcc')

        stmt = f'INSERT INTO __category (`key`, category, destinationAcc) VALUES ("{desc}","{_category}","{_destinationAcc}");'
        db.execute(stmt)
        db.commit()

        stmt = f'UPDATE __transactions SET category = "{_category}", destinationAcc = "{_destinationAcc}", score = "-" where id = "{index}"; '
        db.execute(stmt)
        db.commit()

        return redirect(url_for('transactions.index'))
    destinationAcc_list = pd.read_sql('SELECT DISTINCT destinationAcc FROM __category', get_db())
    category_list = pd.read_sql('SELECT DISTINCT category FROM __category', get_db())
    return render_template('category/createAndAssign.html', desc=desc, destinationAcc_list = destinationAcc_list.values, category_list = category_list.values,)