from flask import Flask, Blueprint, request, jsonify
import os
from app import app
from datetime import datetime
from .cbf import recommend
from .tsp import solve_tsp

def calculate_duration(start_date, end_date):
    start = datetime.strptime(start_date, "%d-%m-%Y")
    end = datetime.strptime(end_date, "%d-%m-%Y")
    return (end - start).days + 1

# Membuat blueprint untuk rekomendasi dan optimasi rute
recommend_blueprint = Blueprint('recommend', __name__)

@recommend_blueprint.route('/recommend', methods=['POST'])
def recommend_places():
    data = request.get_json()
    city = data.get("city")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    price_category = data.get("price_category")

    if not all([city, start_date, end_date, price_category]):
        return jsonify({"error": "Missing required fields"}), 400

    # Menghitung durasi liburan
    num_days = calculate_duration(start_date, end_date)

    # Mendapatkan rekomendasi per slot waktu
    recommendations_per_slot = {
        slot: recommend(city, price_category, slot, top_n=3)
        for slot in ['morning', 'afternoon', 'evening']
    }

    # Menyusun daftar tempat terpilih untuk setiap hari
    selected_places = []
    for day in range(num_days):
        day_places = {}
        for slot, rec in recommendations_per_slot.items():
            if not rec.empty:
                selected_place = rec.iloc[0]
                day_places[slot] = selected_place.to_dict()
                recommendations_per_slot[slot] = rec.iloc[1:]
        selected_places.append({"day": f"Day {day + 1}", "places": day_places})

    # Mengoptimalkan rute perjalanan untuk setiap hari
    optimized_routes = []
    for day_index, day_info in enumerate(selected_places):
        places_with_coords = {
            place['Place_Name']: (float(place['Lat']), float(place['Long']))
            for place in day_info["places"].values()
        }
        route_info = solve_tsp(places_with_coords)
        if route_info:
            optimized_routes.append({
                "day": f"Day {day_index + 1}",
                "route": route_info["route"],
                "total_distance": route_info["total_distance"]
            })

    # Mengembalikan hasil sebagai respons
    return jsonify({
        "selected_places": selected_places,
        "routes": optimized_routes
    })

optimize_route_blueprint = Blueprint('optimize_route', __name__)

@optimize_route_blueprint.route('/optimize_route', methods=['POST'])
def get_optimized_route():
    data = request.json
    places_with_coords = data.get('places')

    if not places_with_coords:
        return jsonify({'error': 'No places provided for optimization'}), 400

    result = solve_tsp(places_with_coords)
    if result:
        return jsonify(result)
    else:
        return jsonify({'error': 'Could not optimize the route'}), 500

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# Daftarkan blueprint ke aplikasi utama
app.register_blueprint(recommend_blueprint)
app.register_blueprint(optimize_route_blueprint)

if __name__ == '__main__':
    # Gunakan variabel PORT atau default ke 8080 jika tidak ada
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
