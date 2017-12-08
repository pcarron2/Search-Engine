#!/usr/bin/python
import copy, sys, os

def generateUrlList(path):
	f=open(path,'r+')
	urlSet=set()
	for line in f:
		url, outLink=line.strip().split("\t")
		urlSet.add(url)
		urlSet.add(outLink)
	f.close()
	return sorted(list(urlSet))[:]

def generateLinkDict(urlList, path):
	f=open(path,'r+')
	urlSet=set(urlList)
	linkDict={a:set() for a in urlList}
	for line in f:
		url, outLink=line.strip().split("\t")
		if outLink in urlSet:
			linkDict[url].add(outLink)
	f.close()
	return copy.deepcopy(linkDict)

def generateInlinkRank(urlList, linkDict):
	ilcDict={word:0 for word in urlList}
	for url in urlList:
		for outLink in linkDict[url]:
			ilcDict[outLink]+=1
	sortedByInLinks=sorted(ilcDict,key=ilcDict.get,reverse=True)
	return sortedByInLinks[:], copy.deepcopy(ilcDict)

def pageRank(linkDict,urlList , tau, lam):
    T=0
    prDict={word:(1.0/len(urlList)) for word in urlList}
    r={word:float(0) for word in urlList}
    rpDict={word:(1.0/len(urlList)) for word in urlList}
    D=float(len(urlList))
    while True:
        convFact=0.0
        T=0
        r={word:0 for word in urlList}
        for url in urlList:
            if len(linkDict[url])>0:
                for dest in linkDict[url]:
                    r[dest]+=(prDict[url]/len(linkDict[url]))
            else:
                T+=prDict[url]
        for url in urlList:
            rpDict[url]=(lam/D)+((1-lam)*r[url])
        for url in urlList:
            rpDict[url]=rpDict[url]+((1.0-lam)*(T/D))
            convFact+=abs(rpDict[url]-prDict[url])
        if convFact<tau:
            return copy.deepcopy(rpDict)
        else:
            print convFact
            prDict=copy.deepcopy(rpDict)

if __name__=="__main__":
	if len(sys.argv)!=3:
		print("Please enter values for tau followed by lambda")
		sys.exit(0)
	tau=float(sys.argv[1])
	lam=float(sys.argv[2])
	if tau>1 or tau<0 or lam>1 or lam<0 or type(tau)!=float or type(lam)!= float:
		print "Please enter float values for lam and tou between 0 and 1"
	pwd=os.getcwd()
	pathToInputFile=pwd+"/links.srt"
	try:
		f=open(pathToInputFile,'r')
	except:
		print "could not find input file in path"
		sys.exit(0)
	f.close()
	pathToInlinksFile=pwd+"/inlinks.txt"
	pathToPageRankFile=pwd+"/pagerank.txt"
	urlList=generateUrlList(pathToInputFile)
	linkDict=generateLinkDict(urlList,pathToInputFile)
	inLinkTop50, ilcDict=generateInlinkRank(urlList,linkDict)
	ilc=open(pathToInlinksFile,'w+')
	for i in range(50):
		ilc.write("Page: "+inLinkTop50[i]+" Rank: "+str(i+1)+" Inlink Count: "+str(ilcDict[inLinkTop50[i]])+"\n")
	ilc.close()
	prDict=pageRank(linkDict,urlList,tau,lam)
	sortByPageRank=sorted(prDict,key=prDict.get,reverse=True)
	prf=open(pathToPageRankFile,'w+')
	for i in range(50):
		prf.write("Page: "+sortByPageRank[i]+" Rank: "+ str(i+1)+ " Pagerank Value: "+str(prDict[sortByPageRank[i]])+ "\n")
	prf.close()
	sys.exit(0)
