import os
import pandas as pd
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, accuracy_score, precision_recall_fscore_support
import seaborn as sns
import matplotlib.pyplot as plt

# ----------------------------
# LOAD DATASET
# ----------------------------
print("Loading the dataset...")

# Dataset information:
'''
It consists of 713 tweets in Indonesian

Number of Non_HS tweets: 453
Number of HS tweets: 260.
Since this dataset is unbalanced, you might have to do over-sampling/down-sampling in order to create a balanced dataset.
'''

# Load dataset IDHSD_RIO_unbalanced_713_2017.txt
df = pd.read_csv('IDHSD_RIO_unbalanced_713_2017.txt', sep='\t', encoding='ISO-8859-1')
# Downsample the Non-HS tweets to 260
df_non_hs = df[ df[ 'Label' ] == "Non_HS" ].sample(n=260, random_state=42)
# Downsample the HS tweets to 260 (same amount)
df_hs = df[ df[ 'Label' ] == "HS" ].sample(n=260, random_state=42)
# Concatenate the downsampled Non-HS and HS tweets
df = pd.concat([ df_non_hs, df_hs ])
# Shuffle the dataset
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

# Display the first 5 rows of the dataset
print("First 5 rows of the dataset:")
print(df.head())

# ----------------------------
# PRE-PROCESSING
# ----------------------------
print("\nPre-processing the dataset...")

# Tokenization
df[ 'tokenized_text' ] = df[ 'Tweet' ].apply(word_tokenize)
print("\nTokenized text:\n", df[ 'tokenized_text' ].head())
# If the current token is a #, remove the current token and the next token
df[ 'tokenized_text' ] = df[ 'tokenized_text' ].apply(lambda x: [ x[i] for i in range(len(x)) if x[i] != '#' and (i == 0 or x[i-1] != '#') ])
# If the current token is a @, remove the current token and the next token
df[ 'tokenized_text' ] = df[ 'tokenized_text' ].apply(lambda x: [ x[i] for i in range(len(x)) if x[i] != '@' and (i == 0 or x[i-1] != '@') ])
# Lowercasing
df[ 'tokenized_text' ] = df[ 'tokenized_text' ].apply(lambda x: [ word.lower() for word in x ])
print("\nLowercased text:\n", df[ 'tokenized_text' ].head())
# # Remove non-alphanumeric tokens
# df[ 'tokenized_text' ] = df[ 'tokenized_text' ].apply(lambda x: [ word for word in x if word.isalnum() ])
# print("\nText with alphanumeric tokens:\n", df[ 'tokenized_text' ].head())
# Remove tokens with only non-alphanumeric characters
df[ 'tokenized_text' ] = df[ 'tokenized_text' ].apply(lambda x: [ word for word in x if any(char.isalnum() for char in word) ])
print("\nText with alphanumeric tokens:\n", df[ 'tokenized_text' ].head())
# Remove stopwords
# Load Indonesian stopwords from stopwordbahasa.csv
stopwords = pd.read_csv('stopwordbahasa.csv')
df[ 'tokenized_text' ] = df[ 'tokenized_text' ].apply(lambda x: [ word for word in x if word not in stopwords ])
print("\nText without stopwords:\n", df[ 'tokenized_text' ].head())

# Display the first 5 rows of the dataset
print("\nFirst 5 rows of the dataset after pre-processing:")
print(df.head())

# ----------------------------
# DATA SPLITTING
# ----------------------------
print("\nSplitting the dataset into training and testing sets...")

# Split the dataset into training and testing sets (80% training, 20% testing)
# Randomly shuffle the dataset
df = df.sample(frac=1, random_state=42).reset_index(drop=True)
# Split the dataset
train_size = int(0.8 * len(df))
train_df = df[ :train_size ]
test_df = df[ train_size: ]

# Display the shape of the training and testing sets
print("\nShape of the training set:", train_df.shape)
print("Shape of the testing set:", test_df.shape)

# ----------------------------
# FEATURE EXTRACTION
# ----------------------------
print("\nExtracting features from the dataset...")

# Calculate the term frequency values for words in the training set
train_tf = {}
train_tf[ 'HS' ] = {}
train_tf[ 'Non_HS' ] = {}
for index, row in train_df.iterrows():
    for word in row[ 'tokenized_text' ]:
        if word not in train_tf[ row[ 'Label' ] ]:
            train_tf[ row[ 'Label' ]][ word ] = 1
        else:
            train_tf[ row[ 'Label' ]][ word ] += 1

# Display the term frequency values for the training set
print("\nTerm frequency values for the training set:")
print(train_tf[ 'HS' ])
print(train_tf[ 'Non_HS' ])

