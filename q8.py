# Q8
import sys
import sqlite3

# global variables
prefix = {}
predicate = {}

sameObject = False
currentPredicate = ""

# prefix handle
def acquirePrefix(lineToken):
    # acquire prefix in RDF file, save into prefix dictionary
    # eg: @prefix dbr:    <http://dbpedia.org/resource/> .	
    # key: dbr
    # value: http://dbpedia.org/resource/
    if (lineToken[0] == "@prefix"):
        type = lineToken[1].replace(":","")
        url = processURLTag(lineToken[2])
        prefix[type] = url
    
def processURLTag(url):
    # remove "<>" token from url
    return url[url.index("<") + 1 : url.index(">")]

# predicate handle
def processTag(tag):
    tag = tag.split(":")
    return prefix[tag[0]]+tag[1]

#def getPredicate(lineToken):
    
        
# file reading and basic string processing
def inObjectSpaceProcess(line):
    # replace whitespace with "@SPACE" tag in an object
    if ('"' in line):
        startIndex = line.index('"')
        endIndex = line.rindex('"')
        stringToProcess = line[startIndex:endIndex+1].replace(" ","@SPACE")
        line = line[:startIndex]+stringToProcess+line[endIndex+1:]
    
    return line

def recoverInObjectSpace(string):
    # replace back whitespace
    return string.replace("@SPACE"," ")
        

def readRDFFile(rdffile):
    infile = open(rdffile)
    lines = infile.readlines()
    for line in lines:
        line = line.strip()
        line = inObjectSpaceProcess(line)
        lineToken = line.split()
        acquirePrefix(lineToken)
        print(lineToken)
    print(prefix)
    print(processTag('dbr:Don_Iveson'))
    print(len(prefix))





def main():
    # argv check and acquire files
    if len(sys.argv) != 3:
        print("Usage: python3 q8.py <database file> <RDF input file>")
        sys.exit()
    dbfile = sys.argv[1]
    rdffile = sys.argv[2]
    readRDFFile(rdffile)
    
if __name__ == '__main__':
    main()