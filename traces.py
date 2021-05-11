import json
import matplotlib.pyplot as plt

file_name = "imaging-raw-trace"
file_path = "../" + file_name + ".json"

with open(file_path, 'r') as json_data:
    data = json.load(json_data)

response_times = []
num_bins = 10
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

n, bins, patches = plt.hist(response_times, num_bins, facecolor='blue', alpha=0.5)
plt.title("Response time histogram")

print(file_name)
print(f"average response time: {sum / 195}")
plt.show()
