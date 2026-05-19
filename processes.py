import requests
import os
import stat
import time
import shutil
from multiprocessing import Pool


OUTPUT_DIR = "pokemon_images"
RUNS = 5


def fetch_and_download(pokemon_id: int) -> None:
    """
    Consulta a PokéAPI, obtém a URL do sprite e faz o download da imagem.
    Executada por cada processo do pool individualmente.
    Precisa ser função de módulo (não pode ser lambda ou função aninhada)
    para ser serializável pelo multiprocessing.
    """
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


def _force_remove(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    for _ in range(10):
        try:
            func(path)
            return
        except PermissionError:
            time.sleep(0.2)
    func(path)


def run_once(quantity: int, num_workers: int) -> float:
    """
    Executa uma rodada completa de download paralelo com `num_workers` processos.
    Apaga e recria o diretório antes de cada rodada para benchmark justo.

    Retorna o tempo total de execução em segundos.
    """
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR, onerror=_force_remove)
    os.makedirs(OUTPUT_DIR)

    ids = list(range(1, quantity + 1))

    start_time = time.time()

    with Pool(processes=num_workers) as pool:
        pool.map(fetch_and_download, ids)

    return time.time() - start_time


def benchmark_multiprocessing(quantity: int, num_workers: int, runs: int = RUNS) -> None:
    """
    Executa `runs` vezes o download paralelo com `num_workers` processos
    para `quantity` Pokémons e exibe a média do tempo de execução.

    Parâmetros
    ----------
    quantity    : Número de Pokémons por rodada (100, 500 ou 1000).
    num_workers : Número de processos simultâneos (2, 4 ou 8).
    runs        : Número de rodadas para a média (padrão: 10).
    """
    print(f"\n{'='*55}")
    print(f"  Benchmark multiprocessing")
    print(f"  Pokémons por rodada : {quantity}")
    print(f"  Processos           : {num_workers}")
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

    print(f"\n  --- Resultados ({quantity} Pokémons, {num_workers} processos, {runs} rodadas) ---")
    print(f"  Tempo mínimo  : {minimum:.2f}s")
    print(f"  Tempo máximo  : {maximum:.2f}s")
    print(f"  Tempo médio   : {avg:.2f}s")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    for quantity in [50, 250, 500]:
        for num_workers in [2, 4, 8]:
            benchmark_multiprocessing(quantity=quantity, num_workers=num_workers, runs=RUNS)
