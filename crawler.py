#!/usr/bin/python
import urlparse, urllib2
import re, time
#beautiful soup is needed. it is a html parser
from bs4 import BeautifulSoup

class Crawler:
    def __init__(self, start, restricted=0):
        self.pagesVisited=[]
        self.domainsVisited=[]
        self.fringe=[start]
        self.robots={}
        self.restricted=restricted
        self.crawlDelay={}
        self.pageCnt=0
        self.totUrlList=[]
#below parses the robots.txt file if found. Otherwise it defaults to 5 second delay
    def parseRobots(self, curPage):
        parsedUrl=urlparse.urlparse(curPage)
        robots=parsedUrl.scheme + "://"+ parsedUrl.netloc +"/robots.txt"
        try:
            robots=urllib2.urlopen(robots).read()
            robots=re.sub(r"""(?m)#.*\n?""",'',robots).split("\n")
            disallow=[]
            crawlDelay=5
        except urllib2.HTTPError as e:
            robots=""
        if "User-agent: *" in robots:
            uaLineIndex=robots.index("User-agent: *")
            robots=robots[uaLineIndex:]
            blankIndex=robots.index("")
            robots=robots[:blankIndex]
            for line in robots:
                temp=line.split(": ")
                if len(temp)>1:
                    if temp[0]=="Crawl-delay":
                        crawlDelay=max(crawlDelay,int(temp[1]))
                    if temp[0]=="Disallow":
                        disallow.append(parsedUrl.netloc+temp[1])
            self.crawlDelay[parsedUrl.netloc]=crawlDelay
            self.robots[parsedUrl.netloc]=disallow[:]
            return
        else:
            self.crawlDelay[parsedUrl.netloc]=5
            self.robots[parsedUrl.netloc]=[]
            return
#below parses webpages. If version a is passed, then cs.umass.edu must be in url
    def parseWebPages(self,curPage,version):
        try:
            response=urllib2.urlopen(curPage).read()
        except urllib2.HTTPError as e:
            return []
        soup=BeautifulSoup(response)
        urlList=[]
        for link in soup.find_all('a'):
            if type(link.get("href"))==str:
                temp, temp2=urlparse.urldefrag(urlparse.urljoin(curPage,link.get('href')))
                try:
                    opened=urllib2.urlopen(temp)
                except:
                    continue
                cont_type=opened.info().get('Content-Type')
                if "application/pdf" in cont_type or "text/html" in cont_type:
                    if temp not in self.totUrlList:
                        if temp not in urlList:
                            if version=="a":
                                if "cs.umass.edu" in temp:
                                    urlList=urlList+[temp]
                            else:
                                urlList=urlList+[temp]
        return urlList[:]
#crawlerthread makes sure that robots is followed and crawls
#can set crawl limit and version
    def crawlerThread(self,limit,version):
        flag=True
        while len(self.fringe)>0 and len(self.totUrlList)<limit:
            flag=True
            url=self.fringe.pop(0)
            parsedUrl=urlparse.urlparse(url)
            if parsedUrl.netloc not in self.domainsVisited:
                self.domainsVisited.append(parsedUrl.netloc)
                self.parseRobots(url)
            robotList=self.robots.get(parsedUrl.netloc)
            delay=self.crawlDelay.get(parsedUrl.netloc)
            for link in robotList:
                if link in url:
                    flag=False
            if flag==True:
                self.pageCnt+=1
                if url not in self.pagesVisited:
                    self.pagesVisited.append(url)
                time.sleep(delay)
                newList=self.parseWebPages(url,version)
                self.totUrlList=self.totUrlList+newList
                self.fringe=self.fringe+newList
                print "PAGES DOWNLOADED: "+ str(len(self.pagesVisited))+" URL TOTAL: "+str(len(self.totUrlList))
        if version=="a":
            self.makeTxtFile()
        return

    def makeTxtFile(self):
        f=open("urls.txt","w")
        for i in range(min(100,len(self.totUrlList))):
            f.write(self.totUrlList[i]+"\n")
        return f.close()

def main():
    test=Crawler("https://ciir.cs.umass.edu/")
    test.crawlerThread(100,"a")
    print "next"
    test2=Crawler("https://ciir.cs.umass.edu/")
    test2.crawlerThread(1000,"b")

if __name__ == "__main__":
    main()
