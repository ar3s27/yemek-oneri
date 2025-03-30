import requests
from flask import Flask, render_template, request, session
from deep_translator import GoogleTranslator

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Session için gerekli (Gizli bir anahtar kullan)

API_KEY = "cb9cd26f89414bb097a9888577511aae"

# Çeviri Fonksiyonları
def turkce_to_ingilizce(malzemeler):
    return [GoogleTranslator(source="tr", target="en").translate(m) for m in malzemeler]

def ingilizce_to_turkce(text):
    return GoogleTranslator(source="en", target="tr").translate(text)

# API'den tarifleri çekme
def tarif_bul(malzemeler):
    malzemeler_ing = turkce_to_ingilizce(malzemeler)
    url = f"https://api.spoonacular.com/recipes/findByIngredients?ingredients={','.join(malzemeler_ing)}&number=8&cuisine=turkish&apiKey={API_KEY}"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else []

def tarif_detaylari(recipe_id):
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information?apiKey={API_KEY}"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

# Ana Sayfa: Yemek Kartları
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        malzemeler = request.form.get("malzemeler").lower().split(",")
        malzemeler = [m.strip() for m in malzemeler]
        bulunan_yemekler = tarif_bul(malzemeler)

        yemekler = []
        for yemek in bulunan_yemekler:
            yemekler.append({
                "id": yemek["id"],
                "title": ingilizce_to_turkce(yemek["title"]),
                "image": yemek["image"]
            })

        session["yemekler"] = yemekler  # Sonuçları session'a kaydet
    else:
        yemekler = session.get("yemekler", [])  # Önceki sonuçları session'dan al

    return render_template("index.html", yemekler=yemekler)

# Yemek Detay Sayfası
@app.route("/tarif/<int:yemek_id>")
def tarif(yemek_id):
    detay = tarif_detaylari(yemek_id)
    if detay:
        yemek_adi_tr = ingilizce_to_turkce(detay["title"])
        malzemeler_listesi = [f"{m['amount']} {m['unit']} {ingilizce_to_turkce(m['name'])}" for m in detay.get("extendedIngredients", [])]
        adimlar = [ingilizce_to_turkce(step["step"]) for instruction in detay.get("analyzedInstructions", []) for step in instruction["steps"]]

        return render_template("tarif.html", yemek=yemek_adi_tr, malzemeler=malzemeler_listesi, adimlar=adimlar, image=detay["image"])

    return "Tarif bulunamadı!", 404

if __name__ == "__main__":
    app.run(debug=True)
