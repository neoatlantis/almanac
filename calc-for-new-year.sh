#!/bin/sh

mkdir -p calculations/$1

echo "table of moon"
python3 table_of_moon.py        $1

echo "table of solar terms"
python3 table_of_solarterms.py  $1

echo "table of sun"
python3 table_of_sun.py         $1

echo "table of sunrise and sunset"
python3 table_of_sunrise_and_sunset.py $1

echo "table of planets"
python3 table_of_planets.py     $1

echo "table of julian time"
python3 table_of_juliantime.py  $1

echo "table of calendar"
python3 table_of_calendar.py    $1

echo "table of events"
python3 table_of_events.py      $1

python3 monthgen.py     $1
mv $1.pdf output/$1.pdf
