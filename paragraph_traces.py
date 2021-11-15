import json
import matplotlib.pyplot as plt
import numpy as np


# function to add value labels
def addlabels(x, y):
    for i in range(len(x)):
        plt.text(i, y[i], "%.3f" % y[i], ha='center')


file_names = ["openfaas-sync", "kubeless-sync", "openfaas-async", "kubeless-async"]
# file_names = ["openfaas-sync-2", "kubeless-sync-2", "openfaas-async-2", "kubeless-async-2"]
data_sets, avgs, par_avgs, itt_avgs, mer_avgs = ([] for i in range(5))

for name in file_names:
    with open(f"../json/{name}.json", 'r') as json_data:
        data = json.load(json_data)

    response_times, par_times, itt_times, mer_times = ([] for i in range(4))

    for trace in data["data"]:
        if len(list(trace["spans"])) == 6:
            for span in trace["spans"]:
                function = span["operationName"]
                if function == "paragraph":
                    startTime = span["startTime"]
                    par_times.append(span["duration"])
                if "image-to-text" in function:
                    itt_times.append(span["duration"])
                if function == "merge":
                    endTime = span["startTime"] + span["duration"]
                    mer_times.append(span["duration"])

            traceDuration = endTime - startTime
            response_times.append(traceDuration / 1000000)

    par_sum, itt_sum, mer_sum = (0 for i in range(3))

    for duration in par_times:
        par_sum += duration / 1000000
    for duration in itt_times:
        itt_sum += duration / 1000000
    for duration in mer_times:
        mer_sum += duration / 1000000

    par_avgs.append(par_sum / len(par_times))
    itt_avgs.append(itt_sum / len(itt_times))
    mer_avgs.append(mer_sum / len(mer_times))

    print(name)
    print(f"Valid traces: {len(response_times)}")

    sum = 0

    for time in response_times:
        sum += time

    print(f"Average response time: {sum / len(response_times):.3f}s")
    data_sets.append(response_times)

    n, bins, patches = plt.hist(x=response_times, bins="auto", color="#0504aa", alpha=0.7, rwidth=0.85)

    plt.grid(axis='y', alpha=0.75)
    plt.xlabel("Response times (s)")
    plt.ylabel("Number of responses")
    maxfreq = n.max()
    # Set a clean upper y-axis limit.
    plt.ylim(ymax=np.ceil(maxfreq / 10) * 10 if maxfreq % 10 else maxfreq + 10)
    plt.title(name)

    plt.show()

minimum = 100
maximum = 0

for times in data_sets:

    if min(times) < minimum:
        minimum = float(min(times))

    if max(times) > maximum:
        maximum = float(max(times))

print(minimum)
print(maximum)

binwidth = (maximum - minimum) / 10

colors = ['r', 'g', 'b', 'y']
labels = ["OpenFaaS-sync", "Kubeless-sync", "OpenFaaS-async", "Kubeless-async"]

n, bins, patches = plt.hist(x=data_sets, bins=np.arange(minimum, maximum + binwidth, binwidth), color=colors, label=labels, alpha=0.7, rwidth=0.85)
plt.title("Response time histogram of each case")
plt.xticks(bins)
plt.legend(prop={'size': 10})
plt.xlabel("Response times")
plt.ylabel("Number of responses")
plt.show()

avgs.append(par_avgs)
avgs.append(itt_avgs)
avgs.append(mer_avgs)

fn_names = ["paragraph", "image-to-text", "merge"]
idx = 0

for avg in avgs:
    plt.title(f"{fn_names[idx]} function response times")
    idx += 1
    plt.xlabel("Framework and invocation type")
    plt.ylabel("Response time (s)")
    addlabels(file_names, avg)

    barlist = plt.bar(file_names, avg)
    barlist[0].set_color('r')
    barlist[1].set_color('g')
    barlist[2].set_color('b')
    barlist[3].set_color('y')

    plt.show()
