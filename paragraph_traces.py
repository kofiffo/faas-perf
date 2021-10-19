import json
import matplotlib.pyplot as plt
import numpy as np

filename = "paragraph-async"
with open(f"../json/{filename}.json", 'r') as json_data:
    data = json.load(json_data)

response_times = []

for trace in data["data"]:
    if len(list(trace["spans"])) == 6:
        for span in trace["spans"]:
            if span["operationName"] == "paragraph":
                startTime = span["startTime"]
            if span["operationName"] == "merge":
                endTime = span["startTime"] + span["duration"]

        traceDuration = endTime - startTime
        response_times.append(traceDuration / 1000000)

print(f"Valid traces: {len(response_times)}")

sum = 0

for time in response_times:
    sum += time

print(sum / len(response_times))

n, bins, patches = plt.hist(x=response_times, bins="auto", color="#0504aa", alpha=0.7, rwidth=0.85)

plt.grid(axis='y', alpha=0.75)
plt.xlabel("Response times (s)")
plt.ylabel("Number of responses")
plt.title("Response time histogram of synchronous function invocations")
maxfreq = n.max()
# Set a clean upper y-axis limit.
plt.ylim(ymax=np.ceil(maxfreq / 10) * 10 if maxfreq % 10 else maxfreq + 10)

plt.show()
