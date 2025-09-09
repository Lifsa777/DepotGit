from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, HTMLResponse
import pandas as pd
from modele_svd import get_top_n_recommendations_svd  # Modèle de recommandation SVD
import uvicorn
import random

# Charger les données nettoyées
books = pd.read_csv('books_clean.csv', sep=';')
ratings = pd.read_csv('ratings_clean.csv', sep=';')

app = FastAPI(title="Recommandations de Livres")

# Simuler un stockage de likes (base de données fictive)
liked_books = {}

@app.get("/api/recommend/")
def recommend_books(user_id: int = Query(..., description="Identifiant de l'utilisateur")):
    # Obtenir les recommandations via le modèle SVD
    recommendations = get_top_n_recommendations_svd(user_id, n=10)

    if not recommendations:
        # Si l'utilisateur n'est pas reconnu, on affiche le top 10 des livres les plus populaires
        popular_books = ratings.groupby("ISBN")["Book-Rating"].count().reset_index()
        popular_books = popular_books.sort_values(by="Book-Rating", ascending=False).head(10)

        result = []
        for isbn in popular_books["ISBN"]:
            book_info = books[books["ISBN"] == isbn]
            if book_info.empty:
                continue
            title = book_info["Book-Title"].values[0]
            image_url = book_info["Image-URL-L"].values[0]
            result.append({
                "ISBN": isbn,
                "Book-Title": title,
                "Predicted Rating": "🔥 Populaire",
                "Image_URL": image_url
            })

        return JSONResponse(content=result)

    # Sinon, on renvoie les recommandations normales
    result = []
    for isbn, score in recommendations:
        title = books.loc[books['ISBN'] == isbn, 'Book-Title'].values[0]
        image_url = books.loc[books['ISBN'] == isbn, 'Image-URL-L'].values[0]
        result.append({
            "ISBN": isbn,
            "Book-Title": title,
            "Predicted Rating": round(score, 2),
            "Image_URL": image_url
        })
    
    return JSONResponse(content=result)

@app.post("/api/like/")
def like_book(isbn: str):
    if isbn in liked_books:
        liked_books[isbn] += 1
    else:
        liked_books[isbn] = 1
    return JSONResponse(content={"message": f"Livre {isbn} liké avec succès", "likes": liked_books[isbn]})


@app.get("/api/trending/")
def trending_books():
    """ Retourne les livres les plus populaires (basés sur les évaluations) """
    top_books = books.sample(10)  # Sélection aléatoire, peut être remplacée par un vrai tri
    result = [
        {
            "ISBN": row['ISBN'],
            "Book-Title": row['Book-Title'],
            "Image_URL": row['Image-URL-L'],
            "Genre": row.get('Genre', "Inconnu"),
            "Likes": liked_books.get(row['ISBN'], random.randint(0, 50))  # Fake likes
        }
        for _, row in top_books.iterrows()
    ]
    return JSONResponse(content=result)

@app.get("/", response_class=HTMLResponse)
def read_root(user_id: int = Query(None, description="Identifiant de l'utilisateur")):
    html_content = """
    <html>
        <head>
            <meta charset="UTF-8">
            <title>Recommandations de Livres</title>
            <style>
                body { font-family: Arial, sans-serif; background: #f4f4f9; text-align: center; margin: 0; padding: 20px; }
                h1 { color: #2C3E50; }
                form { margin-bottom: 20px; }
                input[type="number"] { padding: 10px; font-size: 16px; width: 200px; border-radius: 5px; }
                button { padding: 10px 20px; font-size: 16px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; }
                .book-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; margin-top: 20px; }
                .book-card { width: 180px; padding: 15px; background: white; border-radius: 10px; box-shadow: 0px 2px 5px rgba(0,0,0,0.1); transition: transform 0.2s ease-in-out; }
                .book-card:hover { transform: scale(1.05); }
                img { width: 140px; height: 210px; border-radius: 5px; }
                .error { color: red; font-weight: bold; }
                .like-btn { background: #FF5733; color: white; border: none; padding: 5px 10px; cursor: pointer; margin-top: 10px; border-radius: 5px; }
            </style>
            <script>
                function likeBook(isbn) {
                    fetch(`/api/like/?isbn=${isbn}`, { method: "POST" })
                    .then(response => response.json())
                    .then(data => {
                        alert("👍 Livre liké ! Nombre total de likes : " + data.likes);
                    });
                }
            </script>
        </head>
        <body>
            <h1>📚 Découvrez des livres qui vous correspondent</h1>
            <form method="get" action="/">
                <label for="user_id">🔍 Identifiant utilisateur :</label>
                <input type="number" id="user_id" name="user_id" required>
                <button type="submit">Obtenir des recommandations</button>
            </form>
    """
    if user_id is not None:
        recommendations = get_top_n_recommendations_svd(user_id, n=10)
        if not recommendations:
            html_content += "<p class='error'>❌ Identifiant non reconnu ou pas assez d'évaluations.</p>"
            html_content += "<h3>🔥 Voici une liste des livres les plus populaires:</h3>"
            
            # Obtenir les 10 livres les plus populaires
            popular_books = ratings.groupby("ISBN")["Book-Rating"].count().reset_index()
            popular_books = popular_books.sort_values(by="Book-Rating", ascending=False).head(10)

            html_content += "<div class='book-container'>"
            for isbn in popular_books["ISBN"]:
                book_info = books[books["ISBN"] == isbn]
                if book_info.empty:
                    continue
                title = book_info["Book-Title"].values[0]
                image_url = book_info["Image-URL-L"].values[0]
                html_content += f"""
                    <div class="book-card">
                        <img src="{image_url}" alt="Couverture de {title}">
                        <p><strong>{title}</strong></p>
                        <p>🔥 Populaire</p>
                    </div>
                """
            html_content += "</div>"

            
        else:
            html_content += f"<h2>📖 Recommandations pour l'utilisateur {user_id} :</h2>"
            html_content += "<div class='book-container'>"
            for isbn, predicted_rating in recommendations:
                title = books.loc[books['ISBN'] == isbn, 'Book-Title'].values[0]
                image_url = books.loc[books['ISBN'] == isbn, 'Image-URL-L'].values[0]
                html_content += f"""
                    <div class="book-card">
                        <img src="{image_url}" alt="Couverture de {title}">
                        <p><strong>{title}</strong></p>
                        <p>⭐ Note prédite: {predicted_rating:.2f}</p>
                        <button class="like-btn" onclick="likeBook('{isbn}')">❤️ J'aime</button>
                    </div>
                """
            html_content += "</div>"

    html_content += """
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

# pour lanlcer l'application entrez: uvicorn main:app --reload dans le terminal
 