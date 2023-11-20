from tkinter import *
from tkinter import messagebox
import tkinter.filedialog as tk
import fitz
import timeit,os,numpy
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from sys import platform
from os.path import isfile, join
from os import listdir
import re
import math
import cv2

global tempdir, diffdir

tempdir = 'D:/code_projects/python/diff-dwg/uploads/'
# tempdir = 'D:/code_projects/python/diff-dwg/img/'
diffdir = 'D:/code_projects/python/diff-dwg/diff'

#Anaglyph matrices
_magic = [0.299, 0.587, 0.114]
_zero = [0, 0, 0]
_ident = [[1, 0, 0],
          [0, 1, 0],
          [0, 0, 1]]

true_anaglyph = ([_magic, _zero, _zero], [_zero, _zero, _magic])
gray_anaglyph = ([_magic, _zero, _zero], [_zero, _magic, _magic])
color_anaglyph = ([_ident[0], _zero, _zero], [_zero, _ident[1], _ident[2]])
color2_anaglyph = ([[1, 0, 0],[0,0,0],[0,0,0.603922]],[[0,0,0],[0,1,0],[0,0,0.396078]])
half_color_anaglyph = ([_magic, _zero, _zero], [_zero, _ident[1], _ident[2]])
optimized_anaglyph = ([[0, 0.7, 0.3], _zero, _zero], [_zero, _ident[1], _ident[2]])
methods = [true_anaglyph, gray_anaglyph, color_anaglyph, half_color_anaglyph, optimized_anaglyph]

def pdf2png(pdf,temp):
    #Generate the path for the png file. Need to use a temp directory in case
    #pdf location is read only.
    pdf = str(pdf)
    base = os.path.basename(pdf)
    basefile = os.path.splitext(base)
    png = temp + basefile[0] + ".png"
    png = str(png)
    pdf = str(pdf)
    #print(pdf)
    #print(png)
    doc = fitz.open(pdf)
    xres=2
    yres=2
    mat= fitz.Matrix(xres,yres)
    for page in doc:
        # pix = page.getPixmap(matrix=mat, colorspace="rgb", alpha = False)
        pix = page.get_pixmap(matrix=mat, colorspace="rgb", alpha = False)
        # pix.writePNG(png)
        pix._writeIMG("output.png", 1, 100)
    return png

def anaglyph(image1, image2, method=true_anaglyph):
    m1, m2 = [numpy.array(m).transpose() for m in method]
    im1, im2 = image_to_array(image1), image_to_array(image2)
    composite = numpy.dot(im1, m1) + numpy.dot(im2, m2)
    result = array_to_image(image1.mode, image1.size, composite)
    return result

