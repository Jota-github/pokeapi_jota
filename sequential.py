import requests
import os
import stat
import time
import shutil


OUTPUT_DIR = "pokemon_images"
RUNS = 10


def fetch_image_url(pokemon_id: int) -> str | None:
    """
    Consulta a PokéAPI e retorna a URL do sprite frontal padrão do Pokémon.
    Retorna None se a requisição falhar ou o sprite não existir.
    """
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data["sprites"]["front_default"]
    except requests.exceptions.RequestException as e:
        print(f"  [ERRO] Pokémon #{pokemon_id} — falha na requisição: {e}")
        return None


def download_image(image_url: str, filepath: str) -> bool:
    """
    Faz o download de uma imagem a partir de uma URL e salva no caminho indicado.
    Retorna True em caso de sucesso, False em caso de falha.
    """
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(response.content)
        return True
    except requests.exceptions.RequestException as e:
        print(f"  [ERRO] Download falhou para {image_url}: {e}")
        return False


def run_once(quantity: int) -> float:
    """
    Executa uma rodada completa de download sequencial para `quantity` Pokémons.
    Apaga e recria o diretório de saída antes de começar, garantindo
    que todas as imagens sejam baixadas do zero (benchmark justo).

    Retorna o tempo total de execução em segundos.
    """
    # Limpa o diretório para forçar o download completo a cada rodada.
    # O handler abaixo corrige o erro de permissão somente-leitura no Windows
    # antes de tentar deletar cada arquivo/pasta.
    def _force_remove(func, path, _):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR, onerror=_force_remove)
    os.makedirs(OUTPUT_DIR)

    start_time = time.time()

    for pokemon_id in range(1, quantity + 1):
        filepath = os.path.join(OUTPUT_DIR, f"{pokemon_id}.png")

        image_url = fetch_image_url(pokemon_id)
        if image_url is None:
            continue

        download_image(image_url, filepath)

    return time.time() - start_time


def benchmark_sequential(quantity: int, runs: int = RUNS) -> None:
    """
    Executa `runs` vezes o download sequencial de `quantity` Pokémons
    e exibe a média do tempo de execução.

    Parâmetros
    ----------
    quantity : int
        Número de Pokémons a baixar por rodada (100, 500 ou 1000).
    runs : int
        Quantidade de rodadas para calcular a média (padrão: 10).
    """
    print(f"\n{'='*55}")
    print(f"  Benchmark sequencial")
    print(f"  Pokémons por rodada : {quantity}")
    print(f"  Número de rodadas   : {runs}")
    print(f"{'='*55}")

    times = []

    for i in range(1, runs + 1):
        print(f"  Rodada {i:>2}/{runs} ...", end=" ", flush=True)
        elapsed = run_once(quantity)
        times.append(elapsed)
        print(f"{elapsed:.2f}s")

    avg = sum(times) / len(times)
    minimum = min(times)
    maximum = max(times)

    print(f"\n  --- Resultados ({quantity} Pokémons, {runs} rodadas) ---")
    print(f"  Tempo mínimo  : {minimum:.2f}s")
    print(f"  Tempo máximo  : {maximum:.2f}s")
    print(f"  Tempo médio   : {avg:.2f}s")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    # Altere o valor abaixo para testar com 100, 500 ou 1000 imagens
    QUANTITY = 100

    benchmark_sequential(quantity=QUANTITY, runs=RUNS)
