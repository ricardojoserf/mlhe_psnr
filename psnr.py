#!/usr/bin/env python

"""
Tools for working with YCbCr data.
"""

import argparse
import time
import sys
import os

from collections import namedtuple

import numpy as np



class Y:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.wh = self.width * self.height
        self.div = namedtuple('chroma_div', 'width height')

    def get_420_partitioning(self, width=None, height=None):
        if not width:
            wh = self.wh
        else:
            wh = width * height
        # start-stop
        #       y  y   cb  cb      cr      cr
        return (0, wh, wh, wh/4*5, wh/4*5, wh/2*3)

    def get_422_partitioning(self, width=None, height=None):
        if not width:
            wh = self.wh
        else:
            wh = width * height
        # start-stop
        #       y  y   cb  cb      cr      cr
        return (0, wh, wh, wh/2*3, wh/2*3, wh*2)

class YV12(Y):
    def __init__(self, width, height):
        Y.__init__(self, width, height)

        # width, height
        self.chroma_div = self.div(2, 2)  # Chroma divisor w.r.t luma-size

    def get_frame_size(self, width=None, height=None):
        if not width:
            width = self.width
            height = self.height
        return (width * height * 3 / 2)

    def get_layout(self, width=None, height=None):
        """
        return a tuple of slice-objects
        Y|U|V
        """
        p = self.get_420_partitioning(width, height)
        return (slice(p[0], p[1]),    # start-stop for luma
                slice(p[2], p[3]),    # start-stop for chroma
                slice(p[4], p[5]))    # start-stop for chroma


class IYUV(Y):
    """
    IYUV
    """
    def __init__(self, width, height):
        Y.__init__(self, width, height)
        self.chroma_div = self.div(2, 2)

    def get_frame_size(self, width=None, height=None):
        if not width:
            width = self.width
            height = self.height
        return (width * height * 3 / 2)

    def get_layout(self, width=None, height=None):
        """
        Y|V|U
        """
        p = self.get_420_partitioning(width, height)
        return (slice(p[0], p[1]),
                slice(p[4], p[5]),
                slice(p[2], p[3]))


class NV12(Y):
    """
    NV12
    """
    def __init__(self, width, height):
        Y.__init__(self, width, height)

        # width, height
        self.chroma_div = self.div(2, 2)  # Chroma divisor w.r.t luma-size

    def get_frame_size(self, width=None, height=None):
        if not width:
            width = self.width
            height = self.height
        return (width * height * 3 / 2)

    def get_layout(self, width=None, height=None):
        """
        return a tuple of slice-objects
        Y|U0|V0|U1|V1...
        """
        p = self.get_420_partitioning(width, height)
        return (slice(p[0],   p[1]),       # start-stop for luma
                slice(p[2],   p[5], 2),    # start-stop for chroma
                slice(p[2]+1, p[5], 2))    # start-stop for chroma


class UYVY(Y):
    """
    UYVY
    """
    def __init__(self, width, height):
        Y.__init__(self, width, height)
        self.chroma_div = self.div(2, 1)

    def get_frame_size(self, width=None, height=None):
        if not width:
            width = self.width
            height = self.height
        return (width * height * 2)

    def get_layout(self, width=None, height=None):
        """
        U0|Y0|V0|Y1
        """
        fs = self.get_frame_size(width, height)
        return (slice(1, fs, 2),
                slice(0, fs, 4),
                slice(2, fs, 4))


class YVYU(Y):
    """
    YVYU
    """
    def __init__(self, width, height):
        Y.__init__(self, width, height)
        self.chroma_div = self.div(2, 1)

    def get_frame_size(self, width=None, height=None):
        if not width:
            width = self.width
            height = self.height
        return (width * height * 2)

    def get_layout(self, width=None, height=None):
        """
        Y0|V0|Y1|U0
        """
        fs = self.get_frame_size(width, height)
        return (slice(0, fs, 2),
                slice(3, fs, 4),
                slice(1, fs, 4))


