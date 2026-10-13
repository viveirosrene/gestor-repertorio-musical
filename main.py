import crud

def show_menu():
    print("\n--- 🎸 GESTOR DE REPERTORIO MUSICAL 🎹 ---")
    print("1. Agregar Instrumento")
    print("2. Ver Instrumentos")
    print("3. Agregar Artista")
    print("4. Ver Artistas")
    print("5. Registrar Canción")
    print("6. Ver Repertorio de Canciones")
    print("0. Salir")

def main():
    while True:
        show_menu()
        option = input("\nSelecciona una opción: ").strip()

        if option == "1":
            name = input("Nombre del instrumento (ej. Bajo eléctrico, Piano, Guitarra): ").strip()
            if name:
                crud.add_instrument(name)

        elif option == "2":
            instruments = crud.list_instruments()
            print("\n--- Lista de Instrumentos ---")
            for inst in instruments:
                print(f"[{inst[0]}] {inst[1]}")

        elif option == "3":
            name = input("Nombre del artista/banda: ").strip()
            if name:
                crud.add_artist(name)

        elif option == "4":
            artists = crud.list_artists()
            print("\n--- Lista de Artistas ---")
            for art in artists:
                print(f"[{art[0]}] {art[1]}")

        elif option == "5":
            print("\n--- Agregar Nueva Canción ---")
            title = input("Título de la canción: ").strip()
            
            # Mostrar lista de artistas para elegir ID
            artists = crud.list_artists()
            print("\nArtistas disponibles:")
            for art in artists:
                print(f"[{art[0]}] {art[1]}")
            artist_id = input("ID del artista (o presiona Enter para ninguno): ").strip()
            artist_id = int(artist_id) if artist_id else None

            # Mostrar lista de instrumentos para elegir ID
            instruments = crud.list_instruments()
            print("\nInstrumentos disponibles:")
            for inst in instruments:
                print(f"[{inst[0]}] {inst[1]}")
            instrument_id = input("ID del instrumento: ").strip()
            instrument_id = int(instrument_id) if instrument_id else None

            key = input("Tonalidad (ej. Do mayor, Sol maj 7): ").strip()
            tempo = input("Tempo (BPM): ").strip()
            tempo = int(tempo) if tempo.isdigit() else None
            link = input("Enlace a partitura/tablatura: ").strip()
            
            print("Estado: 1. Por aprender | 2. En práctica | 3. Dominado")
            st_opt = input("Opción de estado (1/2/3): ").strip()
            status_map = {"1": "Por aprender", "2": "En práctica", "3": "Dominado"}
            status = status_map.get(st_opt, "Por aprender")

            crud.add_song(title, artist_id, instrument_id, key, tempo, link, status)

        elif option == "6":
            songs = crud.list_songs()
            print("\n--- Repertorio Musical ---")
            print(f"{'ID':<3} | {'Título':<20} | {'Artista':<15} | {'Instrumento':<15} | {'Tonalidad':<10} | {'Estado':<12}")
            print("-" * 85)
            for s in songs:
                print(f"{s[0]:<3} | {s[1]:<20} | {s[2]:<15} | {s[3]:<15} | {str(s[4]):<10} | {s[6]:<12}")

        elif option == "0":
            print("¡Hasta luego!")
            break
        else:
            print("Opción inválida, intenta de nuevo.")

if __name__ == "__main__":
    main()