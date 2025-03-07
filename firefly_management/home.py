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
        (data.Date,re.sub('\s+',' ',data.Memo),data.Amount,'','','',session['key'],0,)
    )
    db.commit()
    return

def modify_transaction(df, sourceAcc):
    print(sourceAcc)
    if sourceAcc == 'HSBC UK':
        df.to_csv('tmp.csv', header=['transdate','desc','amount'], index=False)
        df = pd.read_csv('tmp.csv')

    if sourceAcc == 'Barclays' or sourceAcc =='Barclays ISA':
        df = df.drop(columns=['Number','Account','Subcategory'])
        df = df.rename(columns={'Date':'transdate','Amount':'amount','Memo':'desc'})

    if sourceAcc == 'Amex (BA)':
        # df['Description'] = df['Description'] + ' (' + df['Card Member'] + ')'
        df['Amount'] = df['Amount'] * -1
        df = df.drop(columns=['Account #', 'Card Member'])
        df = df.rename(columns={'Date':'transdate','Amount':'amount','Description':'desc'})

    for index, row in df.iterrows():
        df_result = scoring(row['desc'])
        first_row = df_result.iloc[0]
        df.loc[index, 'desc'] = re.sub('\s+',' ',row['desc'])
        df.loc[index, 'destinationAcc'] = first_row['destinationAcc']
        df.loc[index, 'category'] = first_row['category']
        df.loc[index, 'score'] = first_row['score']
        df.loc[index, 'session_key'] = session['key']

    return df


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
    # v = re.sub('[^A-Za-z0-9]+', ' ', _checkvalue)
    _checkvalue = re.sub(r'\s+', ' ', _checkvalue)
    scores = process.extract(_checkvalue,keys,scorer=fuzz.partial_ratio,limit=limit)
    for score in scores:
        row = df_cat.loc[df_cat['key'] == score[0]]
        df_cat.loc[df_cat['key'] == score[0],'score']  = score[1]
        # row['score'] = score[1]

    df_result = df_cat[df_cat['score'] != ""].sort_values(by='score', ascending=ascending)

    return df_result

@bp.route('/', methods=['GET','POST'])
def index():
    session.clear()
    session['key'] = uuid.uuid4().hex[:6].upper()

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
           
            sourceAcc = request.form.get('sourceAcc')

            df = pd.read_csv(file)
            df = modify_transaction(df, sourceAcc)

            df['sourceAcc'] = sourceAcc

            df.to_sql(f'__transactions', get_db(), if_exists='append', index=False)

            return redirect(url_for("transactions.index"))
        else:
            flash('File extension is not allowed.')
            return redirect(request.url)
    
    return render_template('home/index.html')

