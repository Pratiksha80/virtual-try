import cv2
import numpy as np
from PIL import Image

# Load person & clothing
person = cv2.imread("person.jpg")
clothes = cv2.imread("tshirt.png", cv2.IMREAD_UNCHANGED)  # has alpha channel

# Example: map clothing corners to person shoulder points
src_points = np.float32([[0,0], [clothes.shape[1],0], [0,clothes.shape[0]], [clothes.shape[1],clothes.shape[0]]])
dst_points = np.float32([[100,150], [300,150], [120,400], [280,400]])  # shoulders & waist

matrix = cv2.getPerspectiveTransform(src_points, dst_points)
warped = cv2.warpPerspective(clothes, matrix, (person.shape[1], person.shape[0]))

# Overlay
alpha = warped[:,:,3] / 255.0
for c in range(0,3):
    person[:,:,c] = person[:,:,c] * (1-alpha) + warped[:,:,c] * alpha

cv2.imshow("Virtual Try-On", person)
cv2.waitKey(0)
