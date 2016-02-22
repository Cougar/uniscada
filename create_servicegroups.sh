#!/bin/sh

BASEURL="http://127.0.0.1/api/v1"

for servicegroup in ${*:-$(ls conf/servicegroup)}; do
    echo -n "$servicegroup: create .."
    curl --silent --request POST --data '[ { "servicegroup": "'$servicegroup'" } ]' ${BASEURL}/servicegroups/ && echo -n " OK" || echo -n " ERROR"
    echo -n " config .."
    curl --silent --request PUT --data @./conf/servicegroup/$servicegroup ${BASEURL}/servicegroups/$servicegroup && echo -n " OK" || echo -n " ERROR"
    echo
done

