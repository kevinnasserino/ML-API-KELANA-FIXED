import pandas as pd
import nltk
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Embedding, Dense, Flatten, Concatenate, Input, Dropout
from tensorflow.keras.regularizers import l2
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import KFold
import matplotlib.pyplot as plt
from sklearn.utils import shuffle

# Download necessary NLTK resources
nltk.download('punkt_tab')
nltk.download('stopwords')

# Load dataset
places_df = pd.read_csv('app/dataset/tourismkelana_fixed.csv')

places_df.head()

# **Step 1: Price Categorization**
def categorize_price(df):
    conditions = [
        (df['Price'] < 50000),
        (df['Price'] >= 50000) & (df['Price'] <= 200000),
        (df['Price'] > 200000)
    ]
    categories = ['Murah', 'Sedang', 'Mahal']
    df['Price_Category'] = np.select(conditions, categories, default='Sedang')
    return df

places_df = categorize_price(places_df)

# **Step 2: Preprocessing Text**
def preprocess_text(text):
    tokens = nltk.word_tokenize(text.lower())
    tokens = [word for word in tokens if word.isalpha()]
    stop_words = set(nltk.corpus.stopwords.words('indonesian'))
    tokens = [word for word in tokens if word not in stop_words]
    return ' '.join(tokens)

# Apply preprocessing to the 'Category' and 'Description' columns
places_df['content'] = places_df['Category'] + ' ' + places_df['Description']
places_df['processed_content'] = places_df['content'].apply(preprocess_text)

# **Step 3: TF-IDF Vectorization**
tfidf_vectorizer = TfidfVectorizer(max_features=500)
tfidf_matrix = tfidf_vectorizer.fit_transform(places_df['processed_content']).toarray()

# **Step 4: Encoding Kategori dan Harga**
label_encoder_category = LabelEncoder()
places_df['Category_encoded'] = label_encoder_category.fit_transform(places_df['Category'])

label_encoder_price = LabelEncoder()
places_df['Price_Category_encoded'] = label_encoder_price.fit_transform(places_df['Price_Category'])

# Step 5: Create Labels Based on Rating (e.g., popular places)
places_df['Label'] = np.where(places_df['Rating'] >= 4.2, 1, 0)

places_df['Rating'].value_counts()

places_df.head()

model = tf.keras.models.load_model('app/cbf_model.h5')



# **Step 6: Rekomendasi Berdasarkan Kota dan Harga**
def recommend(city_name, price_category, waktu, top_n=3):
    """
    Memberikan rekomendasi tempat wisata berdasarkan kota dan kategori harga.

    Parameters:
        city_name: str - Nama kota yang dipilih.
        price_category: str - Kategori harga yang diinginkan ('Murah', 'Sedang', 'Mahal').
        top_n: int - Jumlah rekomendasi yang diinginkan.

    Returns:
        pd.DataFrame - DataFrame yang berisi nama tempat, kategori, deskripsi, rating, dan harga.
    """
    # Filter berdasarkan kota dan harga
    tm = 0
    if waktu == "morning":
      tm = 10
    elif waktu == "afternoon":
      tm = 15
    elif waktu == "evening":
      tm = 21
    city_filtered_df = places_df[places_df['City'].str.contains(city_name, case=False, na=False)]
    time_filtered_df = city_filtered_df[city_filtered_df['Opening_Time'] <= tm]
    time_filtered_df = time_filtered_df[time_filtered_df['Closing_Time'] >= tm]
    price_filtered_df = time_filtered_df[time_filtered_df['Price_Category'] == price_category]

    if price_filtered_df.empty:
        return f"No places found in city '{city_name}' with price category '{price_category}'."

    # Prepare input data
    category_input_data = price_filtered_df['Category_encoded'].values.reshape(-1, 1)
    price_input_data = price_filtered_df['Price_Category_encoded'].values.reshape(-1, 1)
    description_input_data = tfidf_matrix[price_filtered_df.index]
   
    # Shuffle the input data to avoid bias in the recommendation
    category_input_data, price_input_data, description_input_data = shuffle(category_input_data, price_input_data, description_input_data)

    # Predict similarity
    predictions = model.predict([category_input_data, price_input_data, description_input_data]).flatten()

    # Get top_n recommendations
    similar_indices = predictions.argsort()[-top_n:][::-1]
    recommended_places = price_filtered_df.iloc[similar_indices]

    # Output recommendations
    return recommended_places[['Place_Name', 'Category', 'Description', 'Rating', 'Price', 'Lat', 'Long', 'Opening_Time', 'Closing_Time']]

#recommendations = recommend("Surabaya", "Murah", "Evening", 50)
#print(len(recommendations))
#print(recommendations)

# Menyimpan model CBF yang sudah dilatih ke dalam file H5
# model.save('cbf_model.h5')

