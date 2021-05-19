import json
import matplotlib.pyplot as plt
import numpy as np

file_names = ["imaging-async-trace-2", "imaging-async-raw-trace-2", "imaging-async-b64-trace-2"]
data_sets = []
num_bins = 10

for name in file_names:
    file_path = "../" + name + ".json"
    with open(file_path, 'r') as json_data:
        data = json.load(json_data)


    response_times = []
    sum = 0

    for i in range(200):
        try:
            firstSpanStartTime = data["data"][i]["spans"][0]["startTime"]
            secondSpanStartTime = data["data"][i]["spans"][1]["startTime"]
            secondSpanDuration = data["data"][i]["spans"][1]["duration"]

            fullDuration = (secondSpanStartTime + secondSpanDuration - firstSpanStartTime) / 1000000
            response_times.append(fullDuration)
            sum += fullDuration
        except IndexError as e:
            pass

    data_sets.append(response_times)

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

colors = ["red", "tan", "lime"]
labels = ["minio", "raw", "base64"]
# n, bins, patches = plt.hist(data_sets, bins=[0.9425, 1.11558, 1.28866, 1.46174, 1.63482, 1.8079, 1.98098, 2.15406, 2.32714, 2.50022, 2.6733], color=colors, label=labels, alpha=0.5)
n, bins, patches = plt.hist(data_sets, bins=np.arange(minimum, maximum + binwidth, binwidth), color=colors, label=labels, alpha=0.5)
plt.xticks(bins)

# for i in range(len(data_sets)):
#     plt.text(i, len(data_sets[i]), len(data_sets[i]))

plt.legend(prop={'size': 10})
plt.title("Response time histogram")
plt.xlabel("Response times")
plt.ylabel("Number of responses")

plt.show()
