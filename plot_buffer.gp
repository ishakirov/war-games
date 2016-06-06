#!/usr/bin/gnuplot

reset

# png
#set terminal pngcairo size 350,292 enhanced font 'Verdana,10'
#set output 'plotting_data1.png'

# svg
set terminal svg size 800,600 fname 'Verdana, Helvetica, Arial, sans-serif' fsize '10'
set output 'buffer.svg'

# color definitions
set border linewidth 1.5
set style line 1 lc rgb '#A4A4A4' lt 1 lw 2 pt 7 ps 1 # --- gray for buffer

#unset key

set ytics 1
set tics scale 1

f1=filename

plot  f1 u 1:7 w lp title columnheader(7) ls 1, 0.5

set terminal x11
replot

pause -1