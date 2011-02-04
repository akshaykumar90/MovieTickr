#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

# Helper Script for MovieTickrScreenlet (c) XIM ESSX 2009 <akshaykumar90@gmail.com>

# Build 1.29
# Build date: 29/01/2009
# Beta Release

import os
import imdb
import urllib
import xml.dom.minidom

def main():
  folders = []
  if os.path.isfile(os.getcwd() + '/folders.xml'):
    fdoc = xml.dom.minidom.parse(os.getcwd() + '/folders.xml')
    for fpath in fdoc.getElementsByTagName("path"):
      fpath.normalize()
      fname = fpath.firstChild.data.strip()
      folders.append(fname)
  
  i = imdb.IMDb()
  use_types = ['.avi', '.divx']
  movs = []
  cwd = os.getcwd()
  fname = cwd + '/data.xml'
    
  if os.path.isfile(fname):
    doc = xml.dom.minidom.parse(fname)
    for filepath in doc.getElementsByTagName("filename"):
      filepath.normalize()
      name = filepath.firstChild.data.strip()
      slist = name.split('/',3)
      part = '/'.join([slist[0],slist[1],slist[2]])
      if os.path.isfile(name):
        movs.append(name)
      elif os.path.exists(part):
        filepath.parentNode.parentNode.removeChild(filepath.parentNode)
        os.remove(filepath.parentNode.childNodes[1].firstChild.data)
    # Retrieve the already created <data> base element
    data = doc.documentElement
  else:
    # Create the minidom document
    doc = xml.dom.minidom.Document()
        
    # Create the <data> base element
    data = doc.createElement("data")
    doc.appendChild(data)
    
  for folder in folders:
    for root, dirs, files in os.walk(folder): 
      for file in files:
        continue_to_next_file = False
        
        if os.path.splitext(file)[1].lower() in use_types:
          upath = os.path.join(root, file)
          if upath not in movs:
            movie = '#dummy#'
            name = os.path.splitext(os.path.split(upath)[1])[0]
            print 'File found: %s' % name
                        
            while(True):
              try:
                results = i.search_movie(name)
              except imdb.IMDbError, e:
                print "Probably you're not connected to Internet.\nPlease try again later\nQuitting..."
                return 3
                
              if results:
                print 'Best match for "%s"' % name
                movie = results[0]
                print movie.summary()
      
                print 'Continue?(y/n/x):',
                ch = raw_input()
                if ch.lower() == 'y':
                  break
                elif ch.lower() == 'n':
                  # Print other results.
                  print '%s result%s for "%s":' % (len(results),
                                                  ('', 's')[len(results) != 1],
                                                  name)
                  print 'ID\t : Year\t : Title'
      
                  # Print the ID, year and title for every movie.
                  l=1
                  for movie in results:
                    outp = '%d\t : %s\t : %s' % (l,movie['year'],movie['title'])
                    print outp
                    l += 1
      
                  print 'Select the corresponding movieID or 0 for none:',
                  ch = int(raw_input())
                  if ch != 0:
                    movie = results[ch-1]
                    break
                else:
                  xml_to_be_written = doc.toprettyxml(indent="", newl="", encoding="UTF-8")
                  print xml_to_be_written
    
                  fp = open(cwd + '/data.xml',"w")
                  fp.write(xml_to_be_written)
                  fp.close()
                  return 0
  
              else:
                print 'No matches for "%s", sorry.' % name
      
              print 'Provide alternate name?(y/n/x):',
              ch = raw_input()
              if ch.lower() == 'y':
                print 'Enter alternate name:',
                name = raw_input()
              elif ch.lower() == 'n':
                continue_to_next_file = True
                break
              else:
                xml_to_be_written = doc.toprettyxml(indent="", newl="", encoding="UTF-8")
                print xml_to_be_written
    
                fp = open(cwd + '/data.xml',"w")
                fp.write(xml_to_be_written)
                fp.close()
                return 0
            
            if continue_to_next_file: continue
            
            try:
              i.update(movie)
              i.update(movie,'taglines')
            except imdb.IMDbError, e:
              print "Probably you're not connected to Internet.\nPlease try again later\nQuitting..."
              xml_to_be_written = doc.toprettyxml(indent="", newl="", encoding="UTF-8")
              print xml_to_be_written
    
              fp = open(cwd + '/data.xml',"w")
              fp.write(xml_to_be_written)
              fp.close()
              return 3

            imagespath = cwd + '/images/'
            if not os.path.exists(imagespath):
              os.makedirs(imagespath)
            
            imgpath = imagespath + name + movie['cover url'][movie['cover url'].rfind('.'):]
            try:
              urllib.urlretrieve(movie['cover url'], imgpath)
            except Exception:
              print "Probably you're not connected to Internet.\nPlease try again later\nQuitting..."
              xml_to_be_written = doc.toprettyxml(indent="", newl="", encoding="UTF-8")
              print xml_to_be_written
    
              fp = open(cwd + '/data.xml',"w")
              fp.write(xml_to_be_written)
              fp.close()
              return 3
            
            # Create the <movie> element
            moviexml = createXML(doc, movie, upath, imgpath)
            data.appendChild(moviexml)
      
            movs.append(upath)
    
  xml_to_be_written = doc.toprettyxml(indent="", newl="", encoding="UTF-8")
  print xml_to_be_written
    
  fp = open(cwd + '/data.xml',"w")
  fp.write(xml_to_be_written)
  fp.close()
    
