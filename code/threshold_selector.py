import cv2 # OpenCV for perspective transform
import numpy as np
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import scipy.misc # For saving images as needed
import glob  # For reading in a list of images from a folder


def nothing(x):
    pass


# example = '../calibration_images/example_grid1.jpg'
example = '../calibration_images/example_rock1.jpg'
image = mpimg.imread(example)


# Define a function to perform a perspective transform
# I've used the example grid image above to choose source points for the
# grid cell in front of the rover (each grid cell is 1 square meter in the sim)
# Define a function to perform a perspective transform
def perspect_transform(img, src, dst):
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (img.shape[1], img.shape[0]))  # keep same size as input image

    return warped


def color_thresh(img, rgb_min_thresh=(0, 0, 0),rgb_max_thresh=(255, 255, 255)):
    # Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    above_thresh = (img[:,:,0] > rgb_min_thresh[0]) \
                & (img[:,:,1] > rgb_min_thresh[1]) \
                & (img[:,:,2] > rgb_min_thresh[2]) \
                & (img[:,:,0] < rgb_max_thresh[0]) \
                & (img[:,:,1] < rgb_max_thresh[1]) \
                & (img[:,:,2] < rgb_max_thresh[2])


    # Index the array of zeros with the boolean array and set to 1
    color_select[above_thresh] = 1
    # Return the binary image
    return color_select

# Define calibration box in source (actual) and destination (desired) coordinates
# These source and destination points are defined to warp the image
# to a grid where each 10x10 pixel square represents 1 square meter
# The destination box will be 2*dst_size on each side
dst_size = 5
# Set a bottom offset to account for the fact that the bottom of the image
# is not the position of the rover but a bit in front of it
# this is just a rough guess, feel free to change it!
bottom_offset = 6
source = np.float32([[14, 140], [301, 140], [200, 96], [118, 96]])
destination = np.float32([[image.shape[1] / 2 - dst_size, image.shape[0] - bottom_offset],
                          [image.shape[1] / 2 + dst_size, image.shape[0] - bottom_offset],
                          [image.shape[1] / 2 + dst_size, image.shape[0] - 2 * dst_size - bottom_offset],
                          [image.shape[1] / 2 - dst_size, image.shape[0] - 2 * dst_size - bottom_offset],
                          ])
warped = perspect_transform(image, source, destination)

cv2.namedWindow('image')

# create trackbars for color change
cv2.createTrackbar('R-min', 'image', 0, 255, nothing)
cv2.createTrackbar('G-min', 'image', 0, 255, nothing)
cv2.createTrackbar('B-min', 'image', 0, 255, nothing)

cv2.createTrackbar('R-max', 'image', 0, 255, nothing)
cv2.createTrackbar('G-max', 'image', 0, 255, nothing)
cv2.createTrackbar('B-max', 'image', 0, 255, nothing)

threshed = color_thresh(warped, (0,0,0), (255,255,255))

plt.show()

while (1):
    cv2.imshow('image', threshed*255)
    k = cv2.waitKey(1) & 0xFF
    if k == 27:
        break

    # get current positions of four trackbars
    rmin = cv2.getTrackbarPos('R-min', 'image')
    gmin = cv2.getTrackbarPos('G-min', 'image')
    bmin = cv2.getTrackbarPos('B-min', 'image')

    rmax = cv2.getTrackbarPos('R-max', 'image')
    gmax = cv2.getTrackbarPos('G-max', 'image')
    bmax = cv2.getTrackbarPos('B-max', 'image')

    print((rmin, gmin, bmin),(rmax, gmax, bmax))

    threshed = color_thresh(warped, rgb_min_thresh=(rmin, gmin, bmin),rgb_max_thresh=(rmax, gmax, bmax))

cv2.destroyAllWindows()
