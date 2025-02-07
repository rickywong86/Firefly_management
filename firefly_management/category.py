from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from werkzeug.exceptions import abort

from firefly_management.db import get_db

bp = Blueprint('category', __name__)

@bp.route('/category')
def index():
    db = get_db()
    categories = db.execute(
        'SELECT id, key, category, destinationAcc FROM __category'
    ).fetchall()
    return render_template('category/index.html', categories = categories)

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

    return render_template('category/create.html')

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

    return render_template('category/update.html', category=result)

@bp.route('/category/<int:id>/delete', methods=('POST',))
def delete(id):
    get_category(id)
    db = get_db()
    db.execute('DELETE FROM __category WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('category.index'))