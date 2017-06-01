plt.figure(None,figsize=(12,12))
plt.imshow(warped)
plt.plot(destination[:,0],destination[:,1],'r.',markersize=5)
plt.show()

rock_min_thresh = (155, 0, 0)
rock_max_thresh = (255, 255, 117)
obst_min_thresh = (120, 120, 120)
obst_max_thresh = (255,255,255)
path_min_thresh = (0, 0, 0)
path_max_thresh = obst_min_thresh

threshed = np.zeros_like(warped)
threshed[:,:,0] = color_thresh(warped, rock_min_thresh, rock_max_thresh)
threshed[:,:,1] = color_thresh(warped, obst_min_thresh, obst_max_thresh)
threshed[:,:,2] = color_thresh(warped, path_min_thresh, path_max_thresh)

plt.imshow(threshed * 255)

plt.show()