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
  brack2 = txt.find(']')
  txt = txt[0:brack1-1]
  
  return txt


@views.route('/')
def home():

  all_albums = Album.query
          

  #     # website_albums.append(a_album)

  # #is this the best way to pull and organize this information??????
  # #do i get date (month) first and then read table after?
  # #or do i loop through tables (like i alreadyy did) and check prevous sibling element

  # #-----------------------------------------------------
  # #-----------------------------------------------------
  # table0 = mytables[0]

  # albums_test = []
  # table_rows = table0.find_all('tr')
  # for tr in table_rows:
  #   td = tr.find_all('td')
  #   row = [i.text for i in td] #list comprehension
  #   # print(row)
  #   albums_test.append(row)

  # print('tEST: ', albums_test[1])

  # album1 = albums[1]

  # day = album1[0]
  # artist = album1[1]
  # album_name = album1[2]
  # record_label = album1[3]

  # day = day.replace('\n','')
  # artist = artist.replace('\n','')
  # album_name = album_name.replace('\n','')
  # record_label = record_label.replace('\n','')

  # print(artist, 'released', album_name, 'with', record_label)

  #-----------------------------------------------------
  return render_template('home.html', album_list=all_albums)
  #return render_template('home.html')



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
        print(len(td))
      
        row = [i.text for i in td] #list comprehension
        

        
        # print(row[1])
        albums.append(row)
      # print(len(albums))
      # print(albums[1])
      return albums

    # parsing through list of tables and adding ablums to list

    # print(mytables[7])

    #####################################################
    website_albums = []
    for a_table in itertools.islice(mytables , 0, 8):
    # for a_table in mytables:
      month = a_table.find_previous_sibling('h3')
      # print(month.span.string)
      print()
      tables_albums = get_table_rows(a_table)
      
        
      for a_album in tables_albums:
      

        if len(a_album)>0:
          if len(a_album)<5:
            #does not have day published len==4
            day = 0
            month_str = month.span.string
            artist = a_album[0]
            album_name = a_album[1]
            record_label = a_album[2]
            record_label = source_cleanup(record_label)

            new_album = Album(month=month_str, day=day, artist=artist, name=album_name, record_label=record_label)
            db.session.add(new_album)
            db.session.commit()

          else:
            #is the correct size so should have correct collumns. so has day published

            # print(type(a_album))
            # print('Album length <list>:', len(a_album))
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
  all_albums = Album.query
  return render_template('home.html', album_list=all_albums)


@views.route('/delete')
def delete():
  all_albums = Album.query.delete()
  db.session.commit()
  all_albums = Album.query
  return render_template('home.html', album_list=all_albums)


@views.route('/wiki')
def wiki():
  return redirect('https://en.wikipedia.org/wiki/2021_in_hip_hop_music#Released_albums')

@views.route('/about')
def about():
  
  return render_template('about.html')