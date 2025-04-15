from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, sessions
)

from werkzeug.exceptions import abort

from firefly_management.db import get_db

import pandas as pd
from . import home
import json
import requests
from io import StringIO

bp = Blueprint('asset', __name__)

@bp.route('/api/asset/assetsdata')
def assetsdata():
    df = pd.read_sql('SELECT * FROM _sourceAccount', get_db())
    _json = df.to_json(orient='records')
    _json_obj = json.loads(_json)
    return {'data': _json_obj}

@bp.route('/api/asset/assetcolumnsmap/<int:id>')
def assetcolumnsmap(id):
    print(f'get data {id}')
    df = pd.read_sql(f'SELECT * FROM _sourceAccountCsvMapping m where m._sourceAccount_id = {id}', get_db())
    _json = df.to_json(orient='records')
    _json_obj = json.loads(_json)
    return {'data': _json_obj}

@bp.route('/asset')
def index():
    _select_id = request.args.get('id')
    
    r = requests.get('http://127.0.0.1:5000/api/asset/assetcolumnsmap/1')
    j = r.json()

    df = pd.read_json(StringIO(json.dumps(j['data'])), orient='records')
    
    # if _select_id == None:
    #     _select_id = df.min()['id']

    # for index, row in df.iterrows():
    #     update_link = url_for('asset.update',id=row['id'])
    #     _id = row['id']
    #     _desc = row['desc']
    #     _modal_text = f'Delete categoty with Description <b>{_desc}</b>.'
    #     df.loc[index, 'Action'] = (
    #         f'<div class=\'btn-group col-sm-3 text-center\' role=\'group\'>'
    #         f'<a href=\'{update_link}\' class=\'btn btn-primary\'>Edit</a> '
    #         f'<button class=\'btn btn-danger\' onclick=\'delete_modal_show({_id},\'{_modal_text}\')\'>Delete</button>'
    #         f'</div>'
    #     )

    # df.rename(columns={
    #                    'desc':'Description',
    #                    }, inplace=True)

    # _html = df.to_html(header='true', 
    #                    columns=[
    #                             'Description',
    #                             'Action',
    #                    ],
    #                    table_id="table", classes=['table','table-sm','table-clickable'], border=False, render_links=True, escape=False, index=False)
    
    # df_map = pd.read_sql(f'SELECT * FROM _sourceAccountCsvMapping where _sourceAccount_id = {_select_id}', get_db())
    # _html_map= df_map.to_html(header='true', 
    #                 #    columns=[
    #                 #             'Description',
    #                 #             'Action',
    #                 #    ],
    #                    table_id="table_map", classes=['table','table-sm'], border=False, render_links=True, escape=False, index=False)

    
    # return render_template('asset/index.html', table=_html, table_map=_html_map, modal_text=_modal_text, headers=df.to_json(orient="records"))
    return render_template('asset/index.html')

@bp.route('/asset/create', methods=('GET', 'POST'))
def create():

    return render_template('asset/create.html')

@bp.route('/asset/<int:id>/update', methods=('GET', 'POST'))
def update(id):

    return render_template('asset/update.html')

@bp.route('/asset/assetcolumnsmap/<string:asset_id>/create', methods=('GET', 'POST'))
def assetcolumnsmap_create(asset_id):

    return render_template('asset/assetcolumnsmap_create.html')

@bp.route('/asset/assetcolumnsmap/<string:asset_id>/<string:assetcolumnmap_id>/update', methods=('GET', 'POST'))
def assetcolumnsmap_update(asset_id,assetcolumnmap_id):

    return render_template('asset/assetcolumnsmap_update.html')