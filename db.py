import psycopg2
from psycopg2.extras import execute_values
import json
from api_scraper import SrealityScraper


class DB:
    """
    A class used to instantiate a DB connection and save messages into a table 'Flats'
    """
    
    def __init__(self, logger = print):
        self.log = logger
        self.connected = False
        try:
            config = open("config.json", "r")   # load parameters
            self.cfg = json.load(config)
            config.close()
        except json.JSONDecodeError as err:
            self.log("E: Invalid DB config.")
            self.log(err.msg)
            raise err
        except IOError as err:
            self.log("E: DB config does not exist.")
            raise err
        
        self.__connect()

    def __del__(self):
        try:
            self.connected = False
            self.cursor.close()
            self.conn.close()
        except:
            pass
        if self.connected:
            self.log("D: Closed connection with the database.")

    def __connect(self):
        try:    
            self.conn = psycopg2.connect(self.cfg["DB"]["db_connection"])
        except psycopg2.OperationalError as err:
            self.log("E: Unable to connect to the database.")
            self.connected = False
            self.cursor = None
            return
        
        self.log("D: Successfully connected to the database.")
        self.cursor = self.conn.cursor()
        self.connected = True



    def createTables(self):
        self.conn.rollback()
        self.send_command("""CREATE TABLE Flats 
                        (ID SERIAL PRIMARY KEY, 
                        Title text NOT NULL, 
                        Locality text NOT NULL, 
                        Price integer NOT NULL, 
                        ImageURLs text[] NOT NULL
                        )""")
        
    
    
    def dropTables(self):
        self.conn.rollback()
        self.send_command("DROP TABLE Flats")



    def loadScrapedFlats(self, dataTuple):
        self.conn.rollback()
        execute_values(self.cursor, "INSERT INTO Flats(Title, Locality, Price, ImageURLs) VALUES %s", dataTuple)

        self.conn.commit()




    def getItemBetween(self, startItem, endItem):
        getItemsQuery = """SELECT Title, Locality, Price, ImageURLs FROM Flats
                        WHERE ID > {} AND ID < {}
                        """.format(startItem, endItem)
    
        self.conn.rollback()
        return self.send_command(getItemsQuery, True)
    
    
    
    
    def getItemsCount(self):
        itemsCountQuery = "SELECT COUNT(*) FROM Flats"
    
        self.conn.rollback()
        return int(self.send_command(itemsCountQuery, True)[0][0])


    
    
    def send_command(self, command, fetchAll = False):
       
        if not self.connected:
            self.log("D: send_command: Not connected, trying to reconnect")
            self.__connect()
        
        if not self.connected:
            self.log("D: send_command: Reconnecting failed")
            return 

        try:
            self.cursor.execute(command)
            self.conn.commit()
            
            if fetchAll:
                return self.cursor.fetchall()
            
        except psycopg2.IntegrityError as err:
            self.connected = False
            self.log("E: Integrity error: {0}.".format(str(err)))
            
        except Exception as err:
            self.log("E: {0}.".format(str(err)))
            
        return 



def listToSQL(lst):
    return str(lst).replace('[', '{').replace(']', '}').replace('\'', '\"')



if __name__ == '__main__':       # tests
    """
    Scrapes and loads 500 items into database
    """
    
    db = DB()
    print("DB class created")
    
    print("Dropping tables")
    db.dropTables()

    print("Recreating tables")
    db.createTables()
    
    
    print("Starting scraping:\n")
    itemsToScrap = 500
    
    scraper = SrealityScraper()
    flatList = scraper.startScraping(maxItems=itemsToScrap)
    
    print("Scraped items:", len(flatList))
    assert len(flatList) == itemsToScrap
    
    tupleFlatList = tuple(flatList)
    tupleFlatList = tuple(map(lambda x:(x["name"], x["locality"], x["price"], listToSQL(x["images"])), tupleFlatList))    # convert image URL list to SQL format

    db.loadScrapedFlats(tupleFlatList)      # save to DB

    
    print("Scraped items:", len(tupleFlatList))
    print("\nDone")
   