def image_to_array(im):
    s = im.tobytes()
    dim = len(im.getbands())
    return numpy.frombuffer(s, numpy.uint8).reshape(len(s)//dim, dim)

def array_to_image(mode, size, a):
    return Image.frombytes(mode, size, a.reshape(len(a)*len(mode), 1).astype(numpy.uint8).tostring())

def watermark_text(input_image_path,
                   output_image_path,
                   text, pos):
    photo = Image.open(input_image_path)
    drawing = ImageDraw.Draw(photo)
    red = (255, 0, 0)
    if platform == "win32":
        font = ImageFont.truetype("C:\\Windows\\Fonts\\Calibri.ttf", 30)
    else:
        font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMono.ttf", 30)
    drawing.text(pos, text, fill=red, font=font)
    photo.save(output_image_path)

def find_char(find_s,find_c):
    i=0
    j=0
    k=len(find_s)
    for c in find_s:
        if c == find_c:
            j=i
        i=i+1
    trim=k-j
    if trim == k:
        trim = -1
    else:
        trim = trim+1
    return trim

def alignimage(align1,align2):
    img1 = cv2.imread(align1)
    img2 = cv2.imread(align2)

    #Find the corner points of img1
    h1,w1,c=img1.shape
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray1 = numpy.float32(gray1)
    dst1 = cv2.cornerHarris(gray1,5,3,0.04)
    ret1, dst1 = cv2.threshold(dst1,0.1*dst1.max(),255,0)
    dst1 = numpy.uint8(dst1)
    ret1, labels1, stats1, centroids1 = cv2.connectedComponentsWithStats(dst1)
    criteria1 = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.001)
    corners1 = cv2.cornerSubPix(gray1,numpy.float32(centroids1),(5,5),(-1,-1),criteria1)

    #Find the corner points of img2
    h2,w2,c=img2.shape
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    gray2 = numpy.float32(gray2)
    dst2 = cv2.cornerHarris(gray2,5,3,0.04)
    ret2, dst2 = cv2.threshold(dst2,0.1*dst2.max(),255,0)
    dst2 = numpy.uint8(dst2)
    ret2, labels2, stats2, centroids2 = cv2.connectedComponentsWithStats(dst2)
    criteria2 = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.001)
    corners2 = cv2.cornerSubPix(gray2,numpy.float32(centroids2),(5,5),(-1,-1),criteria2)


    #Find the top left, top right, and bottom left outer corners of the drawing frame for img1
    a1=[0,0]
    b1=[w1,0]
    c1=[0,h1]
    a1_dist=[]
    b1_dist=[]
    c1_dist=[]
    for i in corners1:
        temp_a1=math.sqrt((i[0]-a1[0])**2+(i[1]-a1[1])**2)
        temp_b1=math.sqrt((i[0]-b1[0])**2+(i[1]-b1[1])**2)
        temp_c1=math.sqrt((i[0]-c1[0])**2+(i[1]-c1[1])**2)
        a1_dist.append(temp_a1)
        b1_dist.append(temp_b1)
        c1_dist.append(temp_c1)

    #print("Image #1 (reference):")
    #print("Top Left:")
    #print(corners1[a1_dist.index(min(a1_dist))])
    #print("Top Right:")
    #print(corners1[b1_dist.index(min(b1_dist))])
    #print("Bottom Left:")
    #print(corners1[c1_dist.index(min(c1_dist))])

    #Find the top left, top right, and bottom left outer corners of the drawing frame for img2
    a2=[0,0]
    b2=[w2,0]
    c2=[0,h2]
    a2_dist=[]
    b2_dist=[]
    c2_dist=[]
    for i in corners2:
        temp_a2=math.sqrt((i[0]-a2[0])**2+(i[1]-a2[1])**2)
        temp_b2=math.sqrt((i[0]-b2[0])**2+(i[1]-b2[1])**2)
        temp_c2=math.sqrt((i[0]-c2[0])**2+(i[1]-c2[1])**2)
        a2_dist.append(temp_a2)
        b2_dist.append(temp_b2)
        c2_dist.append(temp_c2)

    #print("Image #2 (image to align):")
    #print("Top Left:")
    #print(corners2[a2_dist.index(min(a2_dist))])
    #print("Top Right:")
    #print(corners2[b2_dist.index(min(b2_dist))])
    #print("Bottom Left:")
    #print(corners2[c2_dist.index(min(c2_dist))])

    #Create the points for img1
    point1 = numpy.zeros((3,2), dtype=numpy.float32)
    point1[0][0]=corners1[a1_dist.index(min(a1_dist))][0]
    point1[0][1]=corners1[a1_dist.index(min(a1_dist))][1]
    point1[1][0]=corners1[b1_dist.index(min(b1_dist))][0]
    point1[1][1]=corners1[b1_dist.index(min(b1_dist))][1]
    point1[2][0]=corners1[c1_dist.index(min(c1_dist))][0]
    point1[2][1]=corners1[c1_dist.index(min(c1_dist))][1]

    #Create the points for img2
    point2 = numpy.zeros((3,2), dtype=numpy.float32)
    point2[0][0]=corners2[a2_dist.index(min(a2_dist))][0]
    point2[0][1]=corners2[a2_dist.index(min(a2_dist))][1]
    point2[1][0]=corners2[b2_dist.index(min(b2_dist))][0]
    point2[1][1]=corners2[b2_dist.index(min(b2_dist))][1]
    point2[2][0]=corners2[c2_dist.index(min(c2_dist))][0]
    point2[2][1]=corners2[c2_dist.index(min(c2_dist))][1]

    #Make sure points look ok:
    #print(point1)
    #print(point2)

    #Transform the image
    m = cv2.getAffineTransform(point2,point1)
    image2Reg = cv2.warpAffine(img2, m, (w1, h1), borderValue=(255,255,255))

    #Highlight found points in red:
    #img1[dst1>0.1*dst1.max()]=[0,0,255]
    #img2[dst2>0.1*dst2.max()]=[0,0,255]

    #Output the images:
    cv2.imwrite(align1, img1)
    #cv2.imwrite("output-img2-harris.jpg", img2)
    cv2.imwrite(align2,image2Reg)
    print("Images aligned successfully")
    return align1, align2

def process_images(p1, p2):
    global filePath1, filePath2, v, check, size_check
    filePath1 = p1
    filePath2 = p2
    start = timeit.default_timer()
    img1_file = pdf2png(filePath1, tempdir)
    img2_file = pdf2png(filePath2, tempdir)
    
    
    # return
    align1, align2 = alignimage(img1_file, img2_file)
    im1, im2 = Image.open(align2), Image.open(align1)
    # im1, im2 = Image.open(img2_file), Image.open(img1_file)
    # if check.get() == 1:
    #     align1, align2 = alignimage(img1_file, img2_file)
    #     im1, im2 = Image.open(align2), Image.open(align1)
    # else:
    #     im1, im2 = Image.open(img2_file), Image.open(img1_file)

    file_string = os.path.splitext(os.path.basename(filePath1))[0] + "-diff.png"
    dispimg = diffdir + "\\\\" + file_string
    waterimg = diffdir + "\\\\" + file_string
        # if platform == "win32":
        #     dispimg = diffdir + "\\\\" + file_string
        #     waterimg = diffdir + "\\\\" + file_string
        # else:
        #     dispimg = diffdir + "/" + file_string
        #     waterimg = diffdir + "/" + file_string
    anaglyph(im1, im2, color2_anaglyph).save(dispimg, quality=90)
    # watermark_text(dispimg,waterimg,"UNCONTROLLED COPY",pos=(0, 0))
    
    if im1.size[0] == im2.size[0] and im1.size[1] == im2.size[1]:
        print("Drawing sizes match")
        dispimg = diffdir + "\\\\" + file_string
        waterimg = diffdir + "\\\\" + file_string
        # if platform == "win32":
        #     dispimg = diffdir + "\\\\" + file_string
        #     waterimg = diffdir + "\\\\" + file_string
        # else:
        #     dispimg = diffdir + "/" + file_string
        #     waterimg = diffdir + "/" + file_string
        anaglyph(im1, im2, color2_anaglyph).save(dispimg, quality=90)
        # watermark_text(dispimg,waterimg,"UNCONTROLLED COPY",pos=(0, 0))
    else:
        print("Drawing size mismatch.")
        size_check = 1
    del im1,im2
    # os.remove(img1_file)
    # os.remove(img2_file)
    stop = timeit.default_timer()
    print("Run time was", stop - start)
    print("Done")
   
def main():
    print("Hello, World!")
    # process_images()


main()
