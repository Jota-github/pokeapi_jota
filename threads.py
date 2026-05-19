import requests
import os
import stat
import time
import shutil
import threading


OUTPUT_DIR = "pokemon_images"
RUNS = 5


def fetch_and_download(pokemon_id: int, semaphore: threading.Semaphore) -> None:
    """
    Consulta a PokéAPI, obtém a URL do sprite e faz o download da imagem.
    O semáforo limita quantas threads executam simultaneamente.
    """
    with semaphore:
        url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            image_url = response.json().get("sprites", {}).get("front_default")

            if image_url is None:
                return

            img_response = requests.get(image_url, timeout=10)
            img_response.raise_for_status()

            filepath = os.path.join(OUTPUT_DIR, f"{pokemon_id}.png")
            with open(filepath, "wb") as f:
                f.write(img_response.content)

        except requests.exceptions.RequestException:
            pass


def run_once(quantity: int, num_workers: int) -> float:
    """
    Executa uma rodada completa de download paralelo com `num_workers` threads.
    Usa Semaphore para controlar a concorrência — todas as threads são criadas
    de uma vez, mas apenas `num_workers` executam ao mesmo tempo.

    Retorna o tempo total de execução em segundos.
    """
    def _force_remove(func, path, _):
        os.chmod(path, stat.S_IWRITE)
        for _ in range(10):
            try:
                func(path)
                return
            except PermissionError:
                time.sleep(0.2)
        func(path)

    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR, onerror=_force_remove)
    os.makedirs(OUTPUT_DIR)

    semaphore = threading.Semaphore(num_workers)
    ids = list(range(1, quantity + 1))
    threads = []

    start_time = time.time()

    for pokemon_id in ids:
        t = threading.Thread(
            target=fetch_and_download,
            args=(pokemon_id, semaphore),
            daemon=True
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout=60)

    return time.time() - start_time


def benchmark_threading(quantity: int, num_workers: int, runs: int = RUNS) -> None:
    """
    Executa `runs` vezes o download paralelo com `num_workers` threads
    para `quantity` Pokémons e exibe a média do tempo de execução.

    Parâmetros
    ----------
    quantity    : Número de Pokémons por rodada (50, 250 ou 500).
    num_workers : Número de threads simultâneas (2, 4 ou 8).
    runs        : Número de rodadas para a média (padrão: 5).
    """
    print(f"\n{'='*55}")
    print(f"  Benchmark threading")
    print(f"  Pokémons por rodada : {quantity}")
    print(f"  Threads             : {num_workers}")
    print(f"  Número de rodadas   : {runs}")
    print(f"{'='*55}")

    times = []

    for i in range(1, runs + 1):
        print(f"  Rodada {i:>2}/{runs} ...", end=" ", flush=True)
        elapsed = run_once(quantity, num_workers)
        times.append(elapsed)
        print(f"{elapsed:.2f}s")

    avg = sum(times) / len(times)
    minimum = min(times)
    maximum = max(times)

    print(f"\n  --- Resultados ({quantity} Pokémons, {num_workers} threads, {runs} rodadas) ---")
    print(f"  Tempo mínimo  : {minimum:.2f}s")
    print(f"  Tempo máximo  : {maximum:.2f}s")
    print(f"  Tempo médio   : {avg:.2f}s")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    for quantity in [50, 250, 500]:
        for num_workers in [2, 4, 8]:
            benchmark_threading(quantity=quantity, num_workers=num_workers, runs=RUNS)
