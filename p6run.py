#!/usr/bin/python
import copy, os, math


'''
Below is the EvalMeasure class
All it needs is the name of the type of run
Stores qrels info as a dictionary with queryId as key and the value is a dictionary mapping docs to relavance Scores
Scores trecrun info as a dictionary with the queryId as key pointing to an ordered list of retrieved documents
bDict is a dictionary that returns the number of retrieved docs per query stored as dict
aDict is a dictionary with queryId as key that gives the total number of relavent documents in qrelsDict
relAtNDict, f1AtNDict, and pAtNDict are dictionaries with queryId as key that keeps queryLevel info about different measures
dcgp, idcgpm and ndcgp are all dicaries with queryId as key that are used to calculate ndcgp
'''
class EvalMeasures:
	def __init__(self,trecrun='bm25'):
		self.qrelsDict={}
		self.trecrun={}
		self.perQuery={}
		self.dcgp={}
		self.idcgp={}
		self.ndcgp={}
		self.aveAnswer=0
		self.pAtNDict={}
		self.bDict={}
		self.aDict={}
		self.relAtNDict={}
		self.f1AtNDict={}
		self.avePDict={}
		self.method=trecrun
		self.generateFromTxt(trecrun)

			
		
	def generateFromTxt(self,trecrun):
		# This function reads in the qrels file and parses it to create qrelsDict
		# and then parses the correct trecurn file to create the corresponding dictionaries
		pwd=os.getcwd()
		path=pwd+'/p6-data/qrels'
		trpath=pwd+'/p6-data/'+trecrun+'.trecrun'
		f=open(path,'r+')
		qrelsDict={}
		trDict={}
		aDict={}
		bDict={}
		for line in f:
			splitLine=line.split()
			queryId,docId,relscore=int(splitLine[0]),splitLine[2],int(splitLine[3])
			if queryId in qrelsDict.keys():
				qrelsDict[queryId][docId]=relscore
				if relscore>0:
					aDict[queryId]+=1.0
			else:
				qrelsDict[queryId]={docId:relscore}
				if relscore>0:
					aDict[queryId]=1.0
				else:
					aDict[queryId]=0.0
		f.close()
		trf=open(trpath,'r+')
		for line in trf:
			splitLine=line.split()
			queryId, docId, rank=int(splitLine[0]), splitLine[2], int(splitLine[3])
			if queryId in trDict.keys():
				trDict[queryId].append(docId)
				bDict[queryId]=rank
			else:
				trDict[queryId]=[docId]
				bDict[queryId]=rank
		trf.close()
		self.trecrun=copy.deepcopy(trDict)
		self.qrelsDict=copy.deepcopy(qrelsDict)
		self.aDict=copy.deepcopy(aDict)
		self.bDict=copy.deepcopy(bDict)
		return


	def dcgpToN(self, n=20):
		#calculates dcgp to the given value
		queryIdList=self.trecrun.keys()
		for queryId in queryIdList:
			docList=self.trecrun[queryId]
			#note that the range goes from 1 instead of 0 so the log function will work
			for i in range(1,n+1):
				#make sure that i is less than or equal to the number of results if not, take last value
				if i<=len(docList):
					if docList[i-1] in self.qrelsDict[queryId].keys():
						if i==1:
							self.dcgp[queryId]=[float(self.qrelsDict[queryId][docList[i-1]])]
						else:
							#last is i-2
							last=self.dcgp[queryId][i-2]
							thisNum=self.qrelsDict[queryId][docList[i-1]]
							#calculate base 2 log of rank
							thisDenom=math.log(i)/math.log(2.0)
							this=float(thisNum)/thisDenom
							self.dcgp[queryId].append(last+this)
					else:
						if i==1:
							self.dcgp[queryId]=[0.0]
						else:
							last=self.dcgp[queryId][i-2]
							thisNum=0.0
							thisDenom=math.log(i)/math.log(2.0)
							this=float(thisNum)/thisDenom
							self.dcgp[queryId].append(last+this)
				else:
					if i==1:
						self.dcgp[queryId]=[0.0]
					else:
						last=self.dcgp[queryId][i-2]
						self.dcgp[queryId].append(last)




	def idcgpToN(self, n=20):
		#calculates idcgp to N
		queryIdList=self.trecrun.keys()
		for queryId in queryIdList:
			docList=self.trecrun[queryId]
			#sorted by decending scores
			decRelScores=sorted(self.qrelsDict[queryId].values(), reverse=True)
			#note that the index starts at 1. Same logic as above, but sorted by highest relavance 
			for i in range(1,n+1):
				if i<=len(docList):				
					if i==1:
						self.idcgp[queryId]=[float(decRelScores[i-1])]
					else:
						last=self.idcgp[queryId][i-2]
						thisNum=float(decRelScores[i-1])
						thisDenom=math.log(i)/math.log(2.0)
						this=float(thisNum)/thisDenom
						self.idcgp[queryId].append(last+this)
				else:
					if i==1:
						self.idcgp[queryId]=[0.0]
					else:
						last=self.idcgp[queryId][i-2]
						thisNum=0.0
						thisDenom=math.log(i)/math.log(2.0)
						this=float(thisNum)/thisDenom
						self.idcgp[queryId].append(last+this)

	def ndcgpToN(self,n=20):
		#calculates the ratio between dcgp and idcgp for a query
		self.dcgpToN(n=n)
		self.idcgpToN(n=n)
		queryIdList=self.trecrun.keys()
		for queryId in queryIdList:
			for i in range(n):
				if i==0:
					self.ndcgp[queryId]=[self.dcgp[queryId][0]/self.idcgp[queryId][0]]
				else:
					self.ndcgp[queryId].append(self.dcgp[queryId][i]/self.idcgp[queryId][i])
			self.perQuery[queryId]=self.ndcgp[queryId][n-1]
		#below stores the average answer accross all queries in self.aveAnswer
		self.aveAnswer=sum(self.perQuery.values())/len(self.perQuery.keys())

	def pAtN(self,n=5):
		#calculate percision at doc n. Query id's returned from trecrun list
		queryIdList=self.trecrun.keys()
		totRel=0.0
		for queryId in queryIdList:
			#look up retrieved documents
			docList=self.trecrun[queryId]
			for i in range(1,n+1):
				#make sure i doesnt cause index errors
				if i<=len(docList):
					if docList[i-1] in self.qrelsDict[queryId].keys():
						relScore=self.qrelsDict[queryId][docList[i-1]]
					else:
						relScore=0.0
				else:
					relScore=0.0
				#anything above 0 set to 1
				if relScore>0:
					totRel+=1.0
				if queryId in self.pAtNDict.keys():
					#calculate precision at each index
					self.pAtNDict[queryId].append(totRel/i)
				else:
					self.pAtNDict[queryId]=[totRel/i]
			#store each queries final value
			self.perQuery[queryId]=self.pAtNDict[queryId][n-1]
			totRel=0.0
		#average answer below
		self.aveAnswer=sum(self.perQuery.values())/len(self.perQuery.keys())

	def relAtN(self,n=10):
		#very similar to above, except using recall
		queryIdList=self.trecrun.keys()
		totRel=0.0
		for queryId in queryIdList:
			docList=self.trecrun[queryId]
			for i in range(1, n+1):
				if i<=len(docList):
					if docList[i-1] in self.qrelsDict[queryId].keys():
						relScore=self.qrelsDict[queryId][docList[i-1]]
					else:
						relScore=0.0
				else:
					relScore=0.0
				if relScore>0:
					totRel+=1.0
				if queryId in self.relAtNDict.keys():
					#Divide by the number of relevant docs
					self.relAtNDict[queryId].append(totRel/self.aDict[queryId])
				else:
					self.relAtNDict[queryId]=[totRel/self.aDict[queryId]]
			self.perQuery[queryId]=self.relAtNDict[queryId][n-1]
			totRel=0.0
		self.aveAnswer=sum(self.perQuery.values())/len(self.perQuery.keys())

	def f1Atn(self,n=10):
		#use relAtN and pAtN to calculate f1Atn
		self.relAtN(n=n)
		self.pAtN(n=n)
		queryIdList=self.trecrun.keys()
		for queryId in queryIdList:
			for i in range(n):
				num=2.0*self.relAtNDict[queryId][i]*self.pAtNDict[queryId][i]
				denom=self.relAtNDict[queryId][i]+self.pAtNDict[queryId][i]
				if denom==0:
					denom=1
				if queryId in self.f1AtNDict.keys():
					self.f1AtNDict[queryId].append(num/denom)
				else:
					self.f1AtNDict[queryId]=[num/denom]
			self.perQuery[queryId]=self.f1AtNDict[queryId][n-1]
		self.aveAnswer=sum(self.perQuery.values())/len(self.perQuery.keys())

	def aveP(self):
		#add list keeps trak of ratio's when a relavant doc is found
		queryIdList=self.trecrun.keys()
		totRel=0
		addList=[]
		for queryId in queryIdList:
			docList=self.trecrun[queryId]
			n=len(docList)
			for i in range(1,n+1):
				if i<=len(docList):
					if docList[i-1] in self.qrelsDict[queryId].keys():
						relScore=self.qrelsDict[queryId][docList[i-1]]
					else:
						relScore=0.0
				else:
					relScore=0.0
				if relScore>0:
					totRel+=1.0
					addList.append(totRel/i)
				if queryId in self.avePDict.keys():
					self.avePDict[queryId].append(sum(addList)/max(len(addList),1))
				else:
					self.avePDict[queryId]=[sum(addList)/max(len(addList),1)]
			num=sum(addList)
			#divide by total number of relevant docs per the books instructions
			denom=self.aDict[queryId]
			self.perQuery[queryId]=(num/denom)
			totRel=0.0
			addList=[]
		self.aveAnswer=sum(self.perQuery.values())/len(self.perQuery.keys())


