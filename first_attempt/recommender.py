from __future__ import division
import numpy as np
import os
from math import sqrt
import similar
import csv
import operator
from sys import argv

f = open("ratings.csv")
ratings_data = csv.reader(f)
list_data = list(ratings_data)

f1 = open("toBeRated.csv")
test = csv.reader(f1)
test_data = list(test)

userratings = {}
users = sorted(list_data, key = operator.itemgetter(0))

count = 0
u_prev = 0
'''
	mapping users and movies to ratings
'''
for u in users:
	userid = u[0]
	movieid = u[1]
	movieratings = u[2]
	if u_prev == userid:
		userratings[userid][movieid] = movieratings
		u_prev = userid
	else:
		userratings[userid] = {}
		userratings[userid][movieid] = movieratings
		u_prev = userid
#print userratings

def transposeratings(ratings):
	transposed = {}
	for user in ratings:
		for item in ratings[user]:
			transposed.setdefault(item,{})
			transposed[item][user] = ratings[user][item]
	return transposed

# now to check for similar users
def sim_cosine(ratings, user_1, user_2):
	similarity = {}
	for item in ratings[user_1]:
		if item in ratings[user_2]:
			similarity[item] = 1

	numSim =len(similarity)

	if numSim == 0:
		return 0

	userOneRatingsArray = ([ratings[user_1][s] for s in similarity])
	userOneRatingsArray = map(int, userOneRatingsArray)
	userTwoRatingsArray = ([ratings[user_2][s] for s in similarity])
	userTwoRatingsArray = map(int, userTwoRatingsArray)
	

	sum_xx, sum_yy, sum_xy = 0,0,0

	for i in range(len(userOneRatingsArray)):
		x = userOneRatingsArray[i]
		y = userTwoRatingsArray[i]

		sum_xx += x*x
		sum_yy += y*y
		sum_xy += x*y

	return sum_xy/sqrt(sum_xx*sum_yy)

def sim_pearson(ratings, user_1, user_2):
	similarity = {}
	for item in ratings[user_1]:
		if item in ratings[user_2]:
			similarity[item] = 1

	#calculate the number of similarities 
	numSim = len(similarity)

	# If there is no similarity between them, return 0
	if numSim == 0:
		return 0

	# Add the ratings from users
	userOneSimArray = ([ratings[user_1][s] for s in similarity])
	userOneSimArray = map(int, userOneSimArray)

	sum_1 = sum(userOneSimArray)

	userTwoSimArray = ([ratings[user_2][s] for s in similarity])
	userTwoSimArray = map(int, userTwoSimArray)

	sum_2 = sum(userTwoSimArray)

	# Sum up the squares 

	sum_1_sq = sum([pow(int(ratings[user_1][item]),2) for item in similarity])
	sum_2_sq = sum([pow(int(ratings[user_2][item]),2) for item in similarity])

	# Sum of the products
	productSum = sum([int(ratings[user_1][item]) * int(ratings[user_2][item]) for item in similarity])
	num = productSum - (sum_1*sum_2/numSim)
	den = math.sqrt((sum_1_sq - pow(sum_1,2)/numSim) * (sum_2_sq - pow(sum_2,2)/numSim))

	if den == 0:
		return 0
	r = num / den
	return r

def jaccard(ratings, user_1, user_2):
	# similarity = {}
	# for item in ratings[user_1]:
	# 	if item in ratings[user_2]:
	# 		similarity[item] = 1

	# numSim =len(similarity)

	# if numSim == 0:
	# 	return 0

	userOneRatingsArray = ([ratings[user_1][item] for item in ratings[user_1]])
	userOne = set(userOneRatingsArray)
	userTwoRatingsArray = ([ratings[user_2][item] for item in ratings[user_1]])
	userTwo = set(userTwoRatingsArray)

	return (len(set(userOne.intersection(userTwo))) / float(len(userOne.union(userTwo))))




def matches (ratings,person,similarity):
	first_person = person
	scores = [(similarity(ratings,first_person, second_person),second_person) for second_person in ratings if first_person!=second_person]
	scores.sort()
	scores.reverse()
	return scores

def similaritems(ratings,similarity):
	itemlist = {}
	itemsratings = transposeratings(ratings)
	c =0
	for item in itemsratings:
		c = c+1
		if c%100==0:
			print "%d %d" % (c,len(itemsratings))
		matches = matches(itemsratings,item,similarity)
		itemlist[item] = matches
	return itemlist

def userBasedRecommendations(ratings, wantedPredictions, similarity):
	file = open('user.txt', 'w')
	ranks = {}

	for tuple in wantedPredictions:
		user = tuple[0]
		movieAsked = tuple[1]
		print user, movieAsked
		total = {}
		similaritySums = {}

		for second_person in ratings:
			if second_person == user: continue
			s = similarity(ratings,user, second_person)

			if s <= 0: continue

			for item in ratings[second_person]:
				if item not in ratings[user] or ratings[user][item] == 0:
					total.setdefault(item, 0)
					total[item] += int(ratings[second_person][item])*s
					similaritySums.setdefault(item, 0)
					similaritySums[item] += s
					ranks[item] = total[item]/similaritySums[item]
		file.write(str(ranks[movieAsked])+'\n')
'''
def itemBasedRecommendations(ratings, itemToMatch, wantedPredictions):
	file = open('itemBasedRecos.txt', 'a')
	for tuple in wantedPredictions:
		user = tuple[0]
		movieAsked = tuple[1]

		uRatings = ratings[user]
		scores = {}
		total = {}
		ranks = {}


		# items rated by this user
		for(item, rating) in uRatings.items():
		# items that are similar to this one
			for(similarity,item_2) in itemToMatch[item]:
			# don't consider if the user has already rated this item
				if item_2 in uRatings: continue
				scores.setdefault(item_2, 0)
				scores[item_2] += similarity*int(rating)

				# sum over similarities
				total.setdefault(item_2,0)
				total[item_2] += similarity
				if total[item_2] == 0: 
					ranks[item_2] = 1
				else:
					ranks[item_2] = scores[item_2]/total[item_2]
		print ranks[movieAsked]
		file.write(str(ranks[movieAsked]))

# combination of item based and used based recommendations. Content - Boosted Collaborative Filtering
def itemBasedRecommendationsForCBCF(ratings, itemToMatch):
	for user in ratings:
		uRatings = ratings[user]
		scores = {}
		total = {}
		ranks = {}


		# items rated by this user
		for(item, rating) in uRatings.items():
		# items that are similar to this one
			for(similarity,item_2) in itemToMatch[item]:
			# don't consider if the user has already rated this item
				if item_2 in uRatings: 
					uRatings[item_2] = uRatings[item_2]
				else:
					scores.setdefault(item_2, 0)
					scores[item_2] += similarity*int(rating)

					# sum over similarities
					total.setdefault(item_2,0)
					total[item_2] += similarity
					if total[item_2] == 0: 
						uRatings[item_2] = 1
					else:
						uRatings[item_2] = scores[item_2]/total[item_2]
		
	return ratings
'''
def mainFunction():
	similaritymeasure = raw_input()
	if similaritymeasure == 'cosine':
		sim = sim_cosine
	elif similaritymeasure == 'pearson':
		sim = sim_pearson
	else:
		sim = jaccard
	print sim
	userBasedRecommendations(userratings,test_data,sim)
	

mainFunction()

