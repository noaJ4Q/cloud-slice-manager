import socket
from pymongo import MongoClient

def conexion_db():
    try:
        cliente = MongoClient("localhost", 27017)
        monitoreo_db = cliente["monitoreo"]
    except Exception as e:
        print(f"Error durante la conexión: {e}")
        return None
    return monitoreo_db

db = conexion_db()
coleccion = db["worker1"] if db else None

def mantener_ultimas_n_iteraciones(n):
    total_docs = coleccion.count_documents({})
    if total_docs > n:
        docs_mas_antiguos = coleccion.find().sort("hora_actual", 1).limit(total_docs - n)
        for doc in docs_mas_antiguos:
            coleccion.delete_one({"_id": doc["_id"]})

def servidor(puerto):
    if not coleccion:
        print("Error de conexión a la base de datos")
        return

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', puerto))
    s.listen()
    print(f"Escuchando en el puerto {puerto}...")

    while True:
        conn, addr = s.accept()
        print(f"Conexión recibida de {addr}")
        with conn:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                metricas = data.decode('utf-8').split('\n')
                metricas_dict = {}
                for metrica in metricas:
                    if metrica:
                        partes_metrica = metrica.split(':', 1)  # Dividir solo en el primer ':' encontrado
                        if len(partes_metrica) == 2:
                            clave, valor = partes_metrica
                            metricas_dict[clave] = valor
                        else:
                            print(f"Ignorando métrica: {metrica}. Formato inválido.")

                # Insertar los datos en MongoDB
                resultado = coleccion.insert_one(metricas_dict)
                print(f"Dato insertado en MongoDB: {metricas_dict}")

                # Mantener solo las últimas 20 iteraciones
                mantener_ultimas_n_iteraciones(20)

if __name__ == "__main__":
    servidor(9999)
