from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, sessions
)

from werkzeug.exceptions import abort

from app.db import get_db

import pandas as pd
from . import home

bp = Blueprint('category', __name__)

@bp.route('/category')
def index():
    # db = get_db()
    # categories = db.execute(
    #     'SELECT id, key, category, destinationAcc FROM __category'
    # ).fetchall()
    df = pd.read_sql('SELECT id, key, category, destinationAcc FROM __category', get_db())

    for index, row in df.iterrows():
        update_link = url_for('category.update',id=row['id'])
        _id = row['id']
        _desc = row['key']
        df.loc[index, 'Action'] = (
            f'<div class="btn-group col-sm-12 text-center" role="group">'
            f'<a href="{update_link}" class="btn btn-primary">Edit</a> '
            f"<button class='btn btn-danger' onclick='delete_modal_show({_id},\"{_desc}\")'>Delete</button>"
            f'</div>'
        )
    
    df.rename(columns={
                       'key':'Description',
                       'destinationAcc':'Destination account',
                       'category':'Category'}, inplace=True)
    
    _html = df.to_html(header='true', 
                       columns=[
                                'Description',
                                'Destination account',
                                'Category',
                                'Action',
                       ],
                       table_id="table", classes=['table','table-sm'], border=False, render_links=True, escape=False, index=False)
    return render_template('category/index.html', table=_html)

@bp.route('/category/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        key = request.form['key']
        cat = request.form['category']
        destinationAcc = request.form['destinationAcc']
        error = None

        if not key:
            error = 'Key is required.'

        if not cat:
            error = 'Category is required.'

        if not destinationAcc:
            error = 'DestinationAcc is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO __category (key, category, destinationAcc)'
                ' VALUES (?, ?, ?)',
                (key, cat, destinationAcc)
            )
            db.commit()
            return redirect(url_for('category.index'))
        
    destinationAcc_list = pd.read_sql('SELECT DISTINCT destinationAcc FROM __category', get_db())
    category_list = pd.read_sql('SELECT DISTINCT category FROM __category', get_db())

    return render_template('category/create.html', destinationAcc_list = destinationAcc_list.values, category_list = category_list.values)

def get_category(id):
    result = get_db().execute(
        'SELECT id, key, category, destinationAcc FROM __category WHERE id = ?',
        (id,)
    ).fetchone()

    if result is None:
        abort(404, f"Category id {id} doesn't exist.")

    return result

@bp.route('/category/<int:id>/update', methods=('GET', 'POST'))
def update(id):
    result = get_category(id)

    if request.method == 'POST':
        key = request.form['key']
        cat = request.form['category']
        destinationAcc = request.form['destinationAcc']
        error = None

        if not key:
            error = 'Key is required.'

        if not cat:
            error = 'Category is required.'

        if not destinationAcc:
            error = 'DestinationAcc is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE __category SET key = ?, category = ?, destinationAcc = ?'
                ' WHERE id = ?',
                (key, cat, destinationAcc, id)
            )
            db.commit()
            return redirect(url_for('category.index'))

    destinationAcc_list = pd.read_sql('SELECT DISTINCT destinationAcc FROM __category', get_db())
    category_list = pd.read_sql('SELECT DISTINCT category FROM __category', get_db())

    return render_template('category/update.html', category=result, destinationAcc_list = destinationAcc_list.values, category_list = category_list.values)

@bp.route('/category/delete', methods=('POST',))
def delete():
    print('run')
    id = request.form['hidden_id']
    get_category(id)
    db = get_db()
    db.execute('DELETE FROM __category WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('category.index'))


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