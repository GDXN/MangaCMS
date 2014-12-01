
import matplotlib
matplotlib.use('Agg')

import traceback
import cv2
import numpy as np
from matplotlib import pyplot as plt

import os
import os.path

BORDER_SIZE = 32

def filter_matches(kp1, kp2, matches, ratio = 0.5):
	mkp1, mkp2 = [], []
	for m in matches:
		if len(m) == 2 and m[0].distance < m[1].distance * ratio:
			m = m[0]
			mkp1.append( kp1[m.queryIdx] )
			mkp2.append( kp2[m.trainIdx] )
	p1 = np.float32([kp.pt for kp in mkp1])
	p2 = np.float32([kp.pt for kp in mkp2])
	kp_pairs = zip(mkp1, mkp2)
	return p1, p2, kp_pairs

def insertBorder(img, border=32):
	return cv2.copyMakeBorder(img, border, border, border, border, borderType=cv2.BORDER_CONSTANT, value=255)

def filterArrRows(inarr, rows):
	for row in rows:
		inarr = np.delete(inarr, row, 0)
	return inarr

def drawX(img, cx, cy, color):
	p1, p2, p3, p4 = tuple([int(cx+10), int(cy+10)]), tuple([int(cx-10), int(cy-10)]), tuple([int(cx+10), int(cy-10)]), tuple([int(cx-10), int(cy+10)])

	img = cv2.line(img=img,
			pt1=p1,
			pt2=p2,
			color=color,
			thickness=1)

	img = cv2.line(img=img,
			pt1=p3,
			pt2=p4,
			color=color,
			thickness=1,
			lineType=cv2.LINE_AA)

	return img


def go():


	testIn = "./tests/"
	inIms = os.listdir(testIn)
	testOut = './out/'


	tmpOut = os.listdir(testOut)
	for fn in tmpOut:
		fqIm = os.path.join(testOut, fn)
		print(fqIm, os.path.isfile(fqIm))
		if os.path.isfile(fqIm):
			os.unlink(fqIm)

	# sorb = cv2.ORB_create()
	# borb = cv2.ORB_create(nfeatures=25000)

	# sorb = cv2.BRISK_create()
	# borb = cv2.BRISK_create()

	sorb = cv2.AKAZE_create(nOctaves=1)
	borb = cv2.AKAZE_create(nOctaves=1)


	template = cv2.imread('bw_watermark-r.png', 0)
	template = insertBorder(template, border=BORDER_SIZE)
	kp1, des1 = sorb.detectAndCompute(template, None)
	bf = cv2.BFMatcher(cv2.NORM_HAMMING)

	# TODO: Switch to estimateRigidTransform for matching, since we don't need all the additional dimentions.

	for inIm in inIms:
		fqIm = os.path.join(testIn, inIm)
		print(fqIm)
		try:
			target = cv2.imread(fqIm, 0)
			target = insertBorder(target, border=BORDER_SIZE)
			kp2, des2 = borb.detectAndCompute(target, None)



			raw_matches = bf.match(des1,des2)
			raw_matches = bf.knnMatch(des1, des2, k=2)


			good = []
			for item in raw_matches:
				if len(item) != 2:
					continue
				m,n = item
				if m.distance < 0.7*n.distance:
					good.append(m)

			if len(good)>10:
				src_pts = np.float32([ kp1[m.queryIdx].pt for m in good ]).reshape(-1,1,2)
				dst_pts = np.float32([ kp2[m.trainIdx].pt for m in good ]).reshape(-1,1,2)

				M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC,3.0)
				if mask == None:
					print("Wat?")
					continue
				matchesMask = mask.ravel().tolist()

				ind = [i for i, x in enumerate(matchesMask) if x == 0]
				ind.sort(reverse=True)

				src_filt = filterArrRows(src_pts, ind)
				dst_filt = filterArrRows(dst_pts, ind)



				ret = cv2.estimateRigidTransform(src_filt, dst_filt, fullAffine=False)

				h,w = template.shape
				# pts = np.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2)
				# dst = cv2.perspectiveTransform(pts,M)

				# cx = np.mean(dst[...,0])
				# cy = np.mean(dst[...,1])

				ret = ret.ravel()
				wS, hS = ret[0], ret[4]
				rotA, rotB = ret[1], ret[3]
				tX, tY = ret[2], ret[5]

				errs = [abs(1-wS), abs(1-hS), abs(rotA), abs(rotB)]

				print(errs)

				aX, aY = tX+(w/2), tY+(h/2)
				print(aX, aY)

				# eX, eY = aX - cx, aY - cy
				print("Filtered: ", ind)
				# print("Rigid Transform error:", eX, eY)

				target = cv2.cvtColor(target, cv2.COLOR_GRAY2RGB)

				# target = drawX(target, cx, cy, (0, 0, 255))
				target = drawX(target, aX, aY, (255, 0, 0))

				# target = cv2.polylines(img=target,
				# 		pts=[np.int32(dst)],
				# 		isClosed=True,
				# 		color=(0, 0, 255),
				# 		thickness=3,
				# 		lineType=cv2.LINE_AA)
				# img, pts, isClosed, color[, thickness[, lineType[, shift]]])

				draw_params = dict(matchesMask = matchesMask, # draw only inliers
								   flags = 2)

				# img3 = cv2.drawMatches(template,kp1,target,kp2,good,None,**draw_params)

				plt.imshow(target)


				outName = 'myfig_{inIm}.png'.format(inIm=inIm)
				outName = os.path.join(testOut, outName)
				plt.savefig(outName, dpi=300)

				print("OK Match?")

			else:
				print("No Match?")

			# p1, p2, kp_pairs = filter_matches(kp1, kp2, raw_matches)
			# print(p1)
			# print(p2)

			# retIm = np.array([])
			# img3 = cv2.drawMatches(template,kp1,target,kp2,matches[:50], retIm, flags=2)


			# cv2.findHomography

			# # img2 = template.copy()
			# # img2 = cv2.drawKeypoints(template, kp, img2)
			# # plt.imshow(img2, cmap='gray')
			# # plt.savefig('test.png', dpi=300)

			# plt.imshow(img3)
			# outName = 'myfig_{inIm}.png'.format(inIm=inIm)
			# outName = os.path.join(testOut, outName)
			# plt.savefig(outName, dpi=300)


		except KeyboardInterrupt:
			raise
		except:
			print("Wat?")
			traceback.print_exc()

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

