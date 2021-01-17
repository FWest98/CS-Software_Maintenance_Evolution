import json
import pandas as pd
import collections as col
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
#plt.style.use('seaborn-whitegrid')
import numpy as np
from operator import itemgetter
import seaborn as sns

# bar plot for visualising pattern occurence
# data = [(pattern name, nr of occurences)]
# magnitude = scalar that det. the spread of xticks (must be tweaked per figure)
def bar_plot(data, x_label, y_label, title, save_name, magnitude):
    patterns = [p for p, o in data]
    occurrences = np.int_([o for p, o in data])

    fig, ax = plt.subplots(figsize = (16, 10))

    # horizontal bar plot
    ax.barh(np.arange(len(patterns)), occurrences, align = 'center', color = '#A9A9A9', edgecolor = '#A9A9A9')

    # set ticks and labels 
    ax.set_yticks(np.arange(len(patterns)))
    ax.set_yticklabels(patterns, rotation = 45) # pattern names as labels
    ax.set_xticks([i * magnitude for i in range(0, np.max(occurrences) / magnitude + 1)])

    #ax.invert_yaxis()  # labels read top-to-bottom

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)

    ax.set_title(title)
    ax.grid()

    # save plot
    plt.savefig(save_name)


def pie_plot(sizes, labels, explode, title, save_name):
    fig1, ax1 = plt.subplots(figsize = (14, 10))
    colors = ['#808b96',  '#d5d8dc', '#abb2b9', '#2c3e50',  '#4682b4', '#eaf2f8', '#d5d8dc']

    ax1.pie(sizes, explode = explode, labels = labels, autopct = '%1.1f%%', shadow = False, startangle = 90, colors = colors)
    ax1.axis('equal') 
    #ax1.set_title('Percentage of removed vs. current patterns')

    plt.savefig(save_name + '.png')


def scatter_plot(x, y, xlabel, ylabel, save_name, xticks_freq, reg_fit):
    fig1, ax1 = plt.subplots(figsize = (9, 6))

    ax1 = sns.regplot(x = x, y = y) if reg_fit else ax1.scatter(x, y, alpha = 0.5, edgecolors = 'none', cmap = 'twilight')

    plt.xlabel(xlabel)
    plt.xticks([i * xticks_freq for i in range(0, np.max(x) / xticks_freq + 1)])
    plt.ylabel(ylabel)

    plt.savefig(save_name)



## load data
with open('plot_data.json', 'r') as data_file:
    json_data = data_file.read()
plot_data = json.loads(json_data)

print(plot_data.keys())

### BAR PLOTS FOR PATTERN OCCURRENCE ###
# all occurrences
bar_plot(plot_data['all_patterns'], 'Pattern occurrence', 'Pattern', 'Occurrence of all patterns', 'pattern_occurrence_all', 100)

# current occurrences
bar_plot(plot_data['current_patterns'], 'Pattern occurrence', 'Pattern', 'Occurrence of current patterns', 'pattern_occurrence_current', 5)

# removed occurrences
bar_plot(plot_data['removed_patterns'], 'Pattern occurrence', 'Pattern', 'Occurrence of removed patterns', 'pattern_occurrence_removed', 100)

# median pattern life
bar_plot(sorted(plot_data['median_lifespans'], key = itemgetter(1)), 'Median life span expressed in commits', 'Pattern', 'Median life span of removed patterns', 'mean_life', 50)

### PIE PLOTS ###
## percentage of current vs. removed patterns
sizes = [np.sum([o for p, o in plot_data['removed_patterns']]), np.sum([o for p, o in plot_data['current_patterns']])]
pie_plot(sizes, ['Removed patterns', 'Currently existing patterns'], (0, 0.1),  '', 'current_removed_per')

# percentage of intro/outro commits
pie_plot(plot_data['intro/outro/both'], ['Intro', 'Outro', 'Intro/Outro'], (0.0, 0.0, 0.1),'', 'intro_outro_per')


### SCATTER PLOTS ###
## additions/removals per commit
x_axis = [y[0] for x, y in plot_data['commit_datapoints']]
y_axis = [y[1] for x, y in plot_data['commit_datapoints']]
scatter_plot(x_axis, y_axis, 'Pattern additions', 'Pattern removals', 'additions_removals_commit', 10, False)

## commit timeline (commit --> nr of patterns)
x_axis = [x for x, y in plot_data['commit_stats']]
y_axis = [y for x, y in plot_data['commit_stats']]
scatter_plot(x_axis, y_axis, 'Commit', 'Number of patterns', 'commit_timeline', 300, True)

### SCOPE PLOTS ###
## all scopes
all_scopes = plot_data['all_scopes']
others = []
sizes = []
labels = []

for el in all_scopes:
    if el[1] < 50:
        others.append(el)
    else:
        sizes.append(el[1])
        labels.append(el[0])

sizes.append(np.sum([ss for s, ss in others]))
labels.append('Others')

pie_plot(sizes, labels, (0, 0.1, 0.1), '', 'all_scopes_per')
bar_plot(others, 'Pattern occurence', 'Scope', 'Occurrences of patterns in other scopes', 'other_scopes', 5)

## current scopes
current_scopes = [(sn, s) for sn, s in plot_data['current_scopes'] if sn != 'mina-benchmarks']
explode1 = (0.0, 0.1, 0.1, 0.1, 0.1)
pie_plot([s for sn, s in current_scopes], [sn for sn, s in current_scopes], explode1, '', 'current_scopes_per')

## current scopes extended
current_scopes_core = plot_data['current_specific_scopes']
bar_plot(current_scopes_core, 'Pattern occurrence', 'Scope', 'Pattern scopes within the MINA core component', 'core_scopes', 1)

