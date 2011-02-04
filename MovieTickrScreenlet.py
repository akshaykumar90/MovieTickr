#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!

# MovieTickrScreenlet (c) XIM ESSX 2009 <akshaykumar90@gmail.com>

# Build 1.29
# Build date: 29/01/2009
# Beta Release

import screenlets
from screenlets.options import BoolOption, IntOption, ListOption
from screenlets import DefaultMenuItem
import xml.dom.minidom
import commands
import gobject
import gtk
import cairo
import os


class MovieTickrScreenlet (screenlets.Screenlet):
	"""A Movie Ticker Screenlet which aims at organizing and showcasing
	your movie collection. It can watch multiple folders for movies and
	fetches movie info from IMDb.com using the IMDbPy package."""
	
	# default meta-info for Screenlets (should be removed and put into metainfo)
	__name__	= 'MovieTickrScreenlet'
	__version__	= '0.1'
	__author__	= 'Akshay Kumar'
	__desc__	= __doc__	# set description to docstring of class
	
	# attributes
	__timer = None
	__start = False
	# editable options
	home = commands.getoutput("echo $HOME")
	folders = [home]
	update_interval = 50
	update_interval_fast = 20
	reverse_direction = False
	
	screenlet_width = 460
	screenlet_height = 190
	
	# constructor
	def __init__ (self, **keyword_args):
		screenlets.Screenlet.__init__(self, width=self.screenlet_width, uses_theme=True, **keyword_args)
		# set theme
		self.theme_name = "default"
		# add option group
		self.add_options_group('MovieTickr', 'MovieTicker related settings...')
		# add editable option to the group
		self.add_option(ListOption('MovieTickr', 'folders', self.folders, 'Folders to Watch', \
										'Add/Remove folders to look in for movies'))
		self.add_option(IntOption('MovieTickr', 'update_interval', self.update_interval, 'Speed', \
										'Speed of the movie ticker (in milliseconds, lower means faster)', min=1, max=2000))
		self.add_option(IntOption('MovieTickr', 'update_interval_fast', self.update_interval_fast, \
										'Browsing Speed', 'Browsing speed of the movie ticker (in milliseconds, lower means faster)', min=1, max=2000))
		self.add_option(BoolOption('MovieTickr', 'reverse_direction', bool(self.reverse_direction), \
										'Reverse Direction','Move the ticker in opposite direction'))
			
		cwd = self.get_screenlet_dir()
		self.fname = cwd + '/data.xml'
		
		self.reload()

	def reload (self):
		if self.__timer:
			gobject.source_remove(self.__timer)
			
		if self.__start:
			self.__start = False
			
		self.imgs = []
		if os.path.isfile(self.fname):
			self.doc = xml.dom.minidom.parse(self.fname)
			for imagepath in self.doc.getElementsByTagName("imagepath"):
				imagepath.normalize()
				img = imagepath.firstChild.data.strip()
				self.imgs.append(img)

			i = 0
			self.queuePixBuf = []
			self.queueImage = []
			self.queueMatrix = []
			self.xlist = []
			x= 60
			while x < 400:
				self.xlist.append(x)
				w, h = self.get_image_size(self.imgs[i])
				w = int((float(w) / h) * 150)
				h = 150
				pixbuf = gtk.gdk.pixbuf_new_from_file(self.imgs[i]).scale_simple(w,h,gtk.gdk.INTERP_HYPER) 
				format = cairo.FORMAT_RGB24 
				if pixbuf.get_has_alpha():format = cairo.FORMAT_ARGB32 
				iw = pixbuf.get_width() 
				ih = pixbuf.get_height() 
				image = cairo.ImageSurface(format, iw, ih) 
				matrix = cairo.Matrix(xx=iw/w, yy=ih/h) 
				self.queuePixBuf.append(pixbuf)
				self.queueImage.append(image)
				self.queueMatrix.append(matrix)
				x += w + 5
				i += 1
				if i == len(self.imgs): i = 0
			
			self.next = i
			
			self.__start = True
			self.__timer = gobject.timeout_add( self.update_interval, self.update)
			self.moving = True
		else:
			self.moving = False
		self.movingreverse = False
		self.fastmoving = False
		self.fastmovingreverse = False
		self.showInfo = False
		self.movieIndex = 0
		self.isOpen = False
		self.saveChanges = False
	
	def __setattr__ (self, name, value):
			screenlets.Screenlet.__setattr__(self, name, value)
			if name == 'folders':
				fdoc = xml.dom.minidom.Document()
				data = fdoc.createElement("folders")
				fdoc.appendChild(data)
				for item in self.folders:
					path = fdoc.createElement("path")
					data.appendChild(path)
					pathtext = fdoc.createTextNode(unicode(item,'utf-8'))
					path.appendChild(pathtext)
				rxml = fdoc.toprettyxml(indent="", newl="", encoding="UTF-8")
				fp = open(self.get_screenlet_dir() + '/folders.xml',"w")
				fp.write(rxml)
				fp.close()
			if name == 'update_interval':
				if self.__start:
					if self.__timer:
						gobject.source_remove(self.__timer)
					self.__timer = gobject.timeout_add(self.update_interval, self.update)
			if name == 'update_interval_fast':
				print 'New fast speed:',self.update_interval_fast
			if name == 'reverse_direction':
				if self.__start:
					if self.movingreverse != self.reverse_direction:
						self.movingreverse = not self.movingreverse
						if self.movingreverse:
							self.next -= (len(self.xlist) + 1) % len(self.imgs)
							if self.next < 0:
								self.next += len(self.imgs)
						else:
							self.next  += (len(self.xlist) + 1) % len(self.imgs)
							if self.next >= len(self.imgs):
								self.next -= len(self.imgs) 
					
	def update (self):
		self.redraw_canvas()
		return True # keep running this event	
	
	def on_init (self):
		"""Called when the Screenlet's options have been applied and the 
		screenlet finished its initialization. If you want to have your
		Screenlet do things on startup you should use this handler."""
		
		# add default menu items
		self.add_default_menuitems()
	
	def on_mouse_down (self, event):
		"""Called when a buttonpress-event occured in Screenlet's window. 
		Returning True causes the event to be not further propagated."""
		x, y = self.window.get_pointer()
		x /= (self.scale)
		y /= (self.scale)
		if self.__start:
			if x >= 6 and x <= 54 and y>=61 and y <= 109:
				if self.__timer:
					gobject.source_remove(self.__timer)
				self.__timer = gobject.timeout_add( self.update_interval_fast, self.update)
				self.fastmoving = True
				if self.movingreverse:
					self.next  += (len(self.xlist) + 1) % len(self.imgs)
					if self.next >= len(self.imgs):
						self.next -= len(self.imgs) 
				
				
			if x >= 406 and x <= 436 and y>=61 and y <= 109:
				if self.__timer:
					gobject.source_remove(self.__timer)
				self.__timer = gobject.timeout_add( self.update_interval_fast, self.update)
				self.fastmovingreverse = True
				if not self.movingreverse:
					self.next -= (len(self.xlist) + 1) % len(self.imgs)
					if self.next < 0:
						self.next += len(self.imgs)
				
			if x >= 416 and x <= 436 and y>=170 and y <= 190:
				self.isOpen = not self.isOpen
				if (self.isOpen): 
					self.screenlet_height = 360
				else:
					self.screenlet_height = 190
					
			if x >= 394 and x <= 414 and y>=170 and y <= 190:
				xml_to_be_written = self.doc.toprettyxml(indent="", newl="", encoding="UTF-8")
				print xml_to_be_written
				fp = open(self.get_screenlet_dir() + '/data.xml',"w")
				fp.write(xml_to_be_written)
				fp.close()
					
			if self.showInfo and x >= 388 and x <= 452 and y>=192 and y <= 256:
				node = self.doc.getElementsByTagName("seen")[self.movieIndex]
				isSeen = int(node.firstChild.data)
				# Create the new <seen> element
				seen = self.doc.createElement("seen")

				# Give the <seen> elemenet some text
				if not isSeen:
					seentext = self.doc.createTextNode(unicode('1','utf-8'))
				else:
					seentext = self.doc.createTextNode(unicode('0','utf-8'))
				seen.appendChild(seentext)
				
				node.parentNode.replaceChild(seen, node)
				self.saveChanges = True
				
			if x >= 60 and x <= 400 and y>=10 and y <= 160:
				first = 60
				for i in range(1,len(self.xlist)+1):
					if i==len(self.xlist):
						second = self.width - 60
					else:
						second = self.xlist[i] - 5
					if x > first and x < second:
						if self.movingreverse:
							step = i
						else:
							step = len(self.xlist) - i + 1
						start =  self.next
						loc = step % len(self.imgs)
						if self.movingreverse:
							self.movieIndex = self.next + loc
							if self.movieIndex >= len(self.imgs):
								self.movieIndex -= len(self.imgs)
						else:
							self.movieIndex = self.next - loc
						self.showInfo = True
					first = second + 5
					
		if x >= 438 and x <= 458 and y>=170 and y <= 190:
			self.reload()
			# self.movingreverse is false irrespective of initial conditions
			# Hence switch it if required
			if self.__start:
				if self.movingreverse != self.reverse_direction:
					self.movingreverse = not self.movingreverse
					self.next -= (len(self.xlist) + 1) % len(self.imgs)
					if self.next < 0:
						self.next += len(self.imgs)
		
		return False
	
	def on_mouse_enter (self, event):
		"""Called when the mouse enters the Screenlet's window."""
		x, y = self.window.get_pointer()
		x /= (self.scale)
		y /= (self.scale)
		if self.__start:
			if x >= 6 and x <= 54 and y>=61 and y <= 109:
				if self.__timer:
					gobject.source_remove(self.__timer)
				self.__timer = gobject.timeout_add( self.update_interval, self.update)
				self.fastmoving = False 
				if self.movingreverse:
					self.next -= (len(self.xlist) + 1) % len(self.imgs)
					if self.next < 0:
						self.next += len(self.imgs)
				
			if x >= 406 and x <= 436 and y>=61 and y <= 109:
				if self.__timer:
					gobject.source_remove(self.__timer)
				self.__timer = gobject.timeout_add( self.update_interval, self.update)
				self.fastmovingreverse = False
				if (not self.movingreverse):
					self.next  += (len(self.xlist) + 1) % len(self.imgs)
					if self.next >= len(self.imgs):
						self.next -= len(self.imgs)
			
	def on_mouse_move(self, event):
		"""Called when the mouse moves in the Screenlet's window."""
		x, y = self.window.get_pointer()
		x /= (self.scale)
		y /= (self.scale)
		if self.__start:
			if x >= 60 and x <= 400 and y>=5 and y <= 165:
				if self.__timer and self.moving:
					gobject.source_remove(self.__timer)
					self.moving = False
			else:
				if not self.moving:
					self.__timer = gobject.timeout_add( self.update_interval, self.update)
					self.moving = True
	
	def draw_info_box(self, ctx):
		data = self.doc.documentElement
		caption = ['Director','Genre','Tagline','Runtime','Cast']
		showTagline = False
		if self.showInfo:
			for node in data.childNodes[self.movieIndex].childNodes:
				if node.tagName == 'rating':
					rating = float(node.firstChild.data)
				elif node.tagName == 'director':
					director = node.firstChild.data
				elif node.tagName == 'genres':
					genreText = ''
					for genre in node.childNodes:
						if not genre == genre.parentNode.firstChild:
							genreText += ' | ' + genre.firstChild.data
						else:
							genreText += genre.firstChild.data
				elif node.tagName == 'tagline':
					tagline = node.firstChild.data
					showTagline = True
				elif node.tagName == 'runtime':
					runtime = node.firstChild.data
				elif node.tagName == 'cast':
					members = []
					for member in node.childNodes:
						members.append(member.firstChild.data)
				elif node.tagName == 'seen':
					seen = int(node.firstChild.data)
			for i in range(0,10):
				ctx.move_to(20 + (i*17.5), 200)
				ctx.rel_line_to(2.5,5)
				ctx.rel_line_to(5,0)
				ctx.rel_line_to(-4.5,4)
				ctx.rel_line_to(2.5,5)
				ctx.rel_line_to(-5.5,-3.5)
				ctx.rel_line_to(-5.5,3.5)
				ctx.rel_line_to(2.5,-5)
				ctx.rel_line_to(-4.5,-4)
				ctx.rel_line_to(5,0)
				ctx.close_path()
		
			ctx.set_source_rgb(float(144)/255,float(162)/255,float(142)/255)
			ctx.fill_preserve()
			ctx.save()
			ctx.clip()
			ctx.set_source_rgb(float(247)/255,float(251)/255,float(0)/255)
			self.draw_rectangle(ctx,12.5,200,(15*rating) + (int(rating) * 2.5), 14)
			ctx.restore()
			
			ctx.select_font_face ("Arial", cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_BOLD)
			ctx.set_font_size (14.0)
			
			ctx.set_source_rgb(float(254)/255,float(255)/255,float(34)/255)
			fascent, fdescent, fheight, fxadvance, fyadvance = ctx.font_extents()
			
			i = 0
			j = 0
			while(True):
				if j == 5:
					break
				ctx.move_to (12.5, 214 + (fheight+4) + (fheight+2)*i)
				if j == 2 and not showTagline:
					j += 1
					continue
				ctx.show_text (caption[j])
				i += 1
				j += 1
				
			ctx.set_source_rgb(float(102)/255,float(255)/255,float(203)/255)
			xbearing, ybearing, width, height, xadvance, yadvance =  ctx.text_extents("Runtime ")
			align = xadvance + 20
			
			ctx.move_to (200, 213)
			ctx.show_text (str(rating) + '/10')
			
			i = 0
			j = 0
			while(True):
				if j == 4 + len(members):
					break
				ctx.move_to (12.5 + align, 214 + (fheight+4) + (fheight+2)*i)
				if j == 0:
					ctx.show_text (director)
				elif j == 1:
					ctx.show_text (genreText)
				elif j == 2:
					if showTagline:
						ctx.show_text (tagline)
					else:
						j += 1
						continue
				elif j == 3:
					ctx.show_text (runtime + ' min')
				elif j == 4 or j == 5 or j == 6:
					ctx.show_text (members[j-4])
				i += 1
				j += 1
				
			if self.theme:
				ctx.save()
				ctx.translate(388,192)
				if not seen:
					self.theme.render(ctx, 'no')
				else:
					self.theme.render(ctx, 'yes')
				ctx.restore()
	
	def on_draw (self, ctx):
		"""In here we draw"""
		ctx.scale(self.scale, self.scale)
		if self.height != self.screenlet_height: 
			self.height = self.screenlet_height

		if self.theme:
			ctx.set_source_rgb(float(21)/255,float(12)/255,float(103)/255)
			if self.__start and self.isOpen:
				self.draw_rounded_rectangle(ctx,0,0,14,460,360)
				ctx.set_source_rgb(float(65)/255,float(112)/255,float(206)/255)
				self.draw_rounded_rectangle(ctx,5,195,12,450,160,round_top_left = False, round_top_right=False)
				self.draw_info_box(ctx)
			else:
				self.draw_rounded_rectangle(ctx,0,0,14,460,190,round_bottom_left = False, round_bottom_right=False)
				
			ctx.set_source_rgba(0,0,0,0.8)
			self.draw_rectangle(ctx,60,5,340,160)
			ctx.set_source_rgb(float(241)/255,float(0)/255,float(78)/255)
			self.draw_rectangle(ctx,0,170,460, 20)
			if self.__start and self.theme:
				ctx.save()
				ctx.translate(6,61)
				self.theme.render(ctx, 'previous')
				ctx.translate(400,0)
				self.theme.render(ctx, 'next')
				ctx.restore()
			if self.theme:
				ctx.save()
				ctx.translate(438,170)
				self.theme.render(ctx, 'refresh')
				if self.__start and self.showInfo:
					ctx.translate(-22,0)
					self.theme.render(ctx, 'info')
					if self.saveChanges:
						ctx.translate(-22,0)
						self.theme.render(ctx, 'save')
				ctx.restore()
			if self.__start and self.showInfo:
				ctx.set_source_rgb(float(248)/255,float(255)/255,float(215)/255)
				ctx.select_font_face ("Arial", cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_BOLD)
				ctx.set_font_size (14.0)
				ctx.move_to (10.0, 185)
				data = self.doc.documentElement
				text = "%s (%s)" % (data.childNodes[self.movieIndex].childNodes[2].firstChild.data, \
																			data.childNodes[self.movieIndex].childNodes[3].firstChild.data)
				ctx.show_text (text)
			
			
			ctx.rectangle(60,5,340, 160)
			ctx.clip()
			
			if self.__start:
				for i in range(0,len(self.xlist)):
					if self.fastmoving:
						self.xlist[i] -= 2
					elif self.fastmovingreverse:
						self.xlist[i] += 2
					elif self.movingreverse:
						self.xlist[i] += 1
					else:
						self.xlist[i] -= 1
				
				newElementFlag = False
				removeElementFlag = False
				
				boola = self.movingreverse and self.fastmovingreverse
				boolb = self.fastmovingreverse and not self.movingreverse
				boolc = self.movingreverse and not self.fastmovingreverse and not self.fastmoving
				if boola or boolb or boolc:
					if self.xlist[-1] > 400:
						del self.queuePixBuf[-1]
						del self.queueImage[-1]
						del self.queueMatrix[-1]
						removeElementFlag = True
				else:
					if self.xlist[0] + self.queuePixBuf[0].get_width() < 60:
						del self.queuePixBuf[0]
						del self.queueImage[0]
						del self.queueMatrix[0]
						removeElementFlag = True
			
				newElementWidth = 0
						
				if boola or boolb or boolc:
					if self.xlist[0] > 65:
						w, h = self.get_image_size(self.imgs[self.next])
						w = int((float(w) / h) * 150)
						h = 150
						pixbuf = gtk.gdk.pixbuf_new_from_file(self.imgs[self.next]).scale_simple(w,h,gtk.gdk.INTERP_HYPER) 
						format = cairo.FORMAT_RGB24 
						if pixbuf.get_has_alpha():format = cairo.FORMAT_ARGB32 
						iw = pixbuf.get_width() 
						ih = pixbuf.get_height() 
						newElementWidth = iw
						image = cairo.ImageSurface(format, iw, ih) 
						matrix = cairo.Matrix(xx=iw/w, yy=ih/h) 
						self.queuePixBuf.insert(0,pixbuf)
						self.queueImage.insert(0,image)
						self.queueMatrix.insert(0,matrix)
						if self.next - 1 < 0:
							self.next = len(self.imgs) - 1
						else:
							self.next -= 1			
						newElementFlag = True
				else:
					if self.xlist[-1] + self.queuePixBuf[-1].get_width() + 5 < 400:
						newElementWidth = self.queuePixBuf[-1].get_width()
						w, h = self.get_image_size(self.imgs[self.next])
						w = int((float(w) / h) * 150)
						h = 150
						pixbuf = gtk.gdk.pixbuf_new_from_file(self.imgs[self.next]).scale_simple(w,h,gtk.gdk.INTERP_HYPER) 
						format = cairo.FORMAT_RGB24 
						if pixbuf.get_has_alpha():format = cairo.FORMAT_ARGB32 
						iw = pixbuf.get_width() 
						ih = pixbuf.get_height() 
						image = cairo.ImageSurface(format, iw, ih) 
						matrix = cairo.Matrix(xx=iw/w, yy=ih/h) 
						self.queuePixBuf.append(pixbuf)
						self.queueImage.append(image)
						self.queueMatrix.append(matrix)
						if self.next + 1 == len(self.imgs):
							self.next = 0
						else:
							self.next += 1			
						newElementFlag = True
			
				if removeElementFlag == True:
					if boola or boolb or boolc:
						del self.xlist[-1]
					else:
						del self.xlist[0]
				
				if newElementFlag == True:
					if boola or boolb or boolc:
						self.xlist.insert(0,self.xlist[0] - newElementWidth - 5)
					else:
						self.xlist.append(self.xlist[-1] + newElementWidth + 5)
					
				y=10
				for i in range(0,len(self.xlist)):
					ctx.save()
					ctx.translate(self.xlist[i], y)
					self.queueImage[i] = ctx.set_source_pixbuf(self.queuePixBuf[i], 0, 0) 
					if self.queueImage[i] != None:
						self.queueImage[i].set_matrix(self.queueMatrix[i]) 
					ctx.paint()
					ctx.restore()
	
	def on_draw_shape (self, ctx):
		self.on_draw(ctx)
	
# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":
	# create new session
	import screenlets.session
	screenlets.session.create_session(MovieTickrScreenlet)

