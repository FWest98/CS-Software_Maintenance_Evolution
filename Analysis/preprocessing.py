import json
import pandas as pd
import collections as col
import numpy as np
import statistics as sts
import csv

## load data from results file
with open('mina-nogaps.out', 'r') as data_file:
    json_data = data_file.read()

results = json.loads(json_data)

## create data frame
df = pd.DataFrame(results)
#df = df.drop(columns = ['introCommitMessage', 'introCommitName', 'outroCommitMessage', 'outroCommitName'])

## most recent commit --> CURRENT VERSION
last_commit = np.max(list(df['outroCommitNumber']))

## commits
intro = set(df['introCommitNumber'])
outro = set(df['outroCommitNumber'])
print len(intro.union(outro))

## total. current, removed nr of patterns
print('total number of patterns', len(df))
print('current number of patterns', len(df.loc[df['outroCommitNumber'] == last_commit]))
print('removed number of patterns', len(df) - len(df.loc[df['outroCommitNumber'] == last_commit]))

## list of all pattern names
pattern_names = list(set(df['patternName']))

## file keys for each type of pattern
file_keys = {}
all_file_keys = {}
for p in pattern_names:
    aux = df['pattern'].loc[df['patternName'] == p]

    for elem in aux:
        keys = elem.keys()
        keys = [k for k in keys if 'file' in k or 'File' in k]
    ## keep delegatorFile, strategyFile & adapterFile for the corresponding patterns (t.b.u. for identifying duplications)
    file_keys[p] = keys[1] if p in ['Bridge', 'Strategy'] else keys[0]
    all_file_keys[p] = keys

print('df entries before merge', len(df))

### MULTIPLE INSTANCES OF THE SAME PATTERN IN THE SAME COMMIT IN THE SAME FILE --> COLLAPSE
overview = {}

for p in pattern_names:
    ## all instances of pattern p & their idx in the df
    pattern_p = df.loc[df['patternName'] == p]
    pattern_idx = pattern_p.index

    overview[p] = []

    ## group intro, outro, file name for each pattern instance
    for idx in pattern_idx:
        elem = pattern_p.loc[idx]

        intro = elem['introCommitNumber']
        outro = elem['outroCommitNumber']

        ## get the actual file, not entire path
        f = elem['pattern'][file_keys[p]]
        f = f.split('/')
        f = f[len(f) - 1]
  
        overview[p].append((idx, (p, f, intro, outro)))

to_collapse = {}

## group by (file, intro, outro) --> get the idx (i.e. the pattern instance duplications)
for k in overview.keys():
    aux = overview[k]
    for idx, content in aux:
        if content in to_collapse.keys():
            to_collapse[content].append(idx)
        else:
            to_collapse[content] = [idx]


## remove duplicated pattern instances entries (merge pattern information)
## important: file paths remain consistent
for k in to_collapse.keys():
    elem = to_collapse[k]
    if len(elem) > 1:
        new_pattern = {}

        for i in range(0, len(elem)):
            new_pattern['instance_' + str(i)] = df.loc[elem[i]]['pattern']

        df.at[elem[0], 'pattern'] = new_pattern

        df = df.drop(elem[1:len(elem)])

print('df entries after merge', len(df))

### EXTEND DF WITH PATTERN PATH & BASE FILE NAME (SCOPE OF THE PATTERN)
scope_info = []
path_info = []
file_info = []

for index, row in df.iterrows():
    scope_aux = {'scope': '', 'specificScope': ''}
    pattern = row['patternName']
    pattern_info = row['pattern']

    
    path = pattern_info['instance_0'][file_keys[pattern]] if 'instance_0' in pattern_info.keys() else  pattern_info[file_keys[pattern]]
    fileName = path.split('/')[len(path.split('/')) - 1]

    ## main component
    scope = path.split('/')[1]


    ## 'leaf' component
    specific_scope = path.split('mina')
    specific_scope = specific_scope[len(specific_scope) - 1].split('/')
    specific_scope = '-'.join(specific_scope[1:len(specific_scope) - 1])
    specific_scope = '-'. join([scope, specific_scope])

    scope_aux['scope'] = scope
    scope_aux['specificScope'] = specific_scope

    scope_info.append(scope_aux)
    path_info.append(path)
    file_info.append(fileName)


df['scopeInfo'] = scope_info
df['fileName'] = file_info
df['path'] = path_info


### CROSS MATCH PATTERNS COMMIT 1850 - 1851 (92 patterns per each commit)
com1850 = df.loc[df['outroCommitNumber'] == 1850]
com1851 = df.loc[df['introCommitNumber'] == 1851]

all_matched_indexes = []
count = 0

for index, row in com1850.iterrows():
    pattern1850 = row['patternName']
    file1850 = row['fileName']
    pattern_impl1850 = row['pattern']

    match1851 = com1851.loc[(com1851['patternName'] == pattern1850) & (com1851['fileName'] == file1850)]
    
    matched_indexes = []

    ## match the implementation of the pattern instance
    for idx, row1 in match1851.iterrows():
        pattern_impl1851 = row1['pattern']

        if pattern_impl1850.keys() == pattern_impl1851.keys():
            ## exclude path to impl files since naming convention changes
            keys = set(pattern_impl1850.keys()).difference(set(all_file_keys[pattern1850]))
            
            same = [pattern_impl1850[k] == pattern_impl1851[k] for k in keys]
            
            if all(elem == True for elem in same):
                matched_indexes.append(idx)
            else:
                count = count + 1

    if len(matched_indexes):
        matched_index = matched_indexes[0] 

        ## update table for the re-introduced patterns w/ the same implementation
        outro_updated = df.loc[matched_index]['outroCommitNumber']
        df.at[index, 'outroCommitNumber'] = outro_updated
        all_matched_indexes.extend(list(matched_indexes))

df = df.drop(list(set(all_matched_indexes)))
print('df entries after cross match', len(df))

print('importing preprocessed dataset to csv/json')
with open('pre_processed_dataset.csv', mode = 'w') as f: 
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    writer.writerow(df.columns)
    cols =  [df.columns[i] for i in range(0, len(df.columns))]

    for index, row in df.iterrows():
        writer.writerow([row[col] for col in cols])

df.to_json('preprocessed_data_json.json')


current_df = df.loc[df['outroCommitNumber'] == last_commit]
### export current patterns to csv file
with open('current_patterns.csv', mode = 'w') as f: 
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    for idx, row in current_df.iterrows():
        writer.writerow([idx, row['patternName'], row['pattern'], row['introCommitNumber'], row['introCommitName'], row['introCommitMessage'], row['path']])



    
removed_df = df.loc[df['outroCommitNumber'] != last_commit]
### export removed patterns to csv file
with open('removed_patterns.csv', mode = 'w') as f: 
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    for idx, row in removed_df.iterrows():
        writer.writerow([idx, row['patternName'], row['pattern'], row['introCommitNumber'], row['introCommitName'], row['introCommitMessage'], row['path'], row['lifespan']])


strategy_df = df.loc[df['patternName'] == 'Strategy']
strategy_df = strategy_df.loc[strategy_df['fileName'] == 'IoService.java']
### export current patterns to csv file
with open('ioservice_patterns.csv', mode = 'w') as f: 
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    for idx, row in strategy_df.iterrows():
        writer.writerow([idx, row['patternName'], row['pattern'], row['introCommitNumber'], row['introCommitName'], row['introCommitMessage'], row['path'], row['lifespan'],
        row['outroCommitNumber'], row['outroCommitName'], row['outroCommitMessage']])












            



