# mlhe_psnr
It converts (MP4 -> YUV) and (MP4 -> MLHE -> YUV). Then i calculates the PSNR

## Usage

*sh psnryuv.sh {name of mp4 file without extension}*

Exmple:

*sh psnryuv.sh bunny*

It turns *.mp4 --> .yuv* and *.mp4 --> .mlhe --> .yuv* and calculates PSNR between the .yuv files