from . import database
from sqlalchemy.sql import func
from sqlalchemy.orm import validates, relationship
from sqlalchemy import event, ForeignKey
from sqlalchemy.orm.attributes import QueryableAttribute
from sqlalchemy_serializer import SerializerMixin
import json
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class BaseModel(database.Model, SerializerMixin):
    __abstract__ = True

    def to_dict(self, show=None, _hide=None, _path=None):
        """Return a dictionary representation of this model."""

        show = show or []
        _hide = _hide or []

        hidden = self._hidden_fields if hasattr(self, "_hidden_fields") else []
        default = self._default_fields if hasattr(self, "_default_fields") else []
        default.extend(['id', 'modified_at', 'created_at'])

        if not _path:
            _path = self.__tablename__.lower()

            def prepend_path(item):
                # item = item.lower() - Case sensitive
                if item.split(".", 1)[0] == _path:
                    return item
                if len(item) == 0:
                    return item
                if item[0] != ".":
                    item = ".%s" % item
                item = "%s%s" % (_path, item)
                return item

            _hide[:] = [prepend_path(x) for x in _hide]
            show[:] = [prepend_path(x) for x in show]

        columns = self.__table__.columns.keys()
        relationships = self.__mapper__.relationships.keys()
        properties = dir(self)

        ret_data = {}

        for key in columns:
            if key.startswith("_"):
                continue
            check = "%s.%s" % (_path, key)
            if check in _hide or key in hidden:
                continue
            if check in show or key in default:
                ret_data[key] = getattr(self, key)

        for key in relationships:
            if key.startswith("_"):
                continue
            check = "%s.%s" % (_path, key)
            if check in _hide or key in hidden:
                continue
            if check in show or key in default:
                _hide.append(check)
                is_list = self.__mapper__.relationships[key].uselist
                if is_list:
                    items = getattr(self, key)
                    if self.__mapper__.relationships[key].query_class is not None:
                        if hasattr(items, "all"):
                            items = items.all()
                    ret_data[key] = []
                    for item in items:
                        ret_data[key].append(
                            item.to_dict(
                                show=list(show),
                                _hide=list(_hide),
                                _path=("%s.%s" % (_path, key.lower())),
                            )
                        )
                else:
                    if (
                        self.__mapper__.relationships[key].query_class is not None
                        or self.__mapper__.relationships[key].instrument_class
                        is not None
                    ):
                        item = getattr(self, key)
                        if item is not None:
                            ret_data[key] = item.to_dict(
                                show=list(show),
                                _hide=list(_hide),
                                _path=("%s.%s" % (_path, key.lower())),
                            )
                        else:
                            ret_data[key] = None
                    else:
                        ret_data[key] = getattr(self, key)

        for key in list(set(properties) - set(columns) - set(relationships)):
            if key.startswith("_"):
                continue
            if not hasattr(self.__class__, key):
                continue
            attr = getattr(self.__class__, key)
            if not (isinstance(attr, property) or isinstance(attr, QueryableAttribute)):
                continue
            check = "%s.%s" % (_path, key)
            if check in _hide or key in hidden:
                continue
            if check in show or key in default:
                val = getattr(self, key)
                if hasattr(val, "to_dict"):
                    ret_data[key] = val.to_dict(
                        show=list(show),
                        _hide=list(_hide),
                        _path=('%s.%s' % (_path, key.lower())),
                    )
                else:
                    try:
                        ret_data[key] = json.loads(json.dumps(val))
                    except:
                        pass

        return ret_data

class category(BaseModel):
    __tablename__ = '__category'

    id = database.Column(database.Integer, primary_key=True)
    key = database.Column(database.String(100), default='')
    category = database.Column(database.String(100), default='')
    destinationAcc = database.Column(database.String(100), default='')   

    def __repr__(self):
        return f'<Category id={self.id}, key={self.key}>'

