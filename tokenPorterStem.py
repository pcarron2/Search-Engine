#!/usr/bin/python
import sys, os, re

def tokenize(a):
    upper="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    lower="abcdefghijklmnopqrstuvwxyz"
    alphDict={upper[x]:lower[x] for x in range(len(upper))}
    sepString=list("`~!@#$%^&*)(_-+=-][:;,<>?/|\"\' \n\r")
    sepString.append('/')
    word=""
    wordList=[]
    for num in range(len(a)):
        if a[num]=='.':
            continue
        if a[num] in sepString:
            if len(word)>0:
                wordList.append(word)
            word=""
            continue
        if a[num] in upper:
            a[num]=alphDict[a[num]]
        word=word+a[num]
    if len(word)>0:
        wordList.append(word)
    return wordList[:]

def stopWords(stopList,word):
    if word not in stopList:
        return word
    return ""

def portStem(word):
    word=portStem1a(word)
    word=portStem1b(word)
    return word

def portStem1a(word):
    if re.match(r'^([a-z]*)(sses)$',word)!=None:
        word=re.sub(r'^([a-z]*)(sses)$',r'\1ss',word)
    elif re.match(r'^([a-z]*)([aeiou][a-z]*[^s])s$',word)!=None:
        word=re.sub(r'^([a-z]*)([aeiou][a-z]*[^s])s$',r'\1\2',word)
    elif re.match(r'^([a-z]{2,})(ies|ied)$',word)!=None:
        if re.match(r'^([a-z])(ies|ied)$',word)!=None:
            word=re.sub(r'^([a-z])(ies|ied)$',r'\1ie',word)
        else:
            word=re.sub(r'^([a-z]{2,})(ies|ied)$',r'\1i',word)
    elif re.match(r'^([a-z])(ies|ied)$',word)!=None:
        word=re.sub(r'^([a-z])(ies|ied)$',r'\1ie',word)
    elif re.match(r'^([a-z]*)(ss|us)$',word)==None:
        word=word
    return word

def portStem1b(word):
    word2=word
    if re.match(r'^([a-z]*)(eed|eedly)$',word)!=None:
        match=re.match(r'^([a-z]*)(eed|eedly)$',word)
        if re.match(r'([aeiou][^aeiou])',match.group(1)) != None:
            word2=re.sub(r'^([a-z]*)(eed|eedly)$',r'\1ee',word)
        else:
            word2=word
    elif re.match(r'^([a-z]*)(ed|edly|ing|ingly)$',word)!=None:
        match=re.match(r'^([a-z]*)(ed|edly|ing|ingly)$',word)
        if re.match(r'^[^aeiou]*([aeiou])[a-z]*$',match.group(1))!=None:
            word2=re.sub(r'^([a-z]*)(ed|edly|ing|ingly)$',r'\1',word)
            if re.match(r'^([a-z]*)(at|bl|iz)$',word2)!=None:
                word2=word2+"e"
            elif re.match(r'^([a-z]*)([a-km-rt-x])\2$',word2)!=None:
                word2=re.sub(r'^([a-z]*)([a-km-rt-x])\2$',r'\1\2',word2)
            elif len(word2)<=3:
                word2=word2+"e"
    return word2

if __name__=="__main__":
    if len(sys.argv)!=2:
        print("Please eneter a singe argument either a or b")
        sys.exit(0)
    if sys.argv[1] not in ['a','b',"test"]:
        print("Please enter either a or b as an argument")
        sys.exit(0)
    pwd=os.getcwd()
    if sys.argv[1]=="test":
        print portStem("alas")=="ala"
        print portStem("examples")=="example"
        print portStem("pirating")=="pirate"
        print tokenize(list("A.B.C defg HI.J'k"))==['abc','defg','hij','k']
        sys.exit(0)
    if sys.argv[1]=='a':
        pathToInputFile=pwd+"/input.txt"
        pathToOutputFile=pwd+"/tokenized.txt"
    else:
        pathToInputFile=pwd+"/p2-input-part-B.txt"
        pathToOutputFile=pwd+"/terms.txt"
        pathToData=pwd+"/colData.csv"
    try:
        f=open(pathToInputFile,'r')
        o=open(pathToOutputFile,'w+')
    except:
        print("Could not open input or output file. Make sure it is in the same directory")
        sys.exit(0)
    pathToStopWordsFile=pwd+"/inquery"
    try:
        f2=open(pathToStopWordsFile,'r')
        stopList=[]
        for line in f2:
            stopList.append(line.strip('\n'))
        f2.close()
    except:
        print("Could not open stop words file")
        sys.exit(0)
    if sys.argv[1]=='a':
        for line in f:
            a=list(line)
            a=tokenize(a)
            for word in a:
                temp=stopWords(stopList,word)
                if len(temp)>0:
                    temp=portStem(temp)
                    o.write(temp+"\n")
    else:
        d=open(pathToData,'w+')
        d.write("collectionSize,vocabSize\n")
        wordDict={}
        vocabSize=0
        collectionSize=0
        for line in f:
            a=list(line)
            a=tokenize(a)
            for word in a:
                temp=stopWords(stopList,word)
                if len(temp)>0:
                    temp=portStem(temp)
                    if temp in wordDict.keys():
                        wordDict[temp]+=1
                        collectionSize+=1
                    else:
                        wordDict[temp]=1
                        collectionSize+=1
                        vocabSize+=1
                    if collectionSize%300==0:
                        d.write(str(collectionSize)+","+str(vocabSize)+"\n")
        d.write(str(collectionSize)+","+str(vocabSize)+"\n")
        d.close()
        topWords=sorted(wordDict,key=wordDict.get, reverse=True)
        for i in range(200):
            o.write(topWords[i]+": "+str(wordDict[topWords[i]])+"\n")
    f.close()
    o.close()
    sys.exit(0)
