import numpy as np
import cv2

# Identify pixels above the threshold
# Threshold of RGB > 160 does a nice job of identifying ground pixels only
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

# Define a function to convert to rover-centric coordinates
def rover_coords(binary_img):
    # Identify nonzero pixels
    ypos, xpos = binary_img.nonzero()
    # Calculate pixel positions with reference to the rover position being at the 
    # center bottom of the image.  
    x_pixel = np.absolute(ypos - binary_img.shape[0]).astype(np.float)
    y_pixel = -(xpos - binary_img.shape[0]).astype(np.float)
    return x_pixel, y_pixel


# Define a function to convert to radial coords in rover space
def to_polar_coords(x_pixel, y_pixel):
    # Convert (x_pixel, y_pixel) to (distance, angle) 
    # in polar coordinates in rover space
    # Calculate distance to each pixel
    dist = np.sqrt(x_pixel**2 + y_pixel**2)
    # Calculate angle away from vertical for each pixel
    angles = np.arctan2(y_pixel, x_pixel)
    return dist, angles

# Define a function to apply a rotation to pixel positions
def rotate_pix(xpix, ypix, yaw):
    # Convert yaw to radians
    # Apply a rotation
    yaw_rad = yaw * np.pi / 180
    xpix_rotated = xpix * np.cos(yaw_rad) - ypix * np.sin(yaw_rad)
    ypix_rotated = xpix * np.sin(yaw_rad) + ypix * np.cos(yaw_rad)
    # Return the result  
    return xpix_rotated, ypix_rotated

# Define a function to perform a translation
def translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale): 
    # TODO:
    # Apply a scaling and a translation
    xpix_translated = np.int_(xpos + (xpix_rot / scale))
    ypix_translated = np.int_(ypos + (ypix_rot / scale))
    # Return the result  
    return xpix_translated, ypix_translated

# Define a function to apply rotation and translation (and clipping)
# Once you define the two functions above this function should work
def pix_to_world(xpix, ypix, xpos, ypos, yaw, world_size, scale):
    # Apply rotation
    xpix_rot, ypix_rot = rotate_pix(xpix, ypix, yaw)
    # Apply translation
    xpix_tran, ypix_tran = translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale)
    # Perform rotation, translation and clipping all at once
    x_pix_world = np.clip(np.int_(xpix_tran), 0, world_size - 1)
    y_pix_world = np.clip(np.int_(ypix_tran), 0, world_size - 1)
    # Return the result
    return x_pix_world, y_pix_world

# Define a function to perform a perspective transform
def perspect_transform(img, src, dst):
           
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (img.shape[1], img.shape[0]))# keep same size as input image
    
    return warped


# Apply the above functions in succession and update the Rover state accordingly
def perception_step(Rover):
    # Perform perception steps to update Rover()
    # TODO: 
    # NOTE: camera image is coming to you in Rover.img
    # 1) Define source and destination points for perspective transform
    image = Rover.img
    xpos, ypos = Rover.pos
    yaw = Rover.yaw

    dst_size = 5
    bottom_offset = 6
    src = np.float32([[14, 140], [301, 140], [200, 96], [118, 96]])
    dst = np.float32([[image.shape[1] / 2 - dst_size, image.shape[0] - bottom_offset],
                              [image.shape[1] / 2 + dst_size, image.shape[0] - bottom_offset],
                              [image.shape[1] / 2 + dst_size, image.shape[0] - 2 * dst_size - bottom_offset],
                              [image.shape[1] / 2 - dst_size, image.shape[0] - 2 * dst_size - bottom_offset],
                              ])
    # 2) Apply perspective transform
    warped = perspect_transform(image, src, dst)
    # 3) Apply color threshold to identify navigable terrain/obstacles/rock samples
    rock_min_thresh = (155, 0, 0)
    rock_max_thresh = (255, 255, 117)
    path_min_thresh = (120, 120, 120)
    path_max_thresh = (255,255,255)
    obst_min_thresh = (0, 0, 0)
    obst_max_thresh = path_min_thresh
    
    threshed_rock = color_thresh(warped, rock_min_thresh, rock_max_thresh)
    threshed_obst = color_thresh(warped, obst_min_thresh, obst_max_thresh)
    threshed_path = color_thresh(warped, path_min_thresh, path_max_thresh)
    
    # 4) Update Rover.vision_image (this will be displayed on left side of screen)
    Rover.vision_image[:,:,0] = threshed_obst * 255
    Rover.vision_image[:,:,1] = threshed_rock * 255
    Rover.vision_image[:,:,2] = threshed_path * 255
    
    # 5) Convert map image pixel values to rover-centric coords
    xrov_path, yrov_path = rover_coords(threshed_path)
    xrov_obst, yrov_obst = rover_coords(threshed_obst)
    xrov_rock, yrov_rock = rover_coords(threshed_rock)

    # 6) Convert rover-centric pixel values to world coordinates
    x_world_path, y_world_path = pix_to_world(xrov_path, 
                                                yrov_path, 
                                                xpos,
                                                ypos,
                                                yaw, 200, 10)
    
    x_world_obst, y_world_obst = pix_to_world(xrov_obst, 
                                                yrov_obst,  
                                                xpos,
                                                ypos,
                                                yaw, 200, 10)
        
    x_world_rock, y_world_rock = pix_to_world(xrov_rock, 
                                                yrov_rock, 
                                                xpos,
                                                ypos,
                                                yaw, 200, 10)

    # 7) Update Rover worldmap (to be displayed on right side of screen)
    Rover.worldmap[y_world_obst, x_world_obst, 0] += 2
    Rover.worldmap[y_world_rock, x_world_rock, 1] += 255
    Rover.worldmap[y_world_path, x_world_path, 2] += 2

    # 8) Convert rover-centric pixel positions to polar coordinates
    Rover.nav_dists, Rover.nav_angles = to_polar_coords(xrov_path, yrov_path)
    
    return Rover