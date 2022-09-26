import requests
import time



class SrealityScraper:
        
    def __init__(self, logger=print):
        self.log = logger

    
    @staticmethod
    def getImagesFromJSON(JSONobj) -> list[str]:
        imgList = []
        maxImages = 5
        
        #for i in range(maxImages):
        #    imgURL = str(JSONobj["_links"]["images"][i]["href"])
        #    imgList.append(imgURL)
                
                
        for img in JSONobj["_links"]["images"]:
            imgList.append(str(img["href"]))
            
        return imgList
        

    @staticmethod 
    def parseJSON(JSONobj):
        flatList = []
        flats = JSONobj["_embedded"]["estates"]

        for flat in flats:
            tmpFlat = {"name" : flat["name"],
                    "locality" : flat["locality"],
                    "price" : flat["price"],
                    "images" : SrealityScraper.getImagesFromJSON(flat)}
            
            flatList.append(tmpFlat)
            
        return flatList



    def startScraping(self, maxItems=130):
        """
        Outputs a list of scraped items, each item is a dict
        """
        
        itemPerPage = 60
        reqPages = maxItems // itemPerPage + 1
        flatList = []
        
        self.log(f"Scraping total of {reqPages} pages")
        
        headers = {
                    'Content-Type' : 'application/json',
                    'accept-encoding': 'gzip, deflate, br',
                    'accept-language': 'en-US,en;q=0.9',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/536.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/536.36',
                    'accept': 'application/json,text/plain,*/*',
                    'authority': 'www.sreality.cz',
                    'referer': 'https://www.sreality.cz/hledani/prodej/byty',
                    }

        api_url = "https://www.sreality.cz/api/cs/v2/estates?category_main_cb=1&category_type_cb=1&per_page=" + str(itemPerPage)
        
        for i in range(reqPages):
            if i == 0:
                fullURL = api_url                                   # first page
            else:
                fullURL = api_url + "&page=" + str(i+1)             # i+1 page, enumeration begins with 1

            try:
                response = requests.get(fullURL, headers=headers)
                tmpFlatList = SrealityScraper.parseJSON(response.json())
                
                flatList.extend(tmpFlatList)
                time.sleep(1.0)                                     # to avoid getting banned, maybe
                
            except Exception as e:
                self.log(f"exception: {e}, page {i+1}")
                break                                               # all pages scraped / error

        return flatList[:maxItems]                                  # don't need more than maxItems
            
            
            
            
        
        
if __name__ == '__main__':       # tests
    print("Scraping test:\n")
    
    scraper = SrealityScraper()
    flatList = scraper.startScraping(maxItems=130)
    
    assert len(flatList) == 130
    
    print("Scraped items:", len(flatList))
    print("First item:", flatList[0])
    print("\nDone")
    







