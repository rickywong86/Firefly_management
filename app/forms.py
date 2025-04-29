from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, IntegerField, BooleanField,
                     RadioField)
from wtforms.validators import InputRequired, Length, ValidationError
from wtforms_alchemy import ModelForm
from wtforms_alchemy import model_form_factory
from . import models

def length_check(form, field):
    if len(field.data) > 10:
        raise ValidationError('String too long.')
    
class AccountColumnsMapForm(FlaskForm):
    src_column_name = StringField('Source column:', validators=[InputRequired(),
                                            Length(min=1, max=100)])
    des_column_name = StringField('Destination column:', validators=[InputRequired(),
                                            Length(min=1, max=100)])
    is_drop = BooleanField('Drop', default='')
    format = StringField('Format:', validators=[Length(min=0, max=50)])
    custom = BooleanField('Custom', default='')
    custom_formula = StringField('Custom formula:', validators=[Length(min=0, max=50)])

class AccountsForm(FlaskForm):
    account_name = StringField('Account name:', validators=[InputRequired(),
                                                            Length(min=1, max=100)])
    has_header = BooleanField('Has header', default='')