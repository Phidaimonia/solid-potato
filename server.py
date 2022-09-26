import tornado
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
from tornado.ioloop import IOLoop
from tornado.web import Application as TornadoApplication

from db import DB

import json
import logging, tornado.log
import time


test_mode = True  # disables encryption
http_port = 8080
itemsPerPage = 10



def parsePrice(price):
    if price == 1:
        return "Info o ceně u RK"
    else:
        return str(price) + " Kč"
    
    
    

class RedirectHandler(tornado.web.RequestHandler):
    def get(self, page=0):
            self.redirect('/0')
            


class RootHandler(tornado.web.RequestHandler):
    """
    Displays scraped flat ads
    """
    
    def get(self, page):
        # page starts with 0, always positive int or zero
        
        startItem = int(page) * itemsPerPage
        endItem = startItem + itemsPerPage + 1                  
        
        maxItemCount = app.database.getItemsCount()
        lastPage = max(0, (maxItemCount-1) // itemsPerPage)
        
        if int(page) > lastPage:
            self.redirect('/' + str(lastPage))                      # wrong page number -> redirect
            return

        flats = app.database.getItemBetween(startItem, endItem)
        
        previousPageLink = "/" + str(max(0, int(page)-1))           # wont go below zero
        nextPageLink = "/" + str(min(lastPage, int(page)+1))        # wont go beyond the last page                

        dictFlats = tuple(map(lambda x:{"title":x[0], "locality":x[1], "price":parsePrice(x[2]), "imgs":x[3][:3]}, flats))   # convert list to dictionary, only show 3 images
        
        self.render("Static/index.html", items=dictFlats, previousPageLink=previousPageLink, nextPageLink=nextPageLink)               # case sensitive



            

          
         



class WebApp(TornadoApplication):

    def __init__(self, database, cfg):
        self.cfg = cfg
        self.database = database  

        self.tornado_handlers = [
            (r'/', RedirectHandler),
            (r'/([0-9]+)', RootHandler),
            (r'/(-[0-9]+)', RedirectHandler),
            (r'/index\.html', RedirectHandler),
            (r'/CSS/(.*)', tornado.web.StaticFileHandler, {'path': './Static/CSS'}),
            (r'/js/(.*)', tornado.web.StaticFileHandler, {'path': './Static/js'}),
            (r'/images/(.*)', tornado.web.StaticFileHandler, {'path': './Static/images'}) 
        ]
        
        self.tornado_settings = {
            "debug": True,
            "autoreload": True
        }
        
        TornadoApplication.__init__(self, self.tornado_handlers, **self.tornado_settings)








if __name__ == '__main__':
    
    config = open("config.json", "r")                   # load parameters
    cfg = json.load(config)
    config.close()
    
    
    tornado.log.enable_pretty_logging()
    app_log = logging.getLogger("tornado.application")
    app_log.setLevel(logging.DEBUG)
    
    app_log.debug("Waiting for DB to start...")
    time.sleep(10)

    database = None
    app_log.debug("Connecting to DB...")
    
    for i in range(3):  
        try:
            app_log.debug("Connection attempt {}...".format(i+1))
            database = DB(logger = app_log.debug)
            time.sleep(2)  
            
            if database is None: 
                continue
            
            if database.connected == True:
                break
            
        except Exception as err:
            app_log.error("Database connection error: {}".format(err))
            time.sleep(2)     
    
    if database is None:
        app_log.error("Cant connect to DB")
        exit()
        
    if database.connected == False:
        app_log.error("Cant connect to DB")
        exit()
        
        
        
    database.createTables()                 # in case the DB is empty
    if database.getItemsCount() == 0:
        app_log.debug("DB is empty, starting scraping...")
        database.scrapeAndSave(itemsToScrap=500)
        app_log.debug("Scraping done")


    

    app = WebApp(database, cfg)            
    app_log.debug("WebApp instance created")
    

    http_server = tornado.httpserver.HTTPServer(app)    
    http_server.listen(http_port)

    iol = IOLoop.current()
    app_log.info("Webserver: Initialized...")
    iol.start()




