#!/bin/sh

py_script_route=$(pwd)
files_route=$(pwd)/files

if [ -f "$files_route/$1.mp4" ]; then
	eval $(ffprobe -v error -of flat=s=_ -select_streams v:0 -show_entries stream=height,width "$files_route/$1.mp4")
	width=${streams_stream_0_width}
	height=${streams_stream_0_height}
else
	echo 'No existe el fichero!'
fi


echo -n 'Borrando archivos. '

if [ -f "$files_route/$1_orig.yuv" ]; then
	rm "$files_route/$1_orig.yuv"
fi

if [ -f "$files_route/$1_lhe.yuv" ]; then
	rm "$files_route/$1_lhe.yuv"
fi

if [ -f "$files_route/$1.mlhe" ]; then
	rm "$files_route/$1.mlhe"
fi

echo -n 'Generando '$1'_orig.yuv, '
ffmpeg -i "$files_route/$1.mp4" -f rawvideo -vcodec rawvideo -pix_fmt yuv420p "$files_route/$1_orig.yuv" > /dev/null 2>&1
echo -n $1'.mlhe, '
ffmpeg -i "$files_route/$1.mp4" -pix_fmt yuv420p "$files_route/$1.mlhe" > /dev/null 2>&1
echo $1'_lhe.yuv'
ffmpeg -i "$files_route/$1.mlhe" -f rawvideo -vcodec rawvideo -pix_fmt yuv420p "$files_route/$1_lhe.yuv" > /dev/null 2>&1
echo 
python "$py_script_route/psnr.py" "$files_route/$1_orig.yuv" $width $height IYUV "$files_route/$1_lhe.yuv"
