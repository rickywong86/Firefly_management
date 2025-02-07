import uuid
import os
import csv
import io
import re
import pandas as pd
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, session
)
from thefuzz import fuzz 
from thefuzz import process 

from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename

from firefly_management.db import get_db

bp = Blueprint('home', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def readfile(save_path, filename):
    # df = pd.read_sql('SELECT id, key, category, destinationAcc FROM __category', get_db())
    # keys = df['Key'].tolist()
    # print(keys)
    with open(save_path) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        col_count = 0
        for row in csv_reader:
            if line_count == 0:
                col_count = len(row)                
                line_count += 1
            else:
                if len(row) == col_count:
                    _date = row[1]
                    _amount = row[3]
                    _desc = row[5]
                    insertData([_date,_amount,_desc],filename)
                    line_count += 1

def getData(filename):
    result = get_db().execute(
        'SELECT id, created, transdate, desc, amount, category, sourceAcc, destinationAcc, filename, similarityScore'
        ' FROM __transaction WHERE filename = ?',
        (filename,)
    ).fetchall()

    return result

def insertData(data, filename):
    # update insert data with different file format
    # Barclays, Amex, HSBC UK
    db = get_db()
    db.execute(
        'INSERT into __transaction (transdate, desc, amount, category, sourceAcc, destinationAcc, filename, similarityScore)'
        ' VALUES (?,?,?,?,?,?,?,?)',
        (data.Date,re.sub('\s+',' ',data.Memo),data.Amount,'','','',filename,0,)
    )
    db.commit()
    return

def modify_transaction(df):
    return


def deleteData(filename):
    db = get_db()
    db.execute(
        'DELETE FROM __transaction WHERE filename = ?',
        (filename,)
    )
    db.commit()
    return

def scoring(_checkvalue, limit=5, ascending=False):
    df_cat = pd.read_sql('SELECT id, key, category, destinationAcc FROM __category', get_db())                
    df_cat['score'] = ''
    keys = df_cat['key'].tolist()
    scores = process.extract(_checkvalue,keys,scorer=fuzz.partial_ratio,limit=limit)
    for score in scores:
        row = df_cat.loc[df_cat['key'] == score[0]]
        df_cat.loc[df_cat['key'] == score[0],'score']  = score[1]
        # row['score'] = score[1]

    df_result = df_cat[df_cat['score'] != ""].sort_values(by='score', ascending=ascending)

    return df_result

@bp.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            # file.save(save_path)
            
            session['__session_id'] = uuid.uuid4()
            
            df = pd.read_csv(file)
            for index, row in df.iterrows():                
                insert_transaction(row)

            sql_stmt = f'SELECT id, created, transdate, desc, amount, category, sourceAcc, destinationAcc, filename, similarityScore FROM __transaction WHERE filename = "{filename}"'
            df_transaction = pd.read_sql(sql_stmt,
                                         get_db()
                                         )                   

            for index, row in df_transaction.iterrows():
                df_result = scoring(row['desc'])
                first_row = df_result.iloc[0]
                df_transaction.loc[index, 'destinationAcc'] = first_row['destinationAcc']
                df_transaction.loc[index, 'category'] = first_row['category']
                df_transaction.loc[index, 'similarityScore'] = first_row['score']
                df_transaction.loc[index, 'key'] = first_row['key']
                df_transaction.loc[index, 'action'] = f'<a target="_blank" href="category_selection/{row.desc}/{index}">Click</a>'

            print(df_transaction.to_sql("__transaction", get_db()))

            _html = df_transaction.to_html(header='true', table_id="table", classes=['table','table-striped'], border=0, render_links=True, escape=False)
            # build data from file
            # readfile(save_path, filename)

            return render_template('home/index.html', tables=[_html], titles = [''])
        else:
            flash('File extension is not allowed.')
            return redirect(request.url)
    
    return render_template('home/index.html')


@bp.route('/category_selection/<string:desc>/<int:index>', methods=['GET','POST'])
def category_selection(desc,index):
    if request.method == 'POST':
        print('To be define post action.')
        print(request.form.get('__category'))
    else:
        destinationAcc_list = pd.read_sql('SELECT DISTINCT destinationAcc FROM __category', get_db())
        category_list = pd.read_sql('SELECT DISTINCT category FROM __category', get_db())
        df_result = scoring(desc,300)
        df_result['Action'] = f'<input type="radio" name="category_rdo" />'
        # df_result['Action'] = f'<input type="submit" value="Select" />'
        _html = df_result.style.set_uuid('table_id').to_html(header='true', table_id="table", classes=['table','table-striped'], border=0, render_links=True, escape=False)
        return render_template('home/category_selection.html', tables=[_html], titles = [''], destinationAcc_list = destinationAcc_list.values, category_list = category_list.values)

    return render_template('home/category_selection.html')