# ----------------------------
# VECTORIZE TEXT DATA
# ----------------------------
print("\nVectorizing text data...")

# Combine tokenized text back into strings for vectorization
train_df['clean_text'] = train_df['tokenized_text'].apply(lambda x: ' '.join(x))
test_df['clean_text'] = test_df['tokenized_text'].apply(lambda x: ' '.join(x))

# Create CountVectorizer
vectorizer = CountVectorizer()

# Fit and transform the training data
X_train = vectorizer.fit_transform(train_df['clean_text'])
y_train = train_df['Label']

# Transform the testing data
X_test = vectorizer.transform(test_df['clean_text'])
y_test = test_df['Label']

print("\nShape of the training data:", X_train.shape)
print("Shape of the testing data:", X_test.shape)
print("Shape of y_train:", y_train.shape)
print("Shape of y_test:", y_test.shape)

# ----------------------------
# CLASSIFICATION
# ----------------------------
print("\nTraining the classification model...")

# Initialize Logistic Regression model
clf = LogisticRegression(max_iter=10000, random_state=42)

# Train model
clf.fit(X_train, y_train)

# Predict
y_pred = clf.predict(X_test)

print("\nPredictions:")
print(y_pred)

# ----------------------------
# INCORRECT PREDICTIONS
# ----------------------------
print("\nDisplaying incorrect predictions...")
# Find indices where predicted values do not match actual values
wrong_indices = [i for i in range(len(y_test)) if y_test.iloc[i] != y_pred[i]]

# Retrieve wrong predictions from test data
wrong_predictions = test_df.iloc[wrong_indices]
wrong_actual_values = y_test.iloc[wrong_indices]
wrong_predicted_values = y_pred[wrong_indices]

# Convert vectorized wrong predictions back to text
wrong_actual_texts = vectorizer.inverse_transform(X_test[wrong_indices])
wrong_actual_texts = [' '.join(text) for text in wrong_actual_texts]

# Retrieve pre-processed wrong predictions from test data
wrong_preprocessed_texts = test_df.iloc[wrong_indices]['Tweet'].values

# Create a DataFrame to store wrong predictions, actual texts, pre-processed texts, and predicted values
wrong_data_with_preprocessed = {
    'preprocessed_text': wrong_preprocessed_texts,
    'actual_text': wrong_actual_texts,
    'actual_value': wrong_actual_values.values,
    'predicted_value': wrong_predicted_values
}
wrong_df_with_preprocessed = pd.DataFrame(wrong_data_with_preprocessed)

# Display wrong predictions with actual texts, pre-processed texts, actual, and predicted values
print("\nWrong predictions with actual and pre-processed texts:")
for index, row in wrong_df_with_preprocessed.iterrows():
    print(f"Preprocessed Text: {row['preprocessed_text']}")
    print(f"Actual Text: {row['actual_text']}")
    print(f"Actual Value: {row['actual_value']}, Predicted Value: {row['predicted_value']}")
    print("-" * 50)

# ----------------------------
# PREDICTION
# ----------------------------
print("\nMaking predictions on new data...")
new_data = ['saya suka kamu',
            'ahok mmg mulut sampah provokator paling bangsat']
new_data_vect = vectorizer.transform(new_data)
new_pred = clf.predict(new_data_vect)
print("\nPredictions on new data:")
print("New data:", new_data)
print("Predictions:", new_pred)

# ----------------------------
# EVALUATION
# ----------------------------
print("\nEvaluating the classification model...")

# Calculate accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f"Accuracy: {accuracy*100:.2f}%")

# Calculate precision, recall, and F1-score
precision, recall, f1_score, _ = precision_recall_fscore_support(y_test, y_pred, average='binary', pos_label='HS')
print(f"Precision: {precision*100:.2f}%")
print(f"Recall: {recall*100:.2f}%")
print(f"F1-score: {f1_score*100:.2f}%")

# Display the confusion matrix
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["Non_HS", "HS"], yticklabels=["Non_HS", "HS"])
plt.xlabel('Predicted Label')
plt.ylabel('True Label')
plt.title('Confusion Matrix')
plt.show()

# Save results to a CSV file
results = {
    'Actual': y_test,
    'Predicted': y_pred
}
# Add accuracy, precision, recall, and F1-score to the results
results['Accuracy'] = accuracy
results['Precision'] = precision
results['Recall'] = recall
results['F1-score'] = f1_score
results_df = pd.DataFrame(results)

# Create results directory if it does not exist
if not os.path.exists('results'):
    os.makedirs('results')

# Save results title with accuracy, date and time
results_title = f"results/results_{accuracy:.4f}-" + pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S") + ".csv"
results_df.to_csv(results_title, index=False)
