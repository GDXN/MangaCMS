
import matplotlib
matplotlib.use('Agg')

import traceback
import cv2
import numpy as np
from matplotlib import pyplot as plt

import os
import os.path

def go():


	testIn = "./tests/"
	inIms = os.listdir(testIn)
	testOut = './out/'

	sorb = cv2.ORB_create()
	borb = cv2.ORB_create(nfeatures=25000)


	template = cv2.imread('bw_watermark.png', 0)
	kp1, des1 = sorb.detectAndCompute(template, None)
	bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)


	for inIm in inIms:
		fqIm = os.path.join(testIn, inIm)
		print(fqIm)
		try:
			target = cv2.imread(fqIm, 0)
			kp2, des2 = borb.detectAndCompute(target, None)


			matches = bf.match(des1,des2)
			matches = sorted(matches, key = lambda x:x.distance)


			retIm = np.array([])
			img3 = cv2.drawMatches(template,kp1,target,kp2,matches[:50], retIm, flags=2)

			# img2 = template.copy()
			# img2 = cv2.drawKeypoints(template, kp, img2)
			# plt.imshow(img2, cmap='gray')
			# plt.savefig('test.png', dpi=300)

			plt.imshow(img3)
			outName = 'myfig_{inIm}.png'.format(inIm=inIm)
			outName = os.path.join(testOut, outName)
			plt.savefig(outName, dpi=300)
		except:
			print("Wat?")
			# traceback.print_exc()

	# print("Array shape", template.shape[::-1])
	# d, w, h = template.shape[::-1]


	# kp1, des1 = sift.detectAndCompute(template,None)

	# for inIm in inIms:
	# 	fqIm = os.path.join(testIn, inIm)
	# 	print(fqIm)
	# 	baseIm = cv2.imread(fqIm, -1)

	# 	methods = ['cv2.TM_CCOEFF_NORMED']

	# 	for meth in methods:
	# 		img = baseIm.copy()

	# 		method = eval(meth)

	# 		# Apply template Matching
	# 		res = cv2.matchTemplate(baseIm, template, method)
	# 		min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

	# 		# If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
	# 		if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
	# 			top_left = min_loc
	# 		else:
	# 			top_left = max_loc
	# 		bottom_right = (top_left[0] + w, top_left[1] + h)

	# 		cv2.rectangle(img, top_left, bottom_right, 255, 2)

	# 		plt.subplot(121)
	# 		plt.imshow(res, cmap='gray')
	# 		plt.title('Matching Result')
	# 		plt.xticks([])
	# 		plt.yticks([])
	# 		plt.subplot(122)
	# 		plt.imshow(img, cmap='gray')
	# 		plt.title('Detected Point'), plt.xticks([]), plt.yticks([])


	# 		if max_val > 0.36:
	# 			state = 'Ok'
	# 		else:
	# 			state = 'Fail'

	# 		plt.suptitle('{meth}, {min_val}, {max_val}, {state}'.format(meth=meth, min_val=min_val, max_val=max_val, state=state))
	# 		outName = 'myfig_{inIm}_{meth}.png'.format(inIm=inIm, meth=meth)
	# 		outName = os.path.join(testOut, outName)
	# 		plt.savefig(outName, dpi=300)





if __name__ == "__main__":
	go()

