import time
import json
from pathlib import Path
from snowballstemmer import stemmer
import nltk
from nltk.corpus import stopwords
stopwords.words('english')


FILENAME = Path(r'index_info\tfidf_index.txt') #file to check for now
DOC_FILE = Path(r'index_info\docid_list.txt') #file for doc ids
INDEXED_INDEX = json.load(open(Path(r'index_info\indexed_tfidf.json')))
INDEXED_DOCID = json.load(open(Path(r'index_info\indexed_docid.json')))



def get_query_info3(query_list):
    acquired = []

    for query in query_list:
        f = open(FILENAME)
        try:
            f.seek(INDEXED_INDEX[query[0:4]])
            for line in f:
                #print(line.split('->')[0])
                if line.split('->')[0] == query:
                    acquired.append(eval(line.split('->')[1][:-1]))
                    break
                elif line.split('->')[0][0:4] != query[0:4]:
                    break
        except:
            pass
    return acquired
            

def compare_two3(qinfo1, qinfo2):
    new_qinfo = []
    qinfo2 = dict(qinfo2)
    for i in qinfo1:
        try:
            new_qinfo.append((i[0], i[1] + qinfo2[i[0]]))
            #i[1] += qinfo2[i[0]]
        except:
            pass
    return new_qinfo



def and_get_results3(query_info):
    if len(query_info) == 1:
        return query_info[0]
    qinfo1 = sorted(query_info[0], key = lambda x: x[1], reverse = True)
    for i in range(len(query_info) - 1):
        qinfo2 = query_info[i+1]
        qinfo1 = compare_two3(qinfo1, qinfo2)
    qinfo1 = sorted(qinfo1, key = lambda x: x[1], reverse = True)
    return qinfo1

def id_list_to_url(id_list, numlinks=10):
    links_shown = 0
    choice = ''
    while True:
        for docid in id_list:
            with open(DOC_FILE) as r:
                r.seek(INDEXED_DOCID[str((docid[0]//100) * 100)])
                for line in r:
                    if int(line.split('->')[0]) == docid[0]:
                        if '#' in line: break
                        print(line.split('->')[1])
                        links_shown += 1
                        if links_shown == 10:
                            links_shown = 0
                            choice = input("press enter to show next 10, enter 'q' to quit\n")
                            print()
                        break
            if choice == 'q':
                return
        print("End of search results")
        break


if __name__ == "__main__":
    stem = stemmer('english')
    query_list = list(set(input("Enter query to search: ").split()))
    query_list_ns = [query for query in query_list if query not in stopwords.words('english')]
    query_list = (query_list_ns if (len(query_list) - len(query_list_ns)) / len(query_list) <= .5 else query_list)
    start = time.time()
    query_list = [stem.stemWord(query.lower()) for query in query_list]
    query_info = get_query_info3(query_list)
    if len(query_info) == 0:
        print("no results found")
    else:
        
        results = and_get_results3(query_info)
        end = time.time()
        print("Results acquired in", round(end-start, 3), "seconds\n")
        if len(results) == 0:
            print("no results found")
        else:
            id_list_to_url(results)
    
    
    
