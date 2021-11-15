#!/bin/bash

cd ./"$1" || exit

# delete current deployment if exists
if [ -n "$(kubectl get pod | grep "$1")" ]; then
  podName="$(kubectl get pod | grep "$1" | awk '{print $1}')"
  echo "Deleting current deployment..."
  kubeless function delete "$1" || exit
  kubectl wait --for=delete pod/"$podName" --timeout=60s
fi

# build and push new image
imageName="kofiffo/$1-kubeless:latest"
docker build -t "$imageName" .
docker push "$imageName"

# deploy function
if [ -z "$2" ]; then
  kubeless function deploy "$1" --runtime-image "$imageName" --from-file "$1".py --handler "$1".handle
else
  kubeless function deploy "$1" --runtime-image "$imageName" --from-file "$1".py --handler "$1".handle --env INVOCATION="$2"
fi
podName="$(kubectl get pod | grep "$1" | awk '{print $1}')"
kubectl wait --for=condition=Ready pod/"$podName" --timeout=60s

# expose paragraph function if it was rebuilt
if [ "$1" = "paragraph" ]; then
  if [ "$(ps -ax | grep -c "kubectl port-forward svc/paragraph 8080:8080")" != 1 ]; then
    echo "Killing previous port-forward process..."
    pid="$(ps -ax | grep "kubectl port-forward svc/paragraph 8080:8080" | awk 'NR==1 {print $1}')"
    kill -INT "$pid"
  fi
  kubectl port-forward svc/paragraph 8080:8080 &
fi