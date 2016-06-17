#!/usr/bin/gnuplot

reset

# png
#set terminal pngcairo size 350,292 enhanced font 'Verdana,10'
#set output 'plotting_data1.png'

# svg
set terminal svg size 800,600 fname 'Verdana, Helvetica, Arial, sans-serif' fsize '10'
set output 'fullness.svg'

# color definitions
set border linewidth 1.5
set style line 1 lc rgb '#000000' lt 1 lw 2 pt 7 ps 1 # --- black for buffer

#unset key

set ytics 0.1
set yrange[0:1]
set tics scale 1

set xlabel "Number of Round"
set ylabel "Buffer Fullness (playback time)"

f1=filename

stats f1 using 8 name "A"
plot  f1 u 1:8 w lp title columnheader(8) ls 1, A_mean t "mean value", A_stddev t "Std Dev"

set terminal x11
replot

pause -1