#!/bin/sh

for controller in ${*:-$(ls conf/controller)}; do
    echo -n "$controller: create .."
    curl --silent --request POST --data '[ { "controller": "'$controller'" } ]' http://127.0.0.1/api/v1/controllers/ && echo -n " OK" || echo -n " ERROR"
    echo -n " config .."
    curl --silent --request PUT --data @./conf/controller/$controller http://127.0.0.1/api/v1/controllers/$controller && echo -n " OK" || echo -n " ERROR"
    echo
done
