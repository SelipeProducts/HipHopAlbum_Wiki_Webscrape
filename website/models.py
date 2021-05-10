from . import db

class Album(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  month = db.Column(db.String(150))
  day = db.Column(db.Integer)
  artist = db.Column(db.String(150))
  name =  db.Column(db.String(150))
  record_label = db.Column(db.String(150))
  year = db.Column(db.Integer)
  
  