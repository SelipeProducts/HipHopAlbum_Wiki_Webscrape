from flask import Blueprint, render_template, redirect, request
import requests
from bs4 import BeautifulSoup
import lxml

from .models import Album
from . import db

import itertools

from sqlalchemy import or_

views = Blueprint('views', __name__)

#Write to text file
def writefile(filename, txt):
    with open(filename, 'w') as writer:
      writer.write(str(txt))

#Function that gets rows inside of the table
def get_table_rows(the_table):
  albums =[]
  table_rows = the_table.find_all('tr')
  for tr in table_rows:
    td = tr.find_all('td')
    row = [i.text for i in td] #list comprehension
    albums.append(row)

  return albums

#Remove square brackets from wiki sources
def source_cleanup(txt):
  brack1 = txt.find('[')
  txt = txt[0:brack1-1]

  return txt

#Recursive function that changes dates with 0 value 
def fix_dates(album):
  
  if(album.day != 0 and album.month !=0):
    album_array = [album.month, album.day]
    return album_array
  elif album.day != 0:
    return album.day
  else:
    album_id = album.id
    prev_album = Album.query.filter_by(id=album_id-1).first()
    return fix_dates(prev_album)

#Remove text from title to get year
def title_cleanup(txt):
  title = txt.find(' in hip hop music')
  txt = txt[0:title]

  return txt

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
  #print(all_albums)
  #print(type(all_albums))

  if not all_albums:

    source = requests.get('https://en.wikipedia.org/wiki/2021_in_hip_hop_music').text

    soup = BeautifulSoup(source, 'lxml')

    

    # get text where div has id== bodyContent
    body_content = soup.find(id='bodyContent')

    mytables = soup.find_all('table', {'class':'wikitable'})
    # textfile_name = 'albums.txt'
    # writefile(textfile_name, mytables[0])

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
            year = soup.find(id="firstHeading").string
            year = title_cleanup(year)
            # print(year)

            new_album = Album(month=month_str, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
            db.session.add(new_album)
            db.session.commit()

          else:
            #is the correct size so should have correct collumns. so has day published
            # print(a_album)

            month_str = month.span.string
            day = a_album[0]
            artist = a_album[1]
            album_name = a_album[2]
            record_label = a_album[3]
            record_label = source_cleanup(record_label)
            year = soup.find(id="firstHeading").string
            year = title_cleanup(year)

            new_album = Album(month=month_str, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
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
@views.route('/wiki/<int:year>')
def wiki(year):
  url_str = 'https://en.wikipedia.org/wiki/'+str(year)+'_in_hip_hop_music#Released_albums'
  return redirect(url_str)

#About page
@views.route('/about')
def about():
  return render_template('about.html')

#List all page
@views.route('/list')
def list_all():
  all_albums = Album.query

  return render_template('list_all.html', album_list=all_albums)

#Gets year-specific list from db
@views.route('/list/<int:year>')
def list_year(year):
  album_year = Album.query.filter_by(year=year)
  
  return render_template('list.html', album_list=album_year, year=year)

#Updates album-list based off entererd-year for 2017+
@views.route('/update/<int:year>')
def update_year(year):
  album_year = Album.query.filter_by(year=year).all()
  #print(album_year)
  year = int(year)
    
  if not album_year:
    source_txt = 'https://en.wikipedia.org/wiki/'+str(year)+'_in_hip_hop_music'
    source = requests.get(source_txt).text

    soup = BeautifulSoup(source, 'lxml')
    mytables = soup.find_all('table', {'class':'wikitable'})
    # print('URL:',source_txt)

    #Table format not the same for list before 2016 &2012
    if year < 2017:
      #redirected to be parsed through page differently. Only one table with diff dates
      return redirect('/update/v2/'+ str(year))
    #this is the main parser that finds all tables that are organized by months
    elif year < 2022:
      #used for looping through table
      last_table_loc = 0
      if year == 2021:
        last_table_loc = 10 #2021 only up to sept (FOR NOW!!!) must limit total table parsed through
      else: 
        last_table_loc = 12
      # parsing through list of tables and adding ablums to db
      for a_table in itertools.islice(mytables , 0, last_table_loc):
        month = a_table.find_previous_sibling('h3')
        tables_albums = get_table_rows(a_table)
        #parsing through albums in the table
        for a_album in tables_albums:
          # print(len(a_album))
          #checking collumn numbers
          if len(a_album)>0:
            if len(a_album)<=2:
              for test_col in a_album:
                print('----------test--------------',test_col)
            elif len(a_album)==4 or len(a_album)==3:
              #does not have day published bc len==4
              #len==3 bc busdriver in 2018 only has 3 td
              day = 0  #*** just set automatically to 0
              month_str = month.span.string
              artist = a_album[0] #instead of a_album[1]
              album_name = a_album[1] #instead of a_album[2]
              record_label = a_album[2] #instead of a_album[3]
              record_label = source_cleanup(record_label)
              year = soup.find(id="firstHeading").string
              year = title_cleanup(year)
              # print('Test: ', album_name)

              new_album = Album(month=month_str, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
              db.session.add(new_album)
              db.session.commit()

            else:
              #is the correct size so should have correct collumns. so has day published
              # print(a_album)

              month_str = month.span.string
              day = a_album[0]
              artist = a_album[1]
              album_name = a_album[2]
              record_label = a_album[3]
              record_label = source_cleanup(record_label)
              year = soup.find(id="firstHeading").string
              year = title_cleanup(year)

              new_album = Album(month=month_str, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
              db.session.add(new_album)
              db.session.commit()

  print("Sucessfully Updated DB")
  
  #trying to fix dates
  album_year = Album.query.filter_by(year=year)
  for albums in album_year:
    albums.day = fix_dates(albums)
  db.session.commit()
  album_year = Album.query.filter_by(year=year)

  return render_template('list.html', album_list=album_year, year=year)

#Deletes year specific hip hop lists
@views.route('/delete/<int:year>')
def delete_year(year):
  albums_year = Album.query.filter_by(year=year).delete()
  # all_albums = Album.query.delete()
  db.session.commit()
  albums_year = Album.query.filter_by(year=year)
  return render_template('list.html', album_list=albums_year, year=year)

#U
@views.route('/update/v2/<int:year>')
def update_year2(year):
  album_year = Album.query.filter_by(year=year).all()
  #print(album_year)
  year = int(year)
    
  if not album_year:
    source_txt = 'https://en.wikipedia.org/wiki/'+str(year)+'_in_hip_hop_music'
    source = requests.get(source_txt).text

    soup = BeautifulSoup(source, 'lxml')

    main_table = soup.find('table', {'class':'wikitable'})

    tables_albums = get_table_rows(main_table)
        #parsing through albums in the table
    for a_album in tables_albums:
      #print('Album length:',len(a_album))
      if len(a_album)==0:
        pass
      elif len(a_album)<3:
        pass
      elif len(a_album)==4 or len(a_album)==3:
        date = 0
        month = date
        day = date
        artist = a_album[0] #instead of a_album[1]
        album_name = a_album[1] #instead of a_album[2]
        
        year = soup.find(id="firstHeading").string
        year = title_cleanup(year)
        # print('Test: ', album_name)

        new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=0, year=year)
        db.session.add(new_album)
        db.session.commit()
      else:
        #is the correct size so should have correct collumns. so has day published
        # print(a_album)
        date = a_album[0]
        date_split = date.split(" ")
        month = date_split[0]
        day = date_split[1]
        artist = a_album[1]
        album_name = a_album[2]
        year = soup.find(id="firstHeading").string
        year = title_cleanup(year)

        new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=0, year=year)
        db.session.add(new_album)
        db.session.commit()

  print("Sucessfully Updated DB")
  
  album_year = Album.query.filter_by(year=year)
  for albums in album_year:
    albums_array = fix_dates(albums)
    albums.month = albums_array[0]
    albums.day = albums_array[1]
  db.session.commit()
  album_year = Album.query.filter_by(year=year)

  return render_template('list.html', album_list=album_year, year=year)


@views.route('/search', methods=['POST', 'GET'])
def search():
  # album_year = Album.query.filter_by(year=year)
  if request.method == 'POST':
    searchwords = request.form['search']
    sw_split = searchwords.split(' ')


    # tag = request.form["tag"]
    # search = "%{}%".format(tag)
    # posts = Post.query.filter(Post.tags.like(search)).all()


    for search_word in sw_split:
      search_formated = "%{}%".format(search_word)

      search_by_year = Album.query.filter(Album.year.like(search_formated)).all()
      search_by_month =  Album.query.filter(Album.month.like(search_formated)).all()
      search_by_day = Album.query.filter_by(day=search_word)

      ####working!!!!!!!!!!!!!!!!!!!!!!!!!

      return render_template('search.html', results=search)

      # search_by_year = Album.query.filter_by(year=search_word)
      # search_by_month = Album.query.filter_by(month=search_word)  
      # search_by_day = Album.query.filter_by(day=search_word)  
      
      # search_by_artist = Album.query.filter_by(artist=search_word)
      # search_by_album_name = Album.query.filter_by(name=search_word)
      # search_by_record_label = Album.query.filter_by(record_label=search_word)
      
      # return render_template('search.html', results_year=search_by_year, results_month=search_by_month, results_day =search_by_day, results_artist=search_by_artist, results_album_name=search_by_album_name, results_record_label=search_by_record_label)


    print(searchwords)

  return render_template('search.html', results='none')
  # return render_template('list.html', album_list=album_year, year=year)
