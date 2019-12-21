#!/bin/sh

mkdir -p calculations/$1

python3 table_of_moon.py        $1
python3 table_of_solarterms.py  $1
python3 table_of_sun.py         $1
python3 table_of_sunrise_and_sunset.py $1
python3 table_of_planets.py     $1
python3 table_of_juliantime.py  $1
python3 table_of_calendar.py    $1
python3 table_of_events.py      $1

python3 monthgen.py     $1
mv $1.pdf output/$1.pdf