if __name__=="__main__":
	trecrunList=['bm25','sdm','ql','stress']
	outF=open('output.metric','w+')
	for run in trecrunList:
		evalTest=EvalMeasures(run)
		evalTest.ndcgpToN(n=20)
		outF.write(run+'.trecrun NDCG@20 '+str(evalTest.aveAnswer)+'\n')
		evalTest.pAtN(n=5)
		outF.write(run+'.trecrun P@5 '+str(evalTest.aveAnswer)+'\n')
		evalTest.pAtN(n=10)
		outF.write(run+'.trecrun P@10 '+str(evalTest.aveAnswer)+'\n')
		evalTest.relAtN(n=10)
		outF.write(run+'.trecrun Recall@10 '+str(evalTest.aveAnswer)+'\n')
		evalTest.f1Atn(n=10)
		outF.write(run+'.trecrun F1@10 '+str(evalTest.aveAnswer)+'\n')
		evalTest.aveP()
		outF.write(run+'.trecrun AP '+str(evalTest.aveAnswer)+'\n')
	outF.close()
	#below creates plot info for query 450
	plotF=open('plot450.csv','w+')
	query450run=['ql','sdm','bm25']
	plotF.write('run,r,p'+"\n")
	for run in query450run:
		evalTest=EvalMeasures(run)
		n=len(evalTest.trecrun[450])
		evalTest.pAtN(n=n)
		evalTest.relAtN(n=n)
		for i in range(n):
			plotF.write(run+","+str(evalTest.relAtNDict[450][i])+","+str(evalTest.pAtNDict[450][i])+"\n")
	plotF.close
	#below creates ttest data
	tfile=open('ttest.csv','w+')
	tfile.write("query,qlAvep,sdmAvep\n")
	qlrun=EvalMeasures('ql')
	sdmrun=EvalMeasures('sdm')
	qlrun.aveP()
	sdmrun.aveP()	
	queryList=sorted(qlrun.trecrun.keys())
	for query in queryList:
		tfile.write(str(query)+","+str(qlrun.perQuery[query])+","+str(sdmrun.perQuery[query])+"\n")
	tfile.close()
			



