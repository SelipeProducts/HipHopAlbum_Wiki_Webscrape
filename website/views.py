from flask import Blueprint, render_template, redirect
import requests
from bs4 import BeautifulSoup
import lxml

from .models import Album
from . import db

import itertools

views = Blueprint('views', __name__)

def writefile(filename, txt):
    with open(filename, 'w') as writer:
      writer.write(str(txt))

def source_cleanup(txt):
  brack1 = txt.find('[')
  txt = txt[0:brack1-1]

  return txt

def fix_dates(album):
  if album.day != 0:
    return album.day
  else:
    album_id = album.id
    prev_album = Album.query.filter_by(id=album_id-1).first()
    return fix_dates(prev_album)

#home page
@views.route('/')
def home():
  all_albums = Album.query

  return render_template('home.html', album_list=all_albums)
  #return render_template('home.html')

#Runs when update btn is pressed
@views.route('/fill_db')
def fill_db():
  all_albums = Album.query.all()
  print(all_albums)
  print(type(all_albums))

  if not all_albums:

    source = requests.get('https://en.wikipedia.org/wiki/2021_in_hip_hop_music').text

    soup = BeautifulSoup(source, 'lxml')

    textfile_name = 'albums.txt'

    # get text where div has id== bodyContent
    body_content = soup.find(id='bodyContent')

    mytables = soup.find_all('table', {'class':'wikitable'})

    # writefile(textfile_name, mytables[0])


    #-------------
    #Function that gets rows inside of the table
    def get_table_rows(the_table):
      albums =[]
      table_rows = the_table.find_all('tr')
      for tr in table_rows:
        td = tr.find_all('td')
        row = [i.text for i in td] #list comprehension
        albums.append(row)

      return albums

 
    #####################################################
    # parsing through list of tables and adding ablums to db
    for a_table in itertools.islice(mytables , 0, 8):
      month = a_table.find_previous_sibling('h3')
      tables_albums = get_table_rows(a_table)
      #parsing through albums in the table
      for a_album in tables_albums:
        #checking collumn numbers
        if len(a_album)>0:
          if len(a_album)<5:
            #does not have day published bc len==4
            day = 0  #*** just set automatically to 0
            month_str = month.span.string
            artist = a_album[0] #instead of a_album[1]
            album_name = a_album[1] #instead of a_album[2]
            record_label = a_album[2] #instead of a_album[3]
            record_label = source_cleanup(record_label)

            new_album = Album(month=month_str, day=day, artist=artist, name=album_name, record_label=record_label)
            db.session.add(new_album)
            db.session.commit()

          else:
            #is the correct size so should have correct collumns. so has day published
            print(a_album)

            month_str = month.span.string
            day = a_album[0]
            artist = a_album[1]
            album_name = a_album[2]
            record_label = a_album[3]
            record_label = source_cleanup(record_label)

            new_album = Album(month=month_str, day=day, artist=artist, name=album_name, record_label=record_label)
            db.session.add(new_album)
            db.session.commit()

  print("Sucessfully Updated DB")
  
  #trying to fix dates
  all_albums = Album.query
  for albums in all_albums:
    albums.day = fix_dates(albums)
  db.session.commit()
  all_albums = Album.query

  return render_template('home.html', album_list=all_albums)

#Runs when delete btn is pressed
@views.route('/delete')
def delete():
  all_albums = Album.query.delete()
  db.session.commit()
  all_albums = Album.query
  return render_template('home.html', album_list=all_albums)

#Wiki link redirects to wikipedia page
@views.route('/wiki')
def wiki():
  return redirect('https://en.wikipedia.org/wiki/2021_in_hip_hop_music#Released_albums')

#About page
@views.route('/about')
def about():
  return render_template('about.html')