class YUY2(Y):
    """
    YUY2
    """
    def __init__(self, width, height):
        Y.__init__(self, width, height)
        self.chroma_div = self.div(2, 1)

    def get_frame_size(self, width=None, height=None):
        if not width:
            width = self.width
            height = self.height
        return (width * height * 2)

    def get_layout(self, width=None, height=None):
        """
        Y0|U0|Y1|V0
        """
        fs = self.get_frame_size(width, height)
        return (slice(0, fs, 2),
                slice(1, fs, 4),
                slice(3, fs, 4))


class Y422(Y):
    """
    422
    """
    def __init__(self, width, height):
        Y.__init__(self, width, height)
        self.chroma_div = self.div(2, 1)

    def get_frame_size(self, width=None, height=None):
        if not width:
            width = self.width
            height = self.height
        return (width * height * 2)

    def get_layout(self, width=None, height=None):
        """
        Y|U|V
        """
        p = self.get_422_partitioning(width, height)
        return (slice(p[0], p[1]),
                slice(p[2], p[3]),
                slice(p[4], p[5]))




class YCbCr:
 
    def __init__(
        self,
        width=0,
        height=0,
        filename=None,
        yuv_format_in=None,
        yuv_format_out=None,
        filename_out=None,
        filename_diff=None,
        crop_rect=None,
        num=None,
        func=None):

        self.supported_420 = [
            'YV12',
            'IYUV',
            'NV12',
        ]

        self.supported_422 = [
            'UYVY',
            'YVYU',
            'YUY2',
            '422',
        ]

        self.supported_extra = [
            None,
        ]

        if yuv_format_in not in self.supported_420 + self.supported_422 + \
           self.supported_extra:
            raise NameError('Format not supported! "%s"' % yuv_format_in)

        if yuv_format_out not in self.supported_420 + self.supported_422 + \
           self.supported_extra:
            raise NameError('Format not supported! "%s"' % yuv_format_out)

        self.filename = filename
        self.filename_out = filename_out
        self.filename_diff = filename_diff
        self.width = width
        self.height = height
        self.yuv_format_in = yuv_format_in
        self.yuv_format_out = yuv_format_out

        if crop_rect:
            rect = namedtuple('rect', 'xs ys xe ye')
            self.crop_rect = rect(*crop_rect)

        self.yy = None
        self.cb = None
        self.cr = None

        # Reader/Writer
        RW = {
            'YV12': YV12,
            'IYUV': IYUV,
            'NV12': NV12,
            'UYVY': UYVY,
            'YVYU': YVYU,
            'YUY2': YUY2,
            '422': Y422,
        }

        # Setup
        if self.yuv_format_in:  # we need a reader and and a writer just
                                # to make sure
            self.reader = RW[self.yuv_format_in](self.width, self.height)
            self.writer = RW[self.yuv_format_in](self.width, self.height)
            self.frame_size_in = self.reader.get_frame_size()
            self.frame_size_out = self.reader.get_frame_size()

            # If file-sizes differ, just process the smaller ammount of frames
            n1 = os.path.getsize(self.filename) / self.frame_size_in
            n2 = n1
            if self.filename_diff:
                n2 = os.path.getsize(self.filename_diff) / self.frame_size_in

            self.num_frames = min(n1, n2)

            self.layout_in = self.reader.get_layout()
            self.layout_out = self.reader.get_layout()
            self.frame_size_out = self.frame_size_in
            self.chroma_div = self.reader.chroma_div

        if self.yuv_format_out:
            self.writer = RW[self.yuv_format_out](self.width, self.height)
            self.frame_size_out = self.writer.get_frame_size()
            self.layout_out = self.writer.get_layout()

        # 8bpp -> 10bpp, 10->8 dito; special handling
        if yuv_format_in is not None:
            self.__check()


        # How many frames to process
        if num:
            if num <= self.num_frames:
                self.num_frames = num

    def psnr(self):

        def psnr(a, b):
            m = ((a - b) ** 2).mean()
            if m == 0:
                return float("nan")

            return 10 * np.log10(255 ** 2 / m)


        yy = []; cb = []; cr = []; bd = []

        with open(self.filename, 'rb') as fd_1, \
                open(self.filename_diff, 'rb') as fd_2:
            for i in xrange(self.num_frames):
                self.__read_frame(fd_1)
                frame1 = self.__copy_planes()[:-1]    # skip whole frame
                self.__read_frame(fd_2)
                frame2 = self.__copy_planes()[:-1]    # skip whole frame


                zeros = np.array([0] * 311040)
                if not (frame2[0].all() == zeros.all()): 
                    yy.append(psnr(frame1[0], frame2[0]))
                    cb.append(psnr(frame1[1], frame2[1]))
                    cr.append(psnr(frame1[2], frame2[2]))
                    bd.append((6 * yy[-1] + cb[-1] + cr[-1]) / 8.0)


            yield [sum(yy)/len(yy), sum(cb)/len(cb), sum(cr)/len(cr), sum(bd)/len(bd)]
            

    def __check(self):
        """
        Basic consistency checks to prevent fumbly-fingers
        - width & height even multiples of 16
        - number of frames divides file-size evenly
        - for diff-cmd, file-sizes match
        """

        if self.width & 0xF != 0:
            print >> sys.stderr, "[WARNING] - width not divisable by 16"
        if self.height & 0xF != 0:
            print >> sys.stderr, "[WARNING] - hight not divisable by 16"

        size = os.path.getsize(self.filename)
        if not self.num_frames == size / float(self.frame_size_in):
            print >> sys.stderr, "[WARNING] - # frames not integer"

        if self.filename_diff:
            size_diff = os.path.getsize(self.filename_diff)
            ### if not size == size_diff:
            ###     print >> sys.stderr, "[WARNING] - file-sizes are not equal"
                
    def __read_frame(self, fd):
        """
        Use extended indexing to read 1 frame into self.{y, cb, cr}
        """
        self.raw = np.fromfile(fd, dtype=np.uint8, count=self.frame_size_in)
        self.raw = self.raw.astype(np.int, copy=False)

        self.yy = self.raw[self.layout_in[0]]
        self.cb = self.raw[self.layout_in[1]]
        self.cr = self.raw[self.layout_in[2]]

    def __copy_planes(self):
        """
        Return a copy of the different color planes,
        including whole frame
        """
        return self.yy.copy(), self.cb.copy(), self.cr.copy(), self.raw.copy()



