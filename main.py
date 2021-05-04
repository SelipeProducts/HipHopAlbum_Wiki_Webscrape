from website import create_app
import random



#-----------------------------------------------------
#Flask Main Code
app = create_app()

if __name__ == '__main__':
  app.debug = True
  app.run(host='0.0.0.0', port=random.randint(2000, 9000))

#----------------------------------------------------
#----------------------------------------------------

# source = requests.get('https://en.wikipedia.org/wiki/2021_in_hip_hop_music').text

# soup = BeautifulSoup(source, 'lxml')

# def writefile(filename, txt):
#   with open(filename, 'w') as writer:
#      writer.write(str(txt))

# textfile_name = 'albums.txt'

# # get text where div has id== bodyContent
# body_content = soup.find(id='bodyContent')

# mytables = soup.find_all('table', {'class':'wikitable'})

# # writefile(textfile_name, mytables[0])


# #-------------
# def get_table_rows(the_table):
#   albums =[]
#   table_rows = the_table.find_all('tr')
#   for tr in table_rows:
#     td = tr.find_all('td')
#     row = [i.text for i in td] #list comprehension
#     # print(row)
#     albums.append(row)
#   return albums

# website_albums = []
# for a_table in mytables:
#   month = a_table.find_previous_sibling('h3')
#   print(month.span.string)
#   print()
#   tables_albums = get_table_rows(a_table)
#   website_albums.append(tables_albums)

# #is this the best way to pull and organize this information??????
# #do i get date (month) first and then read table after?
# #or do i loop through tables (like i alreadyy did) and check prevous sibling element

# #-----------------------------------------------------
# #-----------------------------------------------------
# table0 = mytables[0]

# albums = []
# table_rows = table0.find_all('tr')
# for tr in table_rows:
#   td = tr.find_all('td')
#   row = [i.text for i in td] #list comprehension
#   # print(row)
#   albums.append(row)

# print(albums[1])

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

# #-----------------------------------------------------
#-----------------------------------------------------