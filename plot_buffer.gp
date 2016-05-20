#!/usr/bin/gnuplot

reset

# png
#set terminal pngcairo size 350,292 enhanced font 'Verdana,10'
#set output 'plotting_data1.png'

# svg
#set terminal svg size 800,600 fname 'Verdana, Helvetica, Arial, sans-serif' fsize '10'
#set output 'a.svg'

# color definitions
set border linewidth 1.5
set style line 1 lc rgb '#0B6121' lt 1 lw 2 pt 7 ps 1 # --- green for WIPs
set style line 2 lc rgb '#DF0101' lt 1 lw 2 pt 9 ps 1 # --- red for MPs
set style line 3 lc rgb '#0060ad' lt 1 lw 2 pt 5 ps 1 # --- blue for TPs

#unset key

set ytics 1
set tics scale 1

f1=filename

plot  f1 u 1:7 w lp title columnheader(7) ls 1, 0.5

pause -1