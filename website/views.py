from flask import Blueprint, render_template, redirect, request
import requests
from bs4 import BeautifulSoup
import lxml

from .models import Album
from . import db

import itertools

from sqlalchemy import or_

import csv

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

#Remove square brackets from day in 2005
#Doesnt -1 when cutting array
def source_cleanup2(txt):
  brack1 = txt.find('[')
  txt = txt[0:brack1]

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
    if year>=1980 and year<=1996:
      return redirect('/update/v6/'+ str(year))
    elif year == 1997:
      return redirect('/update/v5/'+ str(year))
    elif year<=2001 and year>=1998:
      return redirect('/update/v7/'+ str(year))  
    elif year<=2006 and year>=2002:
      return redirect('/update/v6/'+ str(year)) 
    elif year==2007:
      return redirect('/update/v2/'+ str(year))
    elif year <= 2010:
      return redirect('/update/v5/'+ str(year))   
    elif year < 2012: #for 2011
      #redirected to be parsed through page differently. Only one table with diff dates
      return redirect('/update/v4/'+ str(year))
    if year == 2012:
      #table has diff. formating needed its own
      return redirect('/update/v3/'+ str(year))
    elif year < 2017:
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
    elif year>2022:
      pass
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

#For years 2016-2013
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
      # print('Album length:',len(a_album))
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
        record_label = a_album[2]
        record_label = source_cleanup(record_label)
        year = soup.find(id="firstHeading").string
        year = title_cleanup(year)
        # print('Test: ', album_name)

        new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
        db.session.add(new_album)
        db.session.commit()
      else:
        #is the correct size so should have correct collumns. so has day published
        # print(a_album)
        date = a_album[0]
        date_split = date.split(" ")

        # print('Splitted Date: ',date_split)
        month = date_split[0]
        day = date_split[1]
        artist = a_album[1]
        album_name = a_album[2]
        record_label = a_album[3]
        record_label = source_cleanup(record_label)
        year = soup.find(id="firstHeading").string
        year = title_cleanup(year)

        new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
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