def createXML(doc, movie, path, imgpath):
  # Create the <movie> element
  root = doc.createElement("movie")

  # Create the <filename> element
  filename = doc.createElement("filename")
  root.appendChild(filename)

  # Give the <filename> elemenet some text
  filenametext = doc.createTextNode(path)
  filename.appendChild(filenametext)
  
  # Create the <imagepath> element
  imagepath = doc.createElement("imagepath")
  root.appendChild(imagepath)

  # Give the <filename> elemenet some text
  imagepathtext = doc.createTextNode(imgpath)
  imagepath.appendChild(imagepathtext)

  # Create the <title> element
  title = doc.createElement("title")
  root.appendChild(title)

  # Give the <title> elemenet some text
  titletext = doc.createTextNode(movie['title'])
  title.appendChild(titletext)

  # Create the <year> element
  year = doc.createElement("year")
  root.appendChild(year)

  # Give the <year> elemenet some text
  yeartext = doc.createTextNode(movie['year'])
  year.appendChild(yeartext)

  # Create the <rating> element
  rating = doc.createElement("rating")
  root.appendChild(rating)

  # Give the <rating> elemenet some text
  ratingtext = doc.createTextNode(unicode(str(movie['rating']),'utf-8'))
  rating.appendChild(ratingtext)

  # Create the <director> element
  director = doc.createElement("director")
  root.appendChild(director)

  # Give the <director> elemenet some text
  directortext = doc.createTextNode(movie['director'][0]['name'])
  director.appendChild(directortext)

  # Create the <genres> element
  genres = doc.createElement("genres")
  root.appendChild(genres)

  j=0
  for gt in movie['genres']:
    # Create the <genre> element
    genre = doc.createElement("genre")
    genres.appendChild(genre)
    # Give the <genre> elemenet some text
    genretext = doc.createTextNode(movie['genres'][j])
    genre.appendChild(genretext)
    j += 1
    if j == 3:
      break

  if movie.has_key('taglines'):
    # Create the <tagline> element
    tagline = doc.createElement("tagline")
    root.appendChild(tagline)

    # Give the <tagline> elemenet some text
    taglinetext = doc.createTextNode(movie['taglines'][0])
    tagline.appendChild(taglinetext)

  # Create the <runtime> element
  runtime = doc.createElement("runtime")
  root.appendChild(runtime)

  # Give the <runtime> elemenet some text
  runtimetext = doc.createTextNode(movie['runtimes'][0])
  runtime.appendChild(runtimetext)

  # Create the <cast> element
  cast = doc.createElement("cast")
  root.appendChild(cast)

  j=0
  for cm in movie['cast']:
    # Create the <member> element
    member = doc.createElement("member")
    cast.appendChild(member)
    # Give the <member> elemenet some text
    membertext = doc.createTextNode(movie['cast'][j]['name'])
    member.appendChild(membertext)
    j += 1
    if j == 3:
      break

  # Create the <seen> element
  seen = doc.createElement("seen")
  root.appendChild(seen)

  # Give the <seen> elemenet some text
  seentext = doc.createTextNode(unicode('0','utf-8'))
  seen.appendChild(seentext)
  
  return root
    
if __name__ == '__main__': main()
