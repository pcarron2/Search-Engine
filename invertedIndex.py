#!/usr/bin/python
import json, pickle, copy, os, sys

class InvertedInd:
	def __init__(self,readFromDisk=1,fileToRead='termDict.p'):
		self.invertedIndex={}
		# If file can be read from disk, load, otherwise read from json
		if readFromDisk==1:
			self.invertedIndex=pickle.load( open( fileToRead, "rb" ) )
		else:
			self.generateFromJson(fileToRead)
		
	def generateFromJson(self,fileToRead):
		# this function reads in the raw json file and creates an inverted
		# index if there is not one already saved on disk.  This function also
		# saves the generated index using the saveWithPickle function and gives it
		# the generic filename 'termDict.p'
		pwd=os.getcwd()
		path=pwd+'/'+fileToRead
		f=open(path,'r+')
		data=json.load(f)
		f.close()
		termDict={}
		for i in range(len(data["corpus"])):
		    sId=str(data["corpus"][i]["sceneId"])
		    sNum=int(data["corpus"][i]["sceneNum"])
		    pId=str(data["corpus"][i]["playId"])
		    #line below makes each term vector by splitting the string at spaces and ignores blank terms
		    termVect=[str(term) for term in data["corpus"][i]["text"].split(" ") if len(term)>0]
		    #the inner for loop populates the sNum:[sId,pId,[position]] dictionary. 
		    for j in range(len(termVect)):
		    	#if the term is not in the dictionary create a new entry
		        if termVect[j] not in termDict.keys():
		            termDict[termVect[j]]={sNum:[sId,pId,[j]]}
		        #if the scene number is not in the dictionary returned by the term, create a new posting
		        elif sNum not in termDict[termVect[j]].keys():
		            termDict[termVect[j]][sNum]=[sId,pId,[j]]
		        #if the term exisits in termDict, and the scene num exists in the posting, append position to the position vector
		        else:
		            termDict[termVect[j]][sNum][2].append(j)
		#save the new index to disk so this doesnt have to be rerun each time
		self.invertedIndex=copy.deepcopy(termDict)
		self.saveWithPickle('termDict.p')
		return
	def saveWithPickle(self,newName):
		# Saves inverted index to disk
		#pwd=os.getcwd()
		#path=pwd+'/'+newName
		pickle.dump(self.invertedIndex,open(newName, "wb" ))
		return

	def queryProcess(self,scene0Play1,phrase,compareType="",phrase2=[""]):
		# this processes the queries for this assignment. It's pretty clunky
		# generally I would rather support a query language than write a new one.
		# the function requires that the user specify the type of query to be done.
		# a set is returned usually. Sometimes a dictionary is returned if more info is needed
		# to answer a question.
		if compareType=="orContain":
			wordDict={}
			resultSet=set([])
			for word in phrase:
				wordDict[word]=self.containingWord(word,scene0Play1)
			resultSet=reduce(set.union,[set(results)for results in wordDict.values()])
			return sorted(list(resultSet))
		elif compareType=="andContain":
			wordDict={}
			resultSet=set([])
			for word in phrase:
				wordDict[word]=self.containingWord(word,scene0Play1)
			resultSet=reduce(set.intersection,[set(results)for results in wordDict.values()])
			return sorted(list(resultSet))
		elif compareType=="a>b":
			resultSet=set([])
			w1Dict=self.scenePlayCount(scene0Play1,phrase[0])
			w2Dict=self.scenePlayCount(scene0Play1,phrase2[0])
			wDictList=[w1Dict,w2Dict]
			keysToCheck=reduce(set.intersection,[set(results for results in i.keys()) for i in wDictList])
			for key in keysToCheck:
				if w1Dict[key]>w2Dict[key]:
					resultSet.update([key])
			return sorted(list(resultSet))
		elif compareType=="wordsInOrder":
			return sorted(list(self.phraseInOrder(scene0Play1,phrase)))
		elif compareType=="totWordCount":
			return self.totalWordCount(scene0Play1)
		return

	def compoundQuery(self,SId=1,scene0Play1=0,phrase=[""],compareType="",writeToFile=1):
		# can be expanded next week for p5, wanted to modify to get compoud
		# queries processed and data output for plot in report writeup
		# the query function above returns sets as answers. This function can return
		# scene or play names or the scene id number. I also included code to write to disk for the report.
		if SId==1:
			if compareType=="(a or b)>c":
				aDict=self.sceneIDCount(phrase[0])
				bDict=self.sceneIDCount(phrase[1])
				mergedDict={x: max(i for i in (aDict.get(x), bDict.get(x)) if i) for x in aDict.viewkeys() | bDict}
				cDict=self.sceneIDCount(phrase[2])
				if writeToFile==1:
					abfn="maxTheeThou.txt"
					cfn="youquery.txt"
					abf=open(abfn,"w+")
					cf=open(cfn,"w+")
					for key in sorted(cDict.keys()):
						cf.write(str(key)+","+str(cDict[key])+"\n")
					for key in sorted(mergedDict.keys()):
						abf.write(str(key)+","+str(mergedDict[key])+"\n")
					abf.close()
					cf.close()
		return




	def phraseInOrder(self,scene0Play1,phrase):
		# This helper function is used to preform queries on phrases with multiple words
		# The position vectors from each term are retrieved. A vector the length of the phrase is created
		# and populated initially with 0. Each instance of the first word is checked
		# If the next word is one position higher than the previous word, the vector is populated with 1
		# If the minimum number in the final vector is 1, then all words are found in sequence and the scene or play is
		# added to the result set.
	    wordDict={}
	    resultSet=set([])
	    for word in phrase:
	        wordDict[word]=self.containingWord(word,scene0Play1)
	    #only look at scenes where all terms are used
	    keySet=reduce(set.intersection,[set(results)for results in wordDict.values()])
	    queryList=[self.scenePosition(word) for word in phrase]
	    for key in keySet:
	        tempHold=[queryList[i][key] for i in range(len(phrase))]
	        resultList=[0]*len(phrase)
	        for num in tempHold[0]:
	            for j in range(len(phrase)):
	                if num+j in tempHold[j]:
	                    resultList[j]=1
	        if min(resultList)==1:
	            resultSet.update([key])
	    return resultSet



	def containingWord(self,word,scene0Play1):
		#helper function returns scenes or play where a word occurs
		resultSet=set([])
		wordDict=self.invertedIndex[word]
		for key in wordDict.keys():
			resultSet.update([wordDict[key][scene0Play1]])
		return copy.deepcopy(resultSet)

	def scenePlayCount(self,scene0Play1,phrase):
		#helper function returns a dictionary with scene or play as key and counts of a given word as value
		queryDict={}
		queryKeySet=set([])
		phraseDict=self.invertedIndex[phrase]
		for key in phraseDict.keys():
			if phraseDict[key][scene0Play1] not in queryKeySet:
				queryDict[phraseDict[key][scene0Play1]]=len(phraseDict[key][2])
			else:
				queryDict[phraseDict[key][scene0Play1]]+=len(phraseDict[key][2])
			queryKeySet.update([phraseDict[key][scene0Play1]])
		return copy.deepcopy(queryDict)

	def sceneIDCount(self,phrase):
		# helper function returns same as scenePlayCount but with scene number as key
		queryDict={}
		queryKeySet=set([])
		phraseDict=self.invertedIndex[phrase]
		for key in phraseDict.keys():
			if key not in queryKeySet:
				queryDict[key]=len(phraseDict[key][2])
			else:
				queryDict[key]+=len(phraseDict[key][2])
			queryKeySet.update([key])
		return copy.deepcopy(queryDict)

	def scenePosition(self,phrase):
		# returns a dictionary with each scene as key and position vector as value
		queryDict={}
		queryKeySet=set([])
		phraseDict=self.invertedIndex[phrase]
		for key in phraseDict.keys():
			if phraseDict[key][0] not in queryKeySet:
				queryDict[phraseDict[key][0]]=phraseDict[key][2]
			queryKeySet.update([phraseDict[key][0]])
		return copy.deepcopy(queryDict)

	def totalWordCount(self,scene0Play1):
		# helper query function to return the total word count of either a scene or play
		# used to create document stats to answer questions about min/max/average length
		keyList=self.invertedIndex.keys()
		countDict={}
		visitedSet=set([])
		for key in keyList:
			postDict=self.invertedIndex[key]
			for docId in postDict.keys():
				if postDict[docId][scene0Play1] not in visitedSet:
					countDict[postDict[docId][scene0Play1]]=len(postDict[docId][2])
				else:
					countDict[postDict[docId][scene0Play1]]+=len(postDict[docId][2])
				visitedSet.update([postDict[docId][scene0Play1]])
		resultDictSorted=sorted(countDict,key=countDict.get,reverse=True)
		fn="totplaycount.txt"
		if scene0Play1==0:
			fn="totscenecount.txt"
		f=open(fn,"w+")
		for word in resultDictSorted:
			f.write(word+" : " + str(countDict[word])+ "\n")
		f.close()
		return copy.deepcopy(countDict)



