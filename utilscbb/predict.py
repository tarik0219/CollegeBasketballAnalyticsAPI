import pickle
import numpy as np
import os
def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn

scoresFile = os.path.join(os.getcwd(), "models/scores.pkl")
probFile = os.path.join(os.getcwd(), "models/prob.pkl")

def changeBool(value):
    if value:
        return 1
    else:
        return 0


def make_prediction_api(homeData, awayData, siteType):
    if siteType:
        siteType = changeBool(siteType)
        X = np.array([[homeData['offRating'],homeData['defRating'],homeData['TempoRating'],awayData['offRating'],awayData['defRating'],awayData['TempoRating'],siteType]])
        X2 = np.array([[awayData['offRating'],awayData['defRating'],awayData['TempoRating'],homeData['offRating'],homeData['defRating'],homeData['TempoRating'],siteType]])
        scoresModel = pickle.load(open(scoresFile, 'rb'))
        probModel = pickle.load(open(probFile, 'rb'))

        y_pred = scoresModel.predict(X)
        y_pred.tolist()
        y_pred_2 = scoresModel.predict(X2)
        y_pred_2.tolist()
        homeScore = round((y_pred[0][0] + y_pred_2[0][1])/2,1)
        awayScore = round((y_pred[0][1] + y_pred_2[0][0])/2,1)

        y_prob = probModel.predict_proba(X)
        y_prob.tolist()
        y_prob_2 = probModel.predict_proba(X2)
        y_prob_2.tolist()
        prob = round((y_prob[0][1]+y_prob_2[0][0])/2,4)
    
    else:
        siteType = changeBool(siteType)
        X = np.array([[homeData['offRating'],homeData['defRating'],homeData['TempoRating'],awayData['offRating'],awayData['defRating'],awayData['TempoRating'],siteType]])
        scoresModel = pickle.load(open(scoresFile, 'rb'))
        probModel = pickle.load(open(probFile, 'rb'))

        y_pred = scoresModel.predict(X)
        y_pred.tolist()
        homeScore = round(y_pred[0][0],1)
        awayScore = round(y_pred[0][1],1)

        y_prob = probModel.predict_proba(X)
        y_prob.tolist()
        prob = round(y_prob[0][1],4)

    return homeScore,awayScore,prob