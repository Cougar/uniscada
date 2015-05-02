#!/bin/sh

for servicegroup in ${*:-$(ls conf/servicegroup)}; do
    echo -n "$servicegroup: create .."
    curl --silent --request POST --data '[ { "servicegroup": "'$servicegroup'" } ]' http://127.0.0.1/api/v1/servicegroups/ && echo -n " OK" || echo -n " ERROR"
    echo -n " config .."
    curl --silent --request PUT --data @./conf/servicegroup/$servicegroup http://127.0.0.1/api/v1/servicegroups/$servicegroup && echo -n " OK" || echo -n " ERROR"
    echo
done