if __name__=="__main__":
	# Code assumes that index exists on disk with filename 'termDict.p' in same directory as being run
	# If this is not true, 2 lines below can be uncommented and line below should be commented
	if len(sys.argv) != 2:
		print "Please enter 0 for build from json or 1 to build from pickle file"
		sys.exit(0)
	elif sys.argv[1] not in set(["0","1"]):
		print "Please enter 0 or 1. Be sure json file or pickle file exists in directory"
		sys.exit(0)
	elif sys.argv[1]=="0":
		invTest=InvertedInd(readFromDisk=0,fileToRead='shakespeare-scenes.json')
	elif sys.argv[1]=="1":
		invTest=InvertedInd()
	t0_0=invTest.queryProcess(scene0Play1=0,phrase=["thee"],phrase2=["you"],compareType="a>b")
	t0_1=invTest.queryProcess(scene0Play1=0,phrase=["thou"],phrase2=["you"],compareType="a>b")
	t0=sorted(list(set(t0_0+t0_1)))
	t1=invTest.queryProcess(scene0Play1=0,phrase=["verona","rome","italy"],compareType="orContain")
	t2=invTest.queryProcess(scene0Play1=1,phrase=["falstaff"],compareType="orContain")
	t3=invTest.queryProcess(scene0Play1=1,phrase=["soldier"],compareType="orContain")
	p0=invTest.queryProcess(scene0Play1=0,phrase=["lady","macbeth"],compareType="wordsInOrder")
	p1=invTest.queryProcess(scene0Play1=0,phrase=["a","rose","by","any","other","name"],compareType="wordsInOrder")
	p2=invTest.queryProcess(scene0Play1=0,phrase=["cry","havoc"],compareType="wordsInOrder")
	tpc=invTest.queryProcess(scene0Play1=1,phrase="",compareType="totWordCount")
	tsc=invTest.queryProcess(scene0Play1=0,phrase="",compareType="totWordCount")
	print "average scene length: "+str((float(sum(tsc.values()))/len(tsc.values())))
	cq=invTest.compoundQuery(scene0Play1=0,phrase=["thee","thou","you"],compareType="(a or b)>c",writeToFile=1)
	data=[t0,t1,t2,t3,p0,p1,p2]
	termList=["terms"+str(i)+".txt" for i in range(4)]
	phraseList=["phrase"+str(i)+".txt" for i in range(3)]
	allList=termList+phraseList
	for i in range(len(allList)):
		fn=open(allList[i],"w+")
		for item in data[i]:
			fn.write(str(item)+"\n")
		fn.close()