#For year 2012 specifically
@views.route('/update/v3/<int:year>')
def update_year3(year):
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
      print('Album length:',len(a_album))
      if len(a_album)==0:
        pass
      elif len(a_album)==3:
        pass
      elif len(a_album)==5:
        treated_as_full_collumn = False
        month_list = ['January', 'February', 'March','April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

        month_test = a_album[0]
        month_test = month_test.lower()
        month_test = month_test.split(' ')

        for month in month_list:
          month = month.lower()
          for test_element in month_test:
            if month == test_element:
              print('month:', month)
              print('tester:', month_test)
              print('month match at', month)
              #treating like full collumn
              album_name = a_album[2]
              print('album name fo len5 full:', album_name)


              date = a_album[0]
              date_split = date.split(" ")
              month = date_split[0]
              day = date_split[1]
              artist = a_album[1]
              

              record_label = a_album[3]
              record_label = source_cleanup(record_label)
              year = soup.find(id="firstHeading").string
              year = title_cleanup(year)

              new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
              db.session.add(new_album)
              db.session.commit()
              print("Sucessfully Updated DB")

              treated_as_full_collumn = True
              break
        #treating as missing date collumn
        if treated_as_full_collumn == False:
          album_name = a_album[1] #instead of a_album[2]
          print('album name fo len5', album_name)

          date = 0
          month = date
          day = date
          artist = a_album[0] #instead of a_album[1]
          

          record_label = a_album[2]
          record_label = source_cleanup(record_label)
          year = soup.find(id="firstHeading").string
          year = title_cleanup(year)
          # print('Test: ', album_name)

          new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
          db.session.add(new_album)
          db.session.commit()

          print("Sucessfully Updated DB")

      elif len(a_album)==4:
        date = 0
        month = date
        day = date
        artist = a_album[0] #instead of a_album[1]
        album_name = a_album[1] #instead of a_album[2]
        record_label = a_album[2]
        record_label = source_cleanup(record_label)
        year = soup.find(id="firstHeading").string
        year = title_cleanup(year)
        # print('Test: ', album_name)

        new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
        db.session.add(new_album)
        db.session.commit()
      else:
        #is the correct size so should have correct collumns. so has day published
        # print(a_album)
        date = a_album[0]
        date_split = date.split(" ")

        print('Splitted Date: ',date_split)
        month = date_split[0]
        day = date_split[1]
        artist = a_album[1]
        album_name = a_album[2]
        record_label = a_album[3]
        record_label = source_cleanup(record_label)
        year = soup.find(id="firstHeading").string
        year = title_cleanup(year)

        new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
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



#for years 2011
@views.route('/update/v4/<int:year>')
def update_year4(year):
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

#for yearS 2010 and 2008
@views.route('/update/v5/<int:year>')
def update_year5(year):
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
      elif len(a_album)==3:
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
        print(date_split)
        #if bc error thrown at (1997) June Esham	Bruce Wayne: Gothom City 1987
        #missing day value
        if len(date_split) == 2:
          month = date_split[0]
          day = date_split[1]
        elif len(date_split) == 1:
          month = date_split[0]
          day = 0
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

#for yearS 2006-2002
@views.route('/update/v6/<int:year>')
def update_year6(year):
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
      elif len(a_album)==3:
        #have to do extra tests becuase cLOUDDEAD in 2004
        treated_as_full_collumn = False
        month_list = ['January', 'February', 'March','April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

        month_test = a_album[0]
        month_test = month_test.lower()
        month_test = month_test.split(' ')

        for month in month_list:
          month = month.lower()
          for test_element in month_test:
            if month == test_element:
              #treating like full collumn
              
              date = a_album[0]
              date_split = date.split(" ")
              month = date_split[0]
              day = date_split[1]
              artist = a_album[1]
              album_name = a_album[2]

              record_label = ""
              # record_label = source_cleanup(record_label)
              year = soup.find(id="firstHeading").string
              year = title_cleanup(year)

              new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
              db.session.add(new_album)
              db.session.commit()
              print("Sucessfully Updated DB")

              treated_as_full_collumn = True
              break
            #handing 1996-- unknown dates
        if 'Unknown' in a_album[0] or 'unknown' in a_album[0] or 'N/A' in a_album[0]:
              #treated as full collumn  with unknown date
              #lowercase u used in 1987
              #na in 1986
              
              date = 'Unknown'
              month = date
              day = date
              artist = a_album[1]
              album_name = a_album[2]
              #source clean b/c 1986 schoolly d saturday night
              album_name = source_cleanup2(album_name)
              record_label = ""

              year = soup.find(id="firstHeading").string
              year = title_cleanup(year)

              new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
              db.session.add(new_album)
              db.session.commit()
              print("Sucessfully Updated DB")
              print('cool')
              treated_as_full_collumn = True
                  

        #treating as missing date collumn
        if treated_as_full_collumn == False:
          date = 0
          month = date
          day = date
          artist = a_album[0] #instead of a_album[1]
          album_name = a_album[1] #instead of a_album[2]
          record_label = a_album[2]
          record_label = source_cleanup(record_label)
          year = soup.find(id="firstHeading").string
          year = title_cleanup(year)
          # print('Test: ', album_name)

          new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
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
        #need if statement b/c 1 random source in day <td>      
        if 'Pete Rock' in a_album[1]:
          day = source_cleanup2(day)
        album_name = a_album[2]
        record_label = a_album[3]
        record_label = source_cleanup(record_label)
        year = soup.find(id="firstHeading").string
        year = title_cleanup(year)

        new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
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

#for yearS 2001-1998
@views.route('/update/v7/<int:year>')
def update_year7(year):
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
      elif len(a_album)<2:
        pass
      elif len(a_album)==2:
        date = 0
        month = date
        day = date
        artist = a_album[0]
        album_name = a_album[1]
        record_label = ""
        # record_label = source_cleanup(record_label)
        year = soup.find(id="firstHeading").string
        year = title_cleanup(year)

        new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
        db.session.add(new_album)
        db.session.commit()
        print("Sucessfully Updated DB")
      else:
        #is the correct size so should have correct collumns. so has day published
        
        date = a_album[0]
        date_split = date.split(" ")
        month = date_split[0]
        day = date_split[1]
        artist = a_album[1]
        
        album_name = a_album[2]
        record_label =""
        year = soup.find(id="firstHeading").string
        year = title_cleanup(year)

        new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
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
      search_by_day = Album.query.filter(Album.day.like(search_formated)).all()

      search_by_artist = Album.query.filter(Album.artist.like(search_formated)).all()
      search_by_album_name = Album.query.filter(Album.name.like(search_formated)).all()
      search_by_record_label = Album.query.filter(Album.record_label.like(search_formated)).all()
      

      def append_results(searched_list, results):
        for item in searched_list:
          results.append(item)
        return results

      results = []
      results = append_results(search_by_year, results)
      results = append_results(search_by_month, results)
      results = append_results(search_by_day, results)
      results = append_results(search_by_artist, results)
      results = append_results(search_by_album_name, results)
      results = append_results(search_by_record_label, results)

      results_no_duplicates = []
      
      [results_no_duplicates.append(x) for x in results if x not in results_no_duplicates]

      return render_template('search.html', results=results_no_duplicates)
      
      
      

      ####working!!!!!!!!!!!!!!!!!!!!!!!!!
      # return render_template('search.html', results_year=search_by_year, results_month=search_by_month, results_day =search_by_day, results_artist=search_by_artist, results_album_name=search_by_album_name, results_record_label=search_by_record_label)


    print(searchwords)

  return render_template('search.html')
  # return render_template('list.html', album_list=album_year, year=year)



#########


#updating all albums with 1 action
@views.route('/update/all')
def update_all():
  album_all = Album.query.all() #album_year
  #print(album_year)
  # year = int(year)
  start_year = 2021
  end_year = 1980
    
  if not album_all:
    year_tracker = start_year
    for num in range(start_year, end_year, -1):
      
      source_txt = 'https://en.wikipedia.org/wiki/'+str(year_tracker)+'_in_hip_hop_music'
      source = requests.get(source_txt).text
      soup = BeautifulSoup(source, 'lxml')

      #Updating years 2021-2017
      if year_tracker <= 2021 and year_tracker >= 2017:
        mytables = soup.find_all('table', {'class':'wikitable'})

        #used for looping through mytables.
        last_table_loc = 0
        if year_tracker == 2021:
          last_table_loc = 10 #2021 only up to September(10/2021 (FOR NOW!!!) must limit tables parsed through to avoid errors from other tables
        else: 
          #used for 2020-2017
          last_table_loc = 12
        
        # parsing through mytables 
        #and later adding ablums to db
        for a_table in itertools.islice(mytables , 0, last_table_loc):
          month = a_table.find_previous_sibling('h3')
          tables_albums = get_table_rows(a_table)
          #parsing through albums in the table
          for a_album in tables_albums:
            #checking number of collumns
            if len(a_album) <=2:
              pass
            elif len(a_album) == 4 or len(a_album) == 3:
              #incomplete collumn
              #if len == 4 row missing date
              #if len == 3 missing date and another <td>
              #ex) Busdriver/Electricity Is on Our Side/Temporary Whatever in 2018 only 3 <td>
              day = 0  #missing date so set to 0
              month_str = month.span.string
              artist = a_album[0] #instead of a_album[1]
              album_name = a_album[1] #instead of a_album[2]
              record_label = a_album[2] #instead of a_album[3]
              record_label = source_cleanup(record_label)
              year = soup.find(id="firstHeading").string
              year = title_cleanup(year)

              new_album = Album(month=month_str, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
              db.session.add(new_album)
              db.session.commit()
            else: 
              #complete collumn
              #if len(a_album) == 5
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
        #Fixing Missing Dates
        album_year = Album.query.filter_by(year=year_tracker)
        for albums in album_year:
          albums.day = fix_dates(albums)
        db.session.commit()

      #Updating years 2016-2013
      elif year_tracker <= 2016 and year_tracker >= 2013 or year_tracker == 2007:
        main_table = soup.find('table', {'class':'wikitable'})
        tables_albums = get_table_rows(main_table)
        #parsing through albums in the table
        for a_album in tables_albums:
          if len(a_album)<=2:
            pass
          elif len(a_album)==4 or len(a_album)==3:
            #incomplete row
            date = 0
            month = date
            day = date
            artist = a_album[0] #instead of a_album[1]
            album_name = a_album[1] #instead of a_album[2]
            record_label = a_album[2]
            record_label = source_cleanup(record_label)
            year = soup.find(id="firstHeading").string
            year = title_cleanup(year)

            new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
            db.session.add(new_album)
            db.session.commit()
          else:
            #complete rows
            #if len(a_album)==5
            date = a_album[0]
            date_split = date.split(" ")
            month = date_split[0]
            day = date_split[1]
            artist = a_album[1]
            album_name = a_album[2]
            record_label = a_album[3]
            record_label = source_cleanup(record_label)
            year = soup.find(id="firstHeading").string
            year = title_cleanup(year)

            new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
            db.session.add(new_album)
            db.session.commit()
          
        album_year = Album.query.filter_by(year=year_tracker)
        for albums in album_year:
          albums_array = fix_dates(albums)
          albums.month = albums_array[0]
          albums.day = albums_array[1]
        db.session.commit()
      #Updating year 2012
      elif year_tracker == 2012:
        if len(a_album)<=3:
          pass
        elif len(a_album) == 4:
          date = 0
          month = date
          day = date
          artist = a_album[0] #instead of a_album[1]
          album_name = a_album[1] #instead of a_album[2]
          record_label = a_album[2]
          record_label = source_cleanup(record_label)
          year = soup.find(id="firstHeading").string
          year = title_cleanup(year)

          new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
          db.session.add(new_album)
          db.session.commit()
        elif len(a_album)==5:
          treated_as_full_collumn = False
          month_list = ['January', 'February', 'March','April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

          month_test = a_album[0]
          month_test = month_test.lower()
          month_test = month_test.split(' ')

          for month in month_list:
            month = month.lower()
            for test_element in month_test:
              if month == test_element:
                #even if len==5. This row treated like full collumn
                #month matched so date is in the first collumn
                #missing col from rowspanned <td> for notes
                date = a_album[0]
                date_split = date.split(" ")
                month = date_split[0]
                day = date_split[1]
                artist = a_album[1]
                album_name = a_album[2]
                record_label = a_album[3]
                record_label = source_cleanup(record_label)
                year = soup.find(id="firstHeading").string
                year = title_cleanup(year)

                new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
                db.session.add(new_album)
                db.session.commit()
                print("Sucessfully Updated DB")

                treated_as_full_collumn = True
                break
          
          if treated_as_full_collumn == False:
            #len()==5 still
            #treating as incomplete collumn (missing date)
            date = 0
            month = date
            day = date
            artist = a_album[0] #instead of a_album[1]
            album_name = a_album[1] #instead of a_album[2]
            record_label = a_album[2]
            record_label = source_cleanup(record_label)
            year = soup.find(id="firstHeading").string
            year = title_cleanup(year)
           
            new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
            db.session.add(new_album)
            db.session.commit()

          print("Sucessfully Updated DB")
        
        else:
          #correct collumns for row
          #if len(a_album)==6
          date = a_album[0]
          date_split = date.split(" ")
          month = date_split[0]
          day = date_split[1]
          artist = a_album[1]
          album_name = a_album[2]
          record_label = a_album[3]
          record_label = source_cleanup(record_label)
          year = soup.find(id="firstHeading").string
          year = title_cleanup(year)

          new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
          db.session.add(new_album)
          db.session.commit()
        print("Sucessfully Updated DB")
        album_year = Album.query.filter_by(year=year)
        #Fixing Dates
        for albums in album_year:
          albums_array = fix_dates(albums)
          albums.month = albums_array[0]
          albums.day = albums_array[1]
        db.session.commit()
      #update year 2011
      elif year_tracker == 2011:
        main_table = soup.find('table', {'class':'wikitable'})

        tables_albums = get_table_rows(main_table)
        #parsing through albums in the table
        for a_album in tables_albums:
          if len(a_album)<3:
            pass
          elif len(a_album)==4 or len(a_album)==3:
            date = 0
            month = date
            day = date
            artist = a_album[0] #instead of a_album[1]
            album_name = a_album[1] #instead of a_album[2]
            year = soup.find(id="firstHeading").string
            year = title_cleanup(year)

            new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=0, year=year)
            db.session.add(new_album)
            db.session.commit()
          else:
            #correct collumns in row
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
      
        album_year = Album.query.filter_by(year=year_tracker)
        for albums in album_year:
          albums_array = fix_dates(albums)
          albums.month = albums_array[0]
          albums.day = albums_array[1]
        db.session.commit()
      #for years 2010-2008 and 1997
      elif year_tracker<=2010 and year_tracker>=2008 or year_tracker==1997:
        tables_albums = get_table_rows(main_table)
        #parsing through albums in the table
        for a_album in tables_albums:
          if len(a_album)<=2:
            pass
          elif len(a_album)==3:
            #incomplete collumn in row
            date = 0
            month = date
            day = date
            artist = a_album[0] #instead of a_album[1]
            album_name = a_album[1] #instead of a_album[2]
            year = soup.find(id="firstHeading").string
            year = title_cleanup(year)

            new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=0, year=year)
            db.session.add(new_album)
            db.session.commit()
          else:
            #correct collumns in row
            date = a_album[0]
            date_split = date.split(" ")
            print(date_split)
            #test bc error thrown at (1997) June Esham	Bruce Wayne: Gothom City 1987
            #has month but is missing day value
            if len(date_split) == 2:
              month = date_split[0]
              day = date_split[1]
            elif len(date_split) == 1:
              month = date_split[0]
              day = 0
            artist = a_album[1]
            album_name = a_album[2]
            year = soup.find(id="firstHeading").string
            year = title_cleanup(year)

            new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=0, year=year)
            db.session.add(new_album)
            db.session.commit()

        print("Sucessfully Updated DB")
        
        album_year = Album.query.filter_by(year=year_tracker)
        for albums in album_year:
          albums_array = fix_dates(albums)
          albums.month = albums_array[0]
          albums.day = albums_array[1]
        db.session.commit()
      #elif year_tracker == 2007: #used with 2016-2013

      #for 2006-2002 or 1996-1998
      elif year_tracker <= 2006 and year_tracker >= 2002 or year_tracker <= 1996 and year_tracker >= 1998:
        main_table = soup.find('table', {'class':'wikitable'})

        tables_albums = get_table_rows(main_table)
            #parsing through albums in the table
        for a_album in tables_albums:
          #print('Album length:',len(a_album))
          if len(a_album)<=2:
            pass
          elif len(a_album)==3:
            #have to do extra tests becuase cLOUDDEAD in 2004
            treated_as_full_collumn = False
            month_list = ['January', 'February', 'March','April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
            month_test = a_album[0]
            month_test = month_test.lower()
            month_test = month_test.split(' ')
            #first test
            for month in month_list:
              month = month.lower()
              for test_element in month_test:
                if month == test_element:
                  #treating like full collumn
                  date = a_album[0]
                  date_split = date.split(" ")
                  month = date_split[0]
                  day = date_split[1]
                  artist = a_album[1]
                  album_name = a_album[2]

                  record_label = ""
                  # record_label = source_cleanup(record_label)
                  year = soup.find(id="firstHeading").string
                  year = title_cleanup(year)

                  new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
                  db.session.add(new_album)
                  db.session.commit()
                  print("Sucessfully Updated DB")

                  treated_as_full_collumn = True
                  break
            #second test
            #handing 1996-- unknown dates
            if 'Unknown' in a_album[0] or 'unknown' in a_album[0] or 'N/A' in a_album[0]:
              #treated as full collumn  with unknown date
              #lowercase u used in 1987
              #na in 1986
              date = 'Unknown'
              month = date
              day = date
              artist = a_album[1]
              album_name = a_album[2]
              #source clean b/c 1986 schoolly d saturday night
              album_name = source_cleanup2(album_name)
              record_label = ""
              year = soup.find(id="firstHeading").string
              year = title_cleanup(year)

              new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
              db.session.add(new_album)
              db.session.commit()
              print("Sucessfully Updated DB")
              print('cool')
              treated_as_full_collumn = True
                 
            #treating as missing date collumn
            if treated_as_full_collumn == False:
              date = 0
              month = date
              day = date
              artist = a_album[0] #instead of a_album[1]
              album_name = a_album[1] #instead of a_album[2]
              record_label = a_album[2]
              record_label = source_cleanup(record_label)
              year = soup.find(id="firstHeading").string
              year = title_cleanup(year)

              new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
              db.session.add(new_album)
              db.session.commit()
          else:
            #correct num of collumns in row
            # if len() == 4
            date = a_album[0]
            date_split = date.split(" ")
            month = date_split[0]
            day = date_split[1]
            artist = a_album[1]
            #need if statement b/c 1 random source in day <td>      
            if 'Pete Rock' in a_album[1]:
              day = source_cleanup2(day)
            album_name = a_album[2]
            record_label = a_album[3]
            record_label = source_cleanup(record_label)
            year = soup.find(id="firstHeading").string
            year = title_cleanup(year)

            new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
            db.session.add(new_album)
            db.session.commit()

        print("Sucessfully Updated DB")
      
        album_year = Album.query.filter_by(year=year_tracker)
        for albums in album_year:
          albums_array = fix_dates(albums)
          albums.month = albums_array[0]
          albums.day = albums_array[1]
        db.session.commit()
      
      #For years 2001-1998
      elif year_tracker <= 2001 and year_tracker >= 1998:
        if len(a_album)<2:
          pass
        elif len(a_album)==2:
          date = 0
          month = date
          day = date
          artist = a_album[0]
          album_name = a_album[1]
          record_label = ""
          # record_label = source_cleanup(record_label)
          year = soup.find(id="firstHeading").string
          year = title_cleanup(year)

          new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
          db.session.add(new_album)
          db.session.commit()
          print("Sucessfully Updated DB")
        else:
          #correct collumns
          date = a_album[0]
          date_split = date.split(" ")
          month = date_split[0]
          day = date_split[1]
          artist = a_album[1]
          
          album_name = a_album[2]
          record_label =""
          year = soup.find(id="firstHeading").string
          year = title_cleanup(year)

          new_album = Album(month=month, day=day, artist=artist, name=album_name, record_label=record_label, year=year)
          db.session.add(new_album)
          db.session.commit()

        print("Sucessfully Updated DB")
        
        album_year = Album.query.filter_by(year=year)
        for albums in album_year:
          albums_array = fix_dates(albums)
          albums.month = albums_array[0]
          albums.day = albums_array[1]
        db.session.commit()

      tables_albums = get_table_rows(main_table)
      year_tracker = year_tracker - 1

    #end of for loop that goes through years
    #still need to :
    #render_template   
    #export
    #delete_all
    album_all = Album.query.all()

    return render_template('list_all.html', album_list=album_all)


#Runs when delete btn is pressed
@views.route('/delete_all')
def delete():
  all_albums = Album.query.delete()
  db.session.commit()
  all_albums = Album.query
  return render_template('list_all.html', album_list=all_albums)


@views.route('/export')
def export():
  album_all = Album.query.all()
  write_to_csv(album_all)
  
  return render_template('home.html')


def write_to_csv(album_list):
  with open('albums.csv', mode='w') as album_file:
    album_writer = csv.writer(album_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    #writing header
    album_writer.writerow(['Month', 'Day', 'Artist', 'Album_Name', 'Record_Label', 'Year'])

    for album_indiv in album_list:
      #writing data
       album_writer.writerow([album_indiv.month, album_indiv.day, album_indiv.artist, album_indiv.name, album_indiv.record_label, album_indiv.year])

