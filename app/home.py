import uuid
import os
import csv
import io
import re
import pandas as pd
import json
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, session
)
from thefuzz import fuzz 
from thefuzz import process 

from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename

from app.db import get_db

bp = Blueprint('home', __name__)

df_accounts = None
df_account_columns_map = None

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
    global df_accounts
    global df_account_columns_map
    df = df.fillna(0)
    df_column_def = df_accounts.merge(df_account_columns_map,left_on='id',right_on='account_id')
    df_column_def = df_column_def.drop(columns=['id_x','id_y','account_id'])

    df_column_def = df_column_def.loc[df_column_def['account_name'] == sourceAcc]
    drop_columns = df_column_def.loc[df_column_def['is_drop'] == True]['src_column_name'].to_numpy()
    has_header = df_accounts.loc[df_accounts['account_name'] == sourceAcc, 'has_header'].values[0]
    if has_header == False:
        header = df_column_def.loc[df_column_def['custom'] == False]['src_column_name'].to_numpy()
        print(header)
        df.to_csv('tmp.csv', header=header, index=False)
        df = pd.read_csv('tmp.csv')
    
    df_column_def['format'].str.strip()

    df_format = df_column_def.loc[df_column_def['format'] != ' ']
    print(df_format)
    for index, row in df_format.iterrows():
        df[row['src_column_name']] = pd.to_datetime(df[row['src_column_name']], format=row['format'])
        df[row['src_column_name']] = df[row['src_column_name']].dt.strftime('%d/%m/%Y')
    df_custom = df_column_def.loc[df_column_def['custom'] != 0]
    for index, row in df_custom.iterrows():
        df = pd.eval(f'{row["src_column_name"]} = {row["custom_formula"]}', target=df)
        # df = pd.eval(f'amount = df.Amount * -1', target=df)
    df = df.drop(columns=drop_columns)
    df_rename_dict = df_column_def.loc[(df_column_def['des_column_name'] != df_column_def['src_column_name']) & (df_column_def['is_drop'] == False)].drop(columns=['account_name','has_header','is_drop'])
    dict_rename = {}
    for index, row in df_rename_dict.iterrows():
        dict_rename[row['src_column_name']] = row['des_column_name']
    df = df.rename(columns=dict_rename)

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

@bp.route('/home', methods=['GET','POST'])
def index():
    session.clear()
    session['key'] = uuid.uuid4().hex[:6].upper()

    global df_accounts, df_account_columns_map

    df_accounts = pd.read_sql('SELECT * FROM accounts', get_db())
    df_account_columns_map = pd.read_sql('SELECT * FROM account_columns_map', get_db())

    df_accounts = df_accounts.astype({'has_header':'boolean'})
    df_account_columns_map = df_account_columns_map.astype({'is_drop':'boolean','custom':'boolean'})

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

            df = pd.read_csv(file, thousands=',')
            df = modify_transaction(df, sourceAcc)

            df['sourceAcc'] = sourceAcc

            df.to_sql(f'__transactions', get_db(), if_exists='append', index=False)

            return redirect(url_for("transactions.index"))
        else:
            flash('File extension is not allowed.')
            return redirect(request.url)
    
    json_account = df_accounts['account_name'].to_json()
    obj_account = json.loads(json_account)
    list_account = list(obj_account.values())

    return render_template('home/index.html', accounts=list_account)

