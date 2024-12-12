from haversine import haversine, Unit
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# Fungsi untuk membuat matriks jarak
def create_distance_matrix(places):
    distance_matrix = []
    coords = list(places.values())
    
    for i in range(len(coords)):
        row = []
        for j in range(len(coords)):
            if i == j:
                row.append(0)
            else:
                # Menggunakan haversine untuk menghitung jarak dalam meter
                distance = haversine(coords[i], coords[j], unit=Unit.METERS)
                row.append(int(distance))  # Konversi ke integer
        distance_matrix.append(row)
    return distance_matrix

# Fungsi untuk membuat data model
def create_data_model(places):
    distance_matrix = create_distance_matrix(places)
    data = {
        'distance_matrix': distance_matrix,
        'num_vehicles': 1,  # Hanya satu kendaraan
        'depot': 0  # Tempat awal (depot)
    }
    return data

# Fungsi untuk mencetak solusi
def print_solution(manager, routing, solution, places):
    route = []
    total_distance = 0
    index = routing.Start(0)
    while not routing.IsEnd(index):
        node_index = manager.IndexToNode(index)
        route.append(node_index)
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        total_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
    route.append(manager.IndexToNode(index))

    # Daftar tempat wisata berdasarkan indeks dalam matriks jarak
    route_names = [list(places.keys())[i] for i in route]
    total_distance_km = total_distance / 1000  # Ubah ke kilometer

    return {
        'route': route_names,
        'total_distance': total_distance_km
    }

# Fungsi utama untuk menyelesaikan masalah
def solve_tsp(places):
    data = create_data_model(places)
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']), data['num_vehicles'], data['depot'])
    routing = pywrapcp.RoutingModel(manager)

    # Callback untuk jarak antar tempat
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Menetapkan parameter pencarian
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    # Menyelesaikan masalah
    solution = routing.SolveWithParameters(search_parameters)

    if solution:
        return print_solution(manager, routing, solution, places)
    else:
        print('Tidak ada solusi ditemukan!')
        return None
