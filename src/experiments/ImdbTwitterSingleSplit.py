'''
IMDb and Twitter are just names, can be used for arbitrary datasets.
'''

import math, time, json
import numpy as np
import pandas as pd
import fire
from src.models.BagOfWordsNaiveBayes import BagOfWordsNaiveBayes
from src.models.EmbeddingNaiveBayes import EmbeddingNaiveBayes
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from sklearn.metrics import roc_curve, roc_auc_score, auc
import matplotlib.pyplot as plt

def load_preprocessing(path):
    df = pd.read_csv(path)
    corpus = df.iloc[:,2].values
    y = df['Label'].values
    return corpus, y


def main(name='', seed = 42, train_perc = 0.8, bow=True, 
multinomial=False, tfidf=False, ngram_s=1, ngram_e=1, 
fastText=True, classifierType = 'categorical', numBinsPerFeature=10, embeddingSize = 100, emb_export_path = None, emb_import_path = 'datasets/fasttext/train_embedding.ft', 
showTrainingStats=False, export_results_path='experiments/testSingleSplit', path_imdb = 'imdb_preprocess.csv', path_tweet = 'twitter_preprocess.csv', show=True, imdbClass=1, twitterClass=4):
    '''
    bow=True --> use bag of words, bow=False --> use embeddings
    - multinomial, tfidf, ngram_s, ngram_e ==> used only in Bag of Words
    - fastText, classifierType, numBinsPerFeature, embeddingSize ==> used only with embeddings
    '''
    start_time = time.time()

    print('seed:', seed)
    print('train_perc:', train_perc)
    if bow:
        print('multinomial:', multinomial)
        print('tfidf:', tfidf)
        print('ngram=(', ngram_s, ',', ngram_e, ')', sep='')
    else:
        print('fastText:', fastText)
        print('classifierType:', classifierType)
        print('embeddingSize:', embeddingSize)
        print('numBinsPerFeature:', numBinsPerFeature)

    X_imdb, y_imdb = load_preprocessing(path_imdb)
    y_imdb = y_imdb // imdbClass

    X_tweet, y_tweet = load_preprocessing(path_tweet)
    y_tweet = y_tweet // twitterClass  

    X_imdb_train, X_imdb_test, y_imdb_train, y_imdb_test = train_test_split(X_imdb, y_imdb, train_size=train_perc, random_state=seed) #split imdb in train/test
    X_tweet_train, X_tweet_test, y_tweet_train, y_tweet_test = train_test_split(X_tweet, y_tweet, train_size=train_perc, random_state=seed) #split tweet in train/test

    X_train = {'imdb': X_imdb_train, 'tweet': X_tweet_train}
    X_test = {'imdb': X_imdb_test, 'tweet': X_tweet_test}
    y_train = {'imdb': y_imdb_train, 'tweet': y_tweet_train}
    y_test = {'imdb': y_imdb_test, 'tweet': y_tweet_test}

    params = [bow, multinomial, tfidf, ngram_s, ngram_e, 
    seed, classifierType, fastText, embeddingSize, numBinsPerFeature, emb_import_path, emb_export_path, showTrainingStats, 
    start_time, export_results_path, train_perc, show]

    # Train:Imdb, Test:Twitter 
    ImdbTweet(X_train['imdb'], X_test['tweet'], y_train['imdb'], y_test['tweet'], 'TrainOn1°_' + name, *params)

    # Train:Twitter, Test:Imdb
    ImdbTweet(X_train['tweet'], X_test['imdb'], y_train['tweet'], y_test['imdb'], 'TrainOn2°_' + name, *params)


def ImdbTweet(X_train, X_test, y_train, y_test, name, bow, multinomial, tfidf, ngram_s, ngram_e,
seed, classifierType, fastText, embeddingSize, numBinsPerFeature, emb_import_path, emb_export_path, showTrainingStats,
start_time, export_results_path, train_perc, show):
    print('train:', X_train.shape)
    print('test:', X_test.shape)
    
    #create the model
    model = None 
    if bow: #bag of words model
        model = BagOfWordsNaiveBayes(multinomial, tfidf, ngram_s, ngram_e) #create the model
    else: #embeddings model
        model = EmbeddingNaiveBayes(classifierType, fastText, embeddingSize, numBinsPerFeature, loadEmbedderPath=emb_import_path, exportEmbedderPath=emb_export_path)

    model.train(X_train, y_train) #train the model
    y_score, y_pred = model.perform_test(X_test) #get scores and predictions
    fpr, tpr, thresholds = roc_curve(y_test, y_score) 
    test_acc = accuracy_score(y_test, y_pred)
    test_f1 = f1_score(y_test, y_pred)
    test_auroc = roc_auc_score(y_test, y_score)
    print('accuracy:', test_acc) #print some scores
    print('f1-score:', test_f1)
    print('au-roc:', test_auroc)

    #we perform the evalutation over the training set (just to compare with the test)
    if showTrainingStats:
        y_score_train, y_pred_train = model.perform_test(X_train)
        fpr_train, tpr_train, thresholds_train = roc_curve(y_train, y_score_train)
        print('accuracy:', accuracy_score(y_train, y_pred_train))
        print('f1-score:', f1_score(y_train, y_pred_train))
        print('au-roc:', roc_auc_score(y_train, y_score_train))

    print('seconds needed:', (time.time() - start_time))

    exportStats(export_results_path, name, seed, train_perc, bow, multinomial, tfidf, ngram_s, ngram_e, 
    fastText, classifierType, embeddingSize, numBinsPerFeature, test_acc, test_f1, test_auroc, fpr, tpr)

    if show:
        plt.plot(fpr, tpr, label='test roc')
        if showTrainingStats:
            plt.plot(fpr_train, tpr_train, label='train roc')
        plt.legend()
        plt.show()

def exportStats(path, name, seed, train_perc, bow, multinomial, tfidf, ngram_s, ngram_e, fastText, classifierType, embeddingSize, numBinsPerFeature, accuracy, f1, auroc, fpr, tpr):
    if path is None:
        return
    path += '_'+name+'_'+str(time.time())
    outd = {'name': name,
            'seed': seed, 
            'train_perc': train_perc,
            'bow': bow,
            'accuracy': accuracy,
            'f1-score': f1,
            'auroc': auroc,
            'fpr': fpr.tolist(),
            'tpr': tpr.tolist()}
    if bow:
        outd['multinomial'] = multinomial
        outd['tfidf'] = tfidf 
        outd['ngram_s'] = ngram_s
        outd['ngram_e'] = ngram_e
    else:
        outd['fastText'] = fastText
        outd['classifierType'] = classifierType
        outd['embeddingSize'] = embeddingSize
        outd['numBinsPerFeature'] = numBinsPerFeature
    
    with open(path, 'w') as fout:
        fout.write(json.dumps(outd))


if __name__ == '__main__':
    fire.Fire(main)