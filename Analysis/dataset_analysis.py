import json
import pandas as pd
import collections as col
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
# plt.style.use('seaborn-whitegrid')
import numpy as np
import statistics as sts

## create data frame, drop unnecessary cols
# df = pd.read_csv('pre_processed_dataset.csv')
df = pd.read_json('preprocessed_data_json.json')
df = df.drop(columns = ['pattern'])

## total nr of pattern instnaces
print('total number of patterns retrieved', len(df))

# last commit
last_commit = np.max(list(df['outroCommitNumber']))

## list of pattern names
pattern_names = set(df['patternName'])

## store data for plots
plot_data = {}

## all patterns occurrences
all_patterns = df['patternName']
all_pat = col.Counter(all_patterns).most_common()
plot_data['all_patterns'] = all_pat

## current patterns occurrences
## i.e. outroCommitNumber == last_commit
current_patterns = df['patternName'].loc[df['outroCommitNumber'] == last_commit]
current_pat = col.Counter(current_patterns).most_common()
plot_data['current_patterns'] = current_pat

print('current patterns', len(current_patterns))

## removed pattern occurrences
removed_patterns = df['patternName'].loc[df['outroCommitNumber'] != last_commit]
removed_pat = col.Counter(removed_patterns).most_common()
plot_data['removed_patterns'] = removed_pat

## median life span
removed_patterns = df.loc[df['outroCommitNumber'] != last_commit]
median_lifespan = np.median(removed_patterns['lifespan'])  

lifespans = []
lifespans.append(('Overall median', median_lifespan))

for p in set(removed_patterns['patternName']):
    p_life = removed_patterns['lifespan'].loc[removed_patterns['patternName'] == p]
    p_med_life = np.median(p_life)
    lifespans.append((p, p_med_life))

plot_data['median_lifespans'] = lifespans

## patterns w/ lifespan of 1
patterns_ls1 = df['patternName'].loc[df['lifespan'] == 1]
patterns_ls1 = col.Counter(patterns_ls1).most_common()
plot_data['lifespan1'] = patterns_ls1

## all scopes
all_scopes = df['scopeInfo']
all_scopes = col.Counter([elem['scope'] for elem in all_scopes]).most_common()
plot_data['all_scopes'] = all_scopes

## current scopes (outliers, namings from later versions which dont match the current code structure)
current_scopes = df['scopeInfo'].loc[df['outroCommitNumber'] == last_commit]
curr_scopes = col.Counter([elem['scope'] for elem in current_scopes if 'mina-' in elem['scope']]).most_common()
curr_specific_scopes = col.Counter([elem['specificScope'] for elem in current_scopes if 'mina-' in elem['scope']]).most_common()

plot_data['current_scopes'] = curr_scopes
plot_data['current_specific_scopes'] = curr_specific_scopes

## removals/additions per commit
intro_commits = set(df['introCommitNumber'])
outro_commits = set(df['outroCommitNumber'])
intro_outro = intro_commits.intersection(outro_commits)
intro_commits = intro_commits - intro_outro
outro_commits = outro_commits - intro_outro
all_commits = intro_commits.union(outro_commits, intro_outro)

## total number of commits
print('total number of commits', len(intro_commits))

plot_data['intro/outro/both'] = [len(intro_commits), len(outro_commits), len(intro_outro)]

## commit --> number of additions/removals
commit_datapoints = []
commit_stats = []

for commit in all_commits:
    adds = len(df.loc[df['introCommitNumber'] == commit])
    rems = len(df.loc[df['outroCommitNumber'] == commit])

    commit_datapoints.append((commit, (adds, rems)))

commit_datapoints = sorted(commit_datapoints)

## commit --> number of patterns overall
for i in range(0, len(commit_datapoints)):
    time_pt = commit_datapoints[0:i+1]

    additions = np.sum([y[0] for x, y in time_pt])
    removals = np.sum([y[1] for x, y in time_pt])
    stats = additions - removals

    commit_stats.append((commit_datapoints[i][0], stats))

plot_data['commit_datapoints'] = commit_datapoints
plot_data['commit_stats'] = commit_stats

## save plot_data
with open("plot_data.json", "w") as f:
    json.dump(plot_data, f)















