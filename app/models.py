import uuid
import json
from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy.orm import validates, relationship
from sqlalchemy import event, ForeignKey
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.orm.attributes import QueryableAttribute

# Assuming database is imported from your Flask app instance (e.g., from your_app import db)
from . import database 

class BaseModel(database.Model, SerializerMixin):
    __abstract__ = True
    
    # Use String(36) for UUID compatibility with MySQL
    id = database.Column(database.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

class category(BaseModel):
    __tablename__ = '__category'

    key = database.Column(database.String(100), default='')
    category = database.Column(database.String(100), default='')
    destinationAcc = database.Column(database.String(100), default='')
    
    def __repr__(self):
        return f'<Category id={self.id}, key={self.key}>'

class transactions(BaseModel):
    __tablename__ = '__transactions'
    
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
        result = category.query.filter_by(category=value).first()
        if not result:
            raise ValueError(f'Category {value} is not found.')
        return value

    def __repr__(self):
        return f'<Transaction id={self.id}, desc={self.desc}>'

class accounts(BaseModel):
    __tablename__ = 'accounts'

    account_name = database.Column(database.String(100), default='', info={'label':'Account name'})
    has_header = database.Column(database.Boolean, default=False, info={'label':'Has header'})
    columns = database.relationship('account_columns_map', backref='account', order_by='asc(account_columns_map.seq)')
    transactions = database.relationship('Transaction', backref='source_account')

    def __repr__(self):
        return f'<Asset id={self.id}, name={self.account_name}>'

class account_columns_map(BaseModel):
    __tablename__ = 'account_columns_map'
    
    account_id = database.Column(database.String(36), ForeignKey(accounts.id))
    seq = database.Column(database.Integer, default=0)
    type = database.Column(database.String(100), nullable=False, default='')
    column_name = database.Column(database.String(100), nullable=False, default='')
    src_column_name = database.Column(database.String(100), default='')
    des_column_name = database.Column(database.String(100), default='')
    is_drop = database.Column(database.Boolean, default=False)
    format = database.Column(database.String(100), default='')
    custom = database.Column(database.Boolean, default=False)
    custom_formula = database.Column(database.String(100), default='')

    def __repr__(self):
        return f'<Asset id={self.id}, seq={self.seq}, type={self.type}, column_name={self.column_name}>'

class Project(BaseModel):
    """
    A table for managing projects.
    """
    __tablename__ = 'project'

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
    __tablename__ = 'transaction'

    transdate = database.Column(database.DateTime, nullable=False)
    desc = database.Column(database.String(250), nullable=False)
    amount = database.Column(database.Float(10, 2), nullable=False)
    category = database.Column(database.String(150), nullable=True)
    # Foreign key changed to String(36)
    sourceAcc = database.Column(database.String(36), database.ForeignKey('accounts.id'), nullable=True)
    destinationAcc = database.Column(database.String(150), nullable=True)
    score = database.Column(database.Float(10, 2), nullable=True)
    # Foreign key changed to String(36)
    project_id = database.Column(database.String(36), database.ForeignKey('project.id'), nullable=False)

    def __repr__(self):
        return f'<Transaction id={self.id}, desc={self.desc}>'

class UserCorrection(BaseModel):
    """
    A table to store user-made corrections to transaction categories and destination accounts.
    """
    __tablename__ = 'user_correction'
    
    desc = database.Column(database.String(250), nullable=False)
    category = database.Column(database.String(150), nullable=False)
    destinationAcc = database.Column(database.String(150), nullable=False)

    def __repr__(self):
        return f'<UserCorrection id={self.id}, desc={self.desc}>'
        
if __name__ == "__main__":
    print("Creating database tables...")
    # This requires an active Flask application context
    # with app.app_context():
    #     database.create_all()
    print("Done!")