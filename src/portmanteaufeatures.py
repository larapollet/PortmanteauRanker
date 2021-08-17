import re
from nltk.corpus import wordnet
from nltk.corpus import brown
import json
import csv
from itertools import chain
from nltk.util import ngrams
import os

input_path = "" #should be path to a file containing portmanteaus with lines organised as given by one of two formats:
                #format 1: "root word 1, root word 2, correct portmanteau, portmanteau1, portmanteau2, ..."
                #format 2: "root word 1, root word 2, portmanteau1, portmanteau2, ..."
output_path = "" #path to write the portmanteau features to

format = True # should be false when using format 1, true when using format 2

#count the syllables in a word
def count_syllables(word):
    return len(
        re.findall('(?!e$)[aeiouy]+', word, re.I) +
        re.findall('^[^aeiouy]*e$', word, re.I)
    )

#Readability feature
def readability(word, word1, word2):
    wordsyl = count_syllables(word)
    word1syl = count_syllables(word1)
    word2syl = count_syllables(word2)
    if wordsyl == 0:
        precentagesyl = 0
        precentage1syl = 0
        precentage2syl = 0
    else:
        precentagesyl = float(wordsyl)/float(word1syl + word2syl)
        precentage1syl = float(word1syl)/float(wordsyl)
        precentage2syl = float(word2syl)/float(wordsyl)
    return wordsyl, precentagesyl, precentage1syl, precentage2syl

## return all possible combinations of word split according to the minimum substring length
def split_string(s, min_str_length = 2, root_string=[], results=[]):
    for i in range(min_str_length,len(s)):
        if i == min_str_length:
            primary_root_string=root_string
        else:
            root_string = primary_root_string
        if len(s[i:])>= min_str_length :
            results.append(list(chain(*[root_string,[s[:i]],[s[i:]]])))
            root_string = list(chain(*[root_string,[s[:i]]]))
            split_string(s[i:], min_str_length, root_string, results)
    return results

def maximum_splitscore(possible_splits, woorden):
    score = 0
    for split in possible_splits:
        current_score = 0
        for elem in split:
            if elem in woorden:
                current_score += len(elem)
        if current_score > score:
            score = current_score
    return score
        
#memorability feature
def memorability(word, woorden):
    if len(word) < 3:
        return 0
    #for 3 tot einde van lengte van het woord --> construeer n-gram
    possible_splits = split_string(word, min_str_length=3)
    split_score = maximum_splitscore(possible_splits, woorden)
    return float(split_score)/float((len(word)))

#word structure feature
def wordstructure(word, word1, word2):
    #structure constructed form the first word
    y1 = os.path.commonprefix([word, word1])
    z2 = word.replace(y1,'') 
    z1 = word1.replace(y1,'')
    y2 = word2.replace(z2,'')

    #structure constructed form the second word
    z4 = os.path.commonprefix([word[::-1], word2[::-1]])[::-1]
    y3 = word.replace(z4,'') 
    z3 = word1.replace(y3,'')
    y4 = word2.replace(z4,'')

    #overlap achtervoegsel y1 en y2 + voorvoegseloverlap z1 + z2
    structure1 = len(os.path.commonprefix([z1, z2])) + len(os.path.commonprefix([y1[::-1], y2[::-1]]))
    structure2 = len(os.path.commonprefix([z3, z4])) + len(os.path.commonprefix([y3[::-1], y4[::-1]]))
    structure = max([structure1, structure2])
    if (count_syllables(word) == count_syllables(word1) or count_syllables(word) == count_syllables(word2)):
        structure += 1
    precentage1 = float(len(y1))/float(len(word1))
    precentage2 = float(len(z4))/float(len(word2))
    return precentage1,precentage2,structure

#pronouncability feature
def pronouncability(word):
    chrs = [c for c in word]
    grams = [2,3,4]
    weighted_grams = 0
    for i in grams:
        igram = list(ngrams(chrs,i))
        for elem in igram:
            frequency = 0
            joint_igram = ('').join(elem)
            with open('../data/' + str(i) +'grams.txt') as json_file:
                frequencydict = json.load(json_file)
            if joint_igram in frequencydict.keys():
                frequency += frequencydict[joint_igram]
        weight = float(i)/float((sum(grams)))
        if float((len(word) - i + 1)) == 0:
            result = 0
        else:
            result = float(frequency)/float(len(word)- i + 1)
        weighted_grams += (weight*result)
        if i == 2:
            gram2 = result
        if i == 3:
            gram3 = result
        if i == 4:
            gram4 = result
    mem = (gram2, gram3, gram4, weighted_grams,float(gram2)/float(len(word)), float(gram3)/float(len(word)), float(gram4)/float(len(word)), float(weighted_grams)/float(len(word)))
    return mem



def read_data(words):
    data = {}
    j = 0
    data['learning'] = []
    path = input_path 
    with open(path) as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in csvreader:
            root1 = row[0]
            root2 = row[1]
            true_port = row[2].lower()
            predicted = format
            j += 1
            if j%100 == 0:
                print j
            if root1 != root1.lower():
                continue
            if root2 != root2.lower():
                continue
            for i in range(2, len(row)):
                d = {'root1': root1, 'root2': root2}
                elem = row[i].lower()
                if elem != root1 and elem != root2:
                    d['result'] = elem
                    read = readability(elem, root1, root2)
                    d['syllables_port'] = read[0]
                    d['syllables_rel'] = read[1]
                    d['syllables_rel_to_word1'] = read[2]
                    d['syllables_rel_to_word2'] = read[3]
                    structure = wordstructure(elem, root1, root2)
                    d['percentage1'] = structure[0]
                    d['percentage2'] = structure[1]
                    d['wordstructure'] = structure[2]
                    d['memorability'] = memorability(elem, woorden)
                    pron = pronouncability(elem)
                    d['pronouncability_2gram'] = pron[0]
                    d['pronouncability_3gram'] = pron[1]
                    d['pronouncability_4gram'] = pron[2]
                    d['pronouncability_weighted'] = pron[3]
                    d['pronouncability_2gram_div'] = pron[4]
                    d['pronouncability_3gram_div'] = pron[5]
                    d['pronouncability_4gram_div'] = pron[6]
                    d['pronouncability_weighted_div'] = pron[7]
                    d['length'] = len(elem)
                    d['unused_root_length'] = len(root1) + len(root2) - len(elem)
                    d['root1_min_length'] = len(elem) - len(root1) 
                    d['root2_min_length'] = len(elem) - len(root2)
                    d['prediction_place'] = i - 2
                    if not format:
                        if elem == true_port:
                            predicted = True
                            d['portmanteau'] = True
                        else: 
                            d['portmanteau'] = False
                    else:
                        d['portmanteau'] = False
                else:
                    continue
                data['learning'].append(d)

    path_out = output_path
    with open(path_out, 'w') as outfile:
        json.dump(data, outfile)


def main():
    words = set(wordnet.words())
    read_data(words)


if __name__ == '__main__':
    main()
