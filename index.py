from collections import defaultdict
from pathlib import Path
import json
import os
import sys
import re
import math
from bs4 import BeautifulSoup
from snowballstemmer import stemmer
import warnings
warnings.filterwarnings("ignore") #ignore warnings for demo purposes

CONSOLE_UPDATES = True #Shows current updates
IMPORTANT_TAGS = ['b', 'strong', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'title']
IMPORTANT_WEIGHT = 2
FOLDER = os.getcwd()
NUM_FILE_SPLIT = 20000 #100,000 makes it all into one file, 10,000 would split it into 6 files
                        #since there are 53,000ish files.

class doc:
    #class to keep track of frequency and importance of docIDs
    def __init__(self, docID, important=False):
        self.id = docID
        self.freq = 0
        self.important_freq = 0
        if important:
            self.important_freq += 1
        else:
            self.freq += 1

    def __str__(self):
        return f"({self.id}, {self.freq}, {self.important_freq})"

    def __repr__(self):
        return f"({self.id}, {self.freq}, {self.important_freq})"

    def increment_freq(self, num=1, important=False): #defaults to 1
        if important:
            self.important_freq += num
        else:
            self.freq += num


def tokenize(content, ignore_stopwords=False):
    #takes in a string containing all the content of the page and returns list of tokens that are 3 letters or more
    token_list = []
    word = ""
    for letter in content:
        if re.match('^[a-zA-Z0-9]+$',letter):
            word += letter
        elif word != "":
            if len(word) > 0:
                token_list.append(word.lower())
            word = ""
    if ignore_stopwords:
        return [token for token in token_list if not token in STOPWORDS] #change to exclude stopwords
    else:
        return token_list


def add_to_hashmap(current_hashmap, token_list, current_id, important=False):
    #add current token list to the current hashmap
    stem = stemmer('english')
    for token in token_list:
        token = stem.stemWord(token)
        if len(current_hashmap[token]) == 0 or current_hashmap[token][-1].id != current_id:
            current_hashmap[token].append(doc(current_id, important))  #does id and frequency
        else:
            current_hashmap[token][-1].increment_freq(1, important)
    

def write_to_file(current_hashmap, file_name):
    #writes hashmap to a file
    big_string = ''
    with open(file_name, 'w') as h:
        for key,val in current_hashmap.items():
            try:
                big_string += key + "->" + str(val) + "\n"
                if len(big_string) > 1000000:
                    h.write(big_string)
                    big_string = ''
            except:
                print(key, "    ", val)
        h.write(big_string)
        big_string = ''
    

def merge(file_dir, file_name, file_number):
    # merges indexes to become one larger index
    f1 = open(Path(f"{file_dir}\{file_name}1.txt"))
    for i in range(1, file_number):
        f2 = open(Path(f"{file_dir}\{file_name}{i+1}.txt"))
        if CONSOLE_UPDATES: print(f"Merging {file_name}1 and {file_name}{i+1}")
        big_string = ''
        current1 = f1.readline()
        current2 = f2.readline()
        while current1 != '' or current2 != '':
            n = open(Path(f"{file_dir}\{file_name}temp.txt"), 'a')
            if current1.split('->')[0] == current2.split('->')[0]:
                newline = current1.strip('\n') + current2.split('->')[1].strip('\n')
                newline = newline.replace('][', ', ') + '\n'
                big_string += newline
                current1 = f1.readline()
                current2 = f2.readline()
            elif current2 == '':
                big_string += current1
                current1 = f1.readline()
            elif current1 == '':
                big_string += current2
                current2 = f2.readline()
            elif current1.split('->')[0] < current2.split('->')[0]:
                big_string += current1
                current1 = f1.readline()
            elif current1.split('->')[0] > current2.split('->')[0]:
                big_string += current2
                current2 = f2.readline()
            if len(big_string) > 10000000: #10,000,000
                n.write(big_string)
                big_string = ''
        n.write(big_string)
        big_string = ''
        n.close()
        f1.close()
        f2.close()
        if os.path.exists(Path(f"{file_dir}\{file_name}1.txt")):
            os.remove(Path(f"{file_dir}\{file_name}1.txt"))
        if os.path.exists(Path(f"{file_dir}\{file_name}{i+1}.txt")):
            os.remove(Path(f"{file_dir}\{file_name}{i+1}.txt"))
        os.rename(Path(f"{file_dir}\{file_name}temp.txt"), Path(f"{file_dir}\{file_name}1.txt"))
        f1 = open(Path(f"{file_dir}\{file_name}1.txt"))
    f1.close()
    os.rename(Path(f"{file_dir}\{file_name}1.txt"), Path(f"{file_dir}\\inverted_index.txt"))

            
def index_the_index(index_dir, index_file_name, new_name):
    #makes json file of position for first two characters in file
    #ex: 'ca':164256
    index_path = Path(f'{index_dir}\{index_file_name}.txt')
    current_letter = ''
    current_pos = 0
    indexed_index = dict()
    with open(index_path, 'r') as f:    
        for line in f:
            next_letter = (line[0:4].split('-')[0] if len(line[0:4].split('-')) > 1 else line[0:4])
            if next_letter != current_letter:
                indexed_index[next_letter] = current_pos
            current_pos += len(line) + 1
            current_letter = next_letter
    with open(Path(f'{index_dir}\{new_name}'), 'w') as o:
        json.dump(indexed_index, o)

def index_docid(index_dir, index_file_name, new_name):
    #makes json file of position for first two characters in file
    #ex: 'ca':164256
    index_path = Path(f'{index_dir}\{index_file_name}.txt')
    current_pos = 0
    indexed_index = dict()
    with open(index_path, 'r') as f:    
        for line in f:
            current_num = int(line.split('->')[0])
            if current_num % 100 == 0:
                indexed_index[current_num] = current_pos
            current_pos += len(line) + 1
    with open(Path(f'{index_dir}\{new_name}'), 'w') as o:
        json.dump(indexed_index, o)

def calculate_tfidf_in_index(index_dir, index_file_name, total_docs, important_weight):
    old = open(Path(f'{index_dir}\{index_file_name}.txt'))
    big_string = ''
    for line in old:
        term, doc_list = line[:-1].split('->')
        doc_list = eval(doc_list)
        total_n = len(doc_list)
        new_list = []
        for tup in doc_list:
            tfidf =  (1 + math.log(tup[1] + (tup[2] * important_weight), 10) + math.log(total_docs/total_n))
            new_list.append((tup[0], round(tfidf, 3)))
        new_list = sorted(new_list, key=lambda x: x[1], reverse=True) #ordered by tf_idf score
        big_string += term + '->' + str(new_list) + '\n'
        if len(big_string) > 10000000: #10,000,000
            with open(Path(f"{index_dir}\\tfidf_index.txt"), 'a') as n:
                n.write(big_string)
                big_string = ''
    with open(Path(f"{index_dir}\\tfidf_index.txt"), 'a') as n:
        n.write(big_string)
        big_string = ''
    old.close()

def index(file_path):
    #main program to create the inverted index file. Creates smaller indexs and merges indexes if necessary

    file_dir = r'index_info'
    file_name = r'hash'
    file_number = 1
    
    if os.path.exists(file_dir): #deletes files if run previously
        for file in os.listdir(file_dir):
            os.remove(Path(f"{file_dir}\{file}"))
        os.rmdir(file_dir)
    os.mkdir(file_dir)
    
    hashmap = defaultdict(list)
    current_id = 0
    docidstring = ''

    for directory, folder_list, file_list in os.walk(file_path): 
        for file in file_list:
            file_directory = Path(directory + r'\\' + file)
            with open(file_directory) as f:
                data = json.load(f)
                docidstring += str(current_id) + "->" + data['url'] + '\n'
            content = BeautifulSoup(data['content'], 'html.parser')
            try:
                for tag in IMPORTANT_TAGS:
                    if eval(f"content.{tag} != None"):
                        s = eval(f"content.{tag}.get_text()")
                        add_to_hashmap(hashmap, tokenize(s), current_id, important=True)
            except:
                print(directory, folder_list, file) #debugging purposes
                print(tag, '->', s)                 #debugging purposes
            token_list = tokenize(content.get_text())
            add_to_hashmap(hashmap, token_list, current_id)
            if CONSOLE_UPDATES and current_id % 2500 == 0: print('Current document count:', current_id)
            if len(docidstring) > 1000000:
                with open(Path(f'{file_dir}\\docid_list.txt'), 'a') as a:
                    a.write(docidstring)
                docidstring = ''
            current_id += 1
            if current_id % NUM_FILE_SPLIT == 0: #condition to split files
                hashmap = dict( sorted(hashmap.items(), key=lambda x: x[0]))
                write_to_file(hashmap, Path(f"{file_dir}\{file_name}{file_number}.txt"))
                file_number += 1
                hashmap.clear()
                hashmap = defaultdict(list)

    #write remaining data
    with open(Path(f'{file_dir}\\docid_list.txt'), 'a') as a:
        a.write(docidstring)
    docidstring = ''
    if CONSOLE_UPDATES: print(current_id, "files indexed")
    hashmap = dict( sorted(hashmap.items(), key=lambda x: x[0]))
    write_to_file(hashmap, Path(f"{file_dir}\{file_name}{file_number}.txt"))
    if file_number > 1:
        if CONSOLE_UPDATES: print("Currently merging indexes")
        merge(file_dir, file_name, file_number)
    else:
        os.rename(Path(f"{file_dir}\{file_name}1.txt"), Path(f"{file_dir}\\inverted_index.txt"))
    index_the_index(file_dir, 'inverted_index', 'indexed_index.json')
    if CONSOLE_UPDATES: print('calculating tf-idf')
    calculate_tfidf_in_index(file_dir, 'inverted_index', current_id, IMPORTANT_WEIGHT)
    index_the_index(file_dir, 'tfidf_index', 'indexed_tfidf.json')
    index_docid(file_dir, 'docid_list', 'indexed_docid.json')
    if CONSOLE_UPDATES: print('Finished!')

            
if __name__ == "__main__":
    FOLDER = Path(input("Enter folder name or full path containing data: "))
    if not os.path.exists(FOLDER):
        print("directory does not exist")
    else:
        index(FOLDER)