def main():
    # Helper functions

    def __cmd_psnr(arg):
        yuv = YCbCr(**vars(arg))

        x = (i for i in yuv.psnr())

        for i, n in enumerate(x):
            try:
                print "PSNR(Y)=         {:<10f}".format(*n)
                print "PSNR(Y,U,V)=     ( {:<10f}, {:<10f}, {:<10f})".format(*n)
            except ValueError:
                print "Fallo"
        
    parser = argparse.ArgumentParser(
        description='YCbCr tools',
        epilog=' Be careful with those bits')
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('filename', type=str, help='filename')
    parent_parser.add_argument('width', type=int)
    parent_parser.add_argument('height', type=int)
    parent_parser.add_argument(
        'yuv_format_in', type=str,
        choices=['IYUV', 'UYVY', 'YV12', 'NV12', 'YVYU', 'YUY2', '422'],
        help='valid input-formats')
    parent_parser.add_argument(
        '--num',
        type=int,
        default=None,
        help='number of frames to process [0..n-1]')
    parent_parser.add_argument('filename_diff', type=str, help='filename')

    args = parent_parser.parse_args()
    
    #t1 = time.clock()
    __cmd_psnr(args)
    #t2 = time.clock()
    
    #print ""
    #print "Time:        ", round(t2 - t1, 4)

if __name__ == '__main__':
    main()