class transactions(BaseModel):
    __tablename__ = '__transactions'
    
    id = database.Column(database.Integer, primary_key=True)
    created = database.Column(database.DateTime(timezone=True), server_default=func.now())
    transdate = database.Column(database.DateTime(timezone=True), server_default=func.now())
    desc = database.Column(database.String(250), default='') 
    amount = database.Column(database.Float(10,2), default=0.0)
    category = database.Column(database.String(100), default='')
    sourceAcc = database.Column(database.String(100), default='')
    destinationAcc = database.Column(database.String(100), default='')   
    score = database.Column(database.Float(3,2), default=0.0)
    session_key = database.Column(database.String(100), default='')

    @validates('category')
    def validate_category(self, key, value):
        result = category.query.filter_by(category=value)
        if not result:
            raise(f'Category {value} is not found.')

    # def __init__(self, created, transdate, desc, amount, category, sourceAcc, destinationAcc, score, session_key):
    #     self.key = key
    #     self.category = category
    #     self.destinationAcc = destinationAcc

class accounts(BaseModel):
    __tablename__ = 'accounts'

    id = database.Column(database.Integer, primary_key=True)
    account_name = database.Column(database.String(100), default='', info={'label':'Account name'}) 
    has_header = database.Column(database.Boolean, default=False, info={'label':'Has header'})
    columns = database.relationship('account_columns_map', backref='account')

    def __repr__(self):
        return f'<Asset id={self.id}, name={self.account_name}>'

class account_columns_map(BaseModel):
    __tablename__ = 'account_columns_map'
    id = database.Column(database.Integer, primary_key=True)
    account_id = database.Column(database.Integer, ForeignKey(accounts.id))
    seq = database.Column(database.Integer, default=0)
    src_column_name = database.Column(database.String(100), default='') 
    des_column_name = database.Column(database.String(100), default='') 
    is_drop = database.Column(database.Boolean, default=False)
    format = database.Column(database.String(100), default='') 
    custom = database.Column(database.Boolean, default=False)
    custom_formula = database.Column(database.String(100), default='') 

class Project(BaseModel):
    """
    A table for managing projects.
    """
    id = database.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    description = database.Column(database.String(500), nullable=False)
    created = database.Column(database.DateTime, nullable=False, default=datetime.utcnow)
    completed = database.Column(database.Boolean, default=False)
    transactions = database.relationship('Transaction', backref='project', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Project id={self.id}, description={self.description}>'

class Transaction(BaseModel):
    """
    A table for managing transactions related to a project.
    """
    id = database.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transdate = database.Column(database.DateTime, nullable=False)
    desc = database.Column(database.String(250), nullable=False)
    amount = database.Column(database.Numeric(10, 2), nullable=False)
    category = database.Column(database.String(150), nullable=True)
    sourceAcc = database.Column(database.String(150), database.ForeignKey('accounts.id'), nullable=True)
    destinationAcc = database.Column(database.String(150), nullable=True)
    score = database.Column(database.Numeric(10, 2), nullable=True)
    project_id = database.Column(UUID(as_uuid=True), database.ForeignKey('project.id'), nullable=False)

    source_asset = database.relationship('accounts', backref='transactions')

    def __repr__(self):
        return f'<Transaction id={self.id}, desc={self.desc}>'
    
class UserCorrection(BaseModel):
    """
    A table to store user-made corrections to transaction categories and destination accounts.
    This data is used to improve the scoring logic for future imports.
    """
    id = database.Column(database.Integer, primary_key=True)
    desc = database.Column(database.String(250), nullable=False)
    category = database.Column(database.String(150), nullable=False)
    destinationAcc = database.Column(database.String(150), nullable=False)

    def __repr__(self):
        return f'<UserCorrection id={self.id}, desc={self.desc}>'
    
if __name__ == "__main__":
    # Run this file directly to create the database tables.
    print("Creating database tables...")
    database.create_all()
    print("Done!")