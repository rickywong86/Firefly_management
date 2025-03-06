from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session, make_response, current_app
)

import pandas as pd

from werkzeug.exceptions import abort

from firefly_management.db import get_db

from . import home

import io

bp = Blueprint('transactions', __name__)

@bp.route('/transactions')
def index():
    db = get_db()
    _key = session['key']
    sql_stmt = f'SELECT id, created, transdate, desc, amount, category, sourceAcc, destinationAcc, score FROM __transactions where session_key = "{ _key }"; '
    df = pd.read_sql(sql_stmt,
        get_db()
        ) 
    
    for index, row in df.iterrows():
        update_link = url_for('transactions.update',id=row['id'])
        select_link = url_for('category.category_selection',desc=row['desc'],index=row['id'])
        df.loc[index, 'Action'] = (
            f'<a href="{update_link}">Edit</a> '
            f'<a href="{select_link}">Selection</a>'
        )

    df.rename(columns={'sourceAcc':'Source account',
                       'desc':'Description',
                       'transdate':'Date',
                       'created':'Created date time',
                       'amount':'Amount',
                       'destinationAcc':'Destination account',
                       'category':'Category',
                       'score':'Score'}, inplace=True)
    
    df = df[['Created date time','Source account','Description','Destination account','Date','Amount','Category','Score','Action']]
    

    _html = df.to_html(header='true', 
                       columns=['Created date time',
                                'Source account',
                                'Description',
                                'Destination account',
                                'Date',
                                'Amount',
                                'Category',
                                'Score',
                                'Action',
                       ],
                       table_id="table", classes=['table','table-striped'], border=1, render_links=True, escape=False, index=False)
    
    return render_template('transactions/index.html', tables=[_html], titles = [''])

@bp.route('/transactions/edit/<int:id>', methods=('GET', 'POST'))
def update(id):
    db = get_db()
    _key = session['key']

    if request.method == 'POST':
        desc = request.form['desc']
        destinationAcc = request.form['destinationAcc']
        category = request.form['category']
        df_result = home.scoring(desc,5)
        first_row = df_result.iloc[0]
        if destinationAcc != '' or category != '':
            score = '-'
        else:
            score = first_row['score']
        if destinationAcc == '':
            destinationAcc = first_row['destinationAcc']
        if category == '':
            category = first_row['category'] 
        sql_stmt = f'UPDATE __transactions SET desc = "{desc}", destinationAcc="{destinationAcc}", category="{category}", score="{score}" where session_key = "{ _key }" and id={id}; '
        db.execute(sql_stmt)
        db.commit()
        return redirect(url_for('transactions.index'))
    
    destinationAcc_list = pd.read_sql('SELECT DISTINCT destinationAcc FROM __category', get_db())
    category_list = pd.read_sql('SELECT DISTINCT category FROM __category', get_db())
    sql_stmt = f'SELECT id, created, transdate, desc, amount, category, sourceAcc, destinationAcc, score FROM __transactions where session_key = "{ _key }" and id={id}; '
    transaction = db.execute(sql_stmt).fetchone()
    return render_template('transactions/update.html', transaction=transaction, destinationAcc_list = destinationAcc_list.values, category_list = category_list.values)

@bp.route('/download')
def download():
    _key = session['key']
    stmt = f'SELECT transdate, desc, amount, category, sourceAcc, destinationAcc FROM __transactions where session_key = "{ _key }";' 
    df = pd.read_sql(stmt, get_db())

    df['transdate'] = pd.to_datetime(df.transdate, format='%d/%m/%Y')
    df['transdate'] = df['transdate'].dt.strftime('%Y%m%d')
    df = df[['sourceAcc','desc','destinationAcc','transdate','amount','category']]

    df.rename(columns={'sourceAcc':'Source account',
                       'desc':'Description',
                       'transdate':'Date',
                       'amount':'Amount',
                       'destinationAcc':'Destination account',
                       'category':'Category'}, inplace=True)

    response = make_response(df.to_csv(index=False))
    response.headers["Content-Disposition"] = "attachment; filename=export.csv"
    response.headers["Content-type"] = "text/csv"
    return response
