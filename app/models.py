from . import database
from sqlalchemy.sql import func
from sqlalchemy.orm import validates, relationship
from sqlalchemy import event, ForeignKey

class Dessert(database.Model):
    # See http://flask-sqlalchemy.pocoo.org/2.0/models/#simple-example
    # for details on the column types.

    # We always need an id
    id = database.Column(database.Integer, primary_key=True)

    # A dessert has a name, a price and some calories:
    name = database.Column(database.String(100))
    price = database.Column(database.Float)
    calories = database.Column(database.Integer)

    # def __init__(self, name, price, calories):
    #     self.name = name
    #     self.price = price
    #     self.calories = calories

    def calories_per_dollar(self):
        if self.calories:
            return self.calories / self.price
        
@event.listens_for(Dessert, "before_insert")
def lowercase(mapper, connection, target):
    target.name = target.name.lower()


class category(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    key = database.Column(database.String(100), default='')
    category = database.Column(database.String(100), default='')
    destinationAcc = database.Column(database.String(100), default='')   

    # def __init__(self, key, category, destinationAcc):
    #     self.key = key
    #     self.category = category
    #     self.destinationAcc = destinationAcc

class transactions(database.Model):
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

class accounts(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    account_name = database.Column(database.String(100), default='', info={'label':'Account name'}) 
    has_header = database.Column(database.Boolean, default=False, info={'label':'Has header'})


class account_columns_map(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    account_id = database.Column(database.Integer, ForeignKey(accounts.id))
    src_column_name = database.Column(database.String(100), default='') 
    des_column_name = database.Column(database.String(100), default='') 
    is_drop = database.Column(database.Boolean, default=False)
    format = database.Column(database.String(100), default='') 
    custom = database.Column(database.Boolean, default=False)
    custom_formula = database.Column(database.String(100), default='') 

    account = relationship('accounts', foreign_keys='account_columns_map.account_id')

if __name__ == "__main__":
    # Run this file directly to create the database tables.
    print("Creating database tables...")
    database.create_all()
    print("Done!")