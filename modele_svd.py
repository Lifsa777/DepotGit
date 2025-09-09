# Modélisation SVD avec TruncatedSVD de scikit-learn

import pandas as pd
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt

# Charger les données nettoyées
ratings = pd.read_csv('ratings_clean.csv', sep=';')
books = pd.read_csv('books_clean.csv', sep=';')

# Création de la matrice utilisateurs‑items
ratings_pivot = ratings.pivot(index='User-ID', columns='ISBN', values='Book-Rating').fillna(0)
R = ratings_pivot.values

# Optimisation du nombre de composantes
n_components_values = [10, 20, 30, 40, 50, 60, 70]
rmse_scores = []

for n in n_components_values:
    svd = TruncatedSVD(n_components=n, random_state=42)
    W = svd.fit_transform(R)
    H = svd.components_
    R_pred = np.dot(W, H)
    
    mask = R > 0  # Calcul du RMSE uniquement sur les notes existantes
    mse = mean_squared_error(R[mask], R_pred[mask])
    rmse_scores.append(np.sqrt(mse))
    print(f"n_components = {n}, RMSE = {rmse_scores[-1]:.4f}")

# Tracer la courbe RMSE vs nombre de composantes
plt.figure(figsize=(8, 5))
plt.plot(n_components_values, rmse_scores, marker='o', linestyle='-')
plt.xlabel('Nombre de composantes (n_components)')
plt.ylabel('RMSE')
plt.title("Optimisation du nombre de composantes pour TruncatedSVD")
plt.grid(True)
plt.show()

# Sélection du meilleur nombre de composantes
best_n = n_components_values[np.argmin(rmse_scores)]
print(f"Meilleur n_components: {best_n} avec RMSE = {min(rmse_scores):.4f}")

# Entraînement du modèle optimisé
svd_opt = TruncatedSVD(n_components=best_n, random_state=42)
W_opt = svd_opt.fit_transform(R)
H_opt = svd_opt.components_
R_pred_opt = np.dot(W_opt, H_opt)

# Fonction de recommandation
def get_top_n_recommendations_svd(user_id, n=10):
    if user_id not in ratings_pivot.index:
        return []
    
    user_idx = ratings_pivot.index.get_loc(user_id)
    user_pred = R_pred_opt[user_idx]
    user_rated = ratings_pivot.loc[user_id]
    unrated_books = user_rated[user_rated == 0].index
    
    preds = [(isbn, user_pred[ratings_pivot.columns.get_loc(isbn)]) for isbn in unrated_books]
    preds.sort(key=lambda x: x[1], reverse=True)
    return preds[:n]

# Exemple d'utilisation pour un utilisateur donné
example_user = ratings_pivot.index[0]
top_n = get_top_n_recommendations_svd(example_user, n=10)
print("Top 10 recommandations pour l'utilisateur", example_user)
for isbn, score in top_n:
    title = books.loc[books['ISBN'] == isbn, 'Book-Title'].values[0]
    print(f"{title} (ISBN: {isbn}) - Note prédite: {score:.2f}")