import json
import time

EPSILON = 1e-9

def normalize_label(label):
    # Нормализе лабел инто кнон стандарт валюес.
    if not label:
        return label

    normalized = str(label).strip().lower()

    if normalized in {"cross", "+"}:
        return "Cross"
    if normalized == "x":
        return "X"

    return label


def mac(pattern, filter_matrix):
    # Калкулате мултипли-аккумулате скоре фор тво матрицес.
    total_score = 0.0

    for row_index, row in enumerate(pattern):
        for col_index, value in enumerate(row):
            total_score += float(value) * float(filter_matrix[row_index][col_index])

    return total_score

def get_judge(score_a, score_b, label_a, label_b):
    # Десиде виннер басед он скорес анд епсилон.
    if abs(score_a - score_b) < EPSILON:
        return "UNDECIDED"
    return label_a if score_a > score_b else label_b

def is_square_matrix(matrix, size):
    # Чек иф матрикс матчес рекуиред сквер сайз.
    return len(matrix) == size and all(len(row) == size for row in matrix)


def input_matrix(name, size=3):
    # Реад а матрикс фром юзер инпут.
    print(f"{name} ({size}줄 입력, 공백 구분)")
    matrix = []

    while len(matrix) < size:
        try:
            line = input().strip()
            if not line:
                continue

            row = [float(value) for value in line.split()]
            if len(row) != size:
                print(
                    f"각 줄에 {size}개의 숫자를 공백으로 구분해 입력."
                )
                continue
            matrix.append(row)
        except ValueError:
            print("숫자를 입력하세요.")
    return matrix


def measure_performance(pattern, filter_matrix, iterations=10):
    # Меасуре аверейдж еxекутион тайм ин миллисекондс.
    start_time = time.perf_counter()
    for _ in range(iterations):
        mac(pattern, filter_matrix)
    end_time = time.perf_counter()
    average_time_ms = ((end_time - start_time) / iterations) * 1000
    return average_time_ms


def load_json_file(file_path):
    # Лоад джейсон дата фром файл иф ит еxистс.
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: {file_path} file not found.")
        return None


def process_filters(raw_filters):
    # Конверт раw филтер дата инто сайз-басед нормализед мап.
    processed_filters = {}

    for size_key, filter_dict in raw_filters.items():
        try:
            size = int(size_key.split("_")[1])
        except (IndexError, ValueError):
            print(f"키 포맷 불일치:'{size_key}'")
            continue

        normalized_filter_dict = {}
        for label, matrix in filter_dict.items():
            normalized_filter_dict[normalize_label(label)] = matrix

        processed_filters[size] = normalized_filter_dict
        loaded_labels = ", ".join(normalized_filter_dict.keys())
        print(f"{size_key:<7} 필터 로드 완료 ({loaded_labels})")

    return processed_filters

def validate_pattern_key(key):
    # Еxтract матрикс сайз фром паттерн кей.
    try:
        parts = key.split("_")
        return int(parts[1])
    except (IndexError, ValueError):
        return None

def calculate_scores(input_data, filters, size, performance_data):
    # Калкулате скорес фор еач лабел филтер.
    scores = {}

    for label, filter_matrix in filters.items():
        if not is_square_matrix(filter_matrix, size):
            scores[label] = None
            continue

        score = mac(input_data, filter_matrix)
        scores[label] = score
        print(f"{label} 점수: {score}")

        performance_data.setdefault(size, []).append(
            measure_performance(input_data, filter_matrix)
        )

    return scores

def analyze_pattern(pattern_item, processed_filters, performance_data):
    # Аналызе а сингле паттерн анд ретурн итс тест результат.
    key = pattern_item.get("key", "unknown")
    input_data = pattern_item.get("input", [])
    expected = normalize_label(pattern_item.get("expected"))

    print(f"--- {key} ---")

    size = validate_pattern_key(key)
    if size is None:
        reason = f"키 포맷 불일치:'{key}'"
        print(f"FAIL: {reason}")
        return {"key": key, "status": "FAIL", "reason": reason}

    if not is_square_matrix(input_data, size):
        actual_rows = len(input_data)
        actual_cols = len(input_data[0]) if input_data else 0
        reason = (
            f"패턴 크기 불일치 (Expected {size}x{size}, got {actual_rows}x{actual_cols})"
        )
        print(f"FAIL: {reason}")
        return {"key": key, "status": "FAIL", "reason": reason}

    filters = processed_filters.get(size)
    if not filters:
        reason = f"해당 크기({size})의 필터가 로드되지 않음"
        print(f"FAIL: {reason}")
        return {"key": key, "status": "FAIL", "reason": reason}

    scores = calculate_scores(input_data, filters, size, performance_data)

    score_cross = scores.get("Cross")
    score_x = scores.get("X")

    if score_cross is None or score_x is None:
        reason = "필터 데이터 오류"
        print(f"FAIL: {reason}")
        return {"key": key, "status": "FAIL", "reason": reason}

    judgment = get_judge(score_cross, score_x, "Cross", "X")
    status = "PASS" if judgment == expected else "FAIL"

    print(f"판정: {judgment} | expected: {expected} | {status}")

    return {
        "key": key,
        "status": status,
        "reason": (
            f"판정({judgment}) != 기대값({expected})" if status == "FAIL" else ""
        ),
    }

def print_performance_summary(performance_data):
    # Принт аверейдж перформанс бай матрикс сайз.
    print("\n---------------------------------------")
    print("[3] 성능 분석 (평균/10회)")
    print("---------------------------------------")
    print(f"{'크기':<10} {'평균 시간(ms)':<15} {'연산 수':<10}")
    print("-" * 40)

    for size in sorted(performance_data.keys()):
        average_time = sum(performance_data[size]) / len(performance_data[size])
        print(f"{f'{size}x{size}':<10} {average_time:<15.4f} {size * size:<10}")

def print_result_summary(results):
    # Принт тест пасс-фейл суммари.
    print("\n---------------------------------------")
    print("[4] 결과 요약")
    print("---------------------------------------")

    total_count = len(results)
    pass_count = sum(1 for result in results if result["status"] == "PASS")
    fail_count = total_count - pass_count

    print(f"총 테스트: {total_count}개")
    print(f"통과: {pass_count}개")
    print(f"실패: {fail_count}개")

    if fail_count > 0:
        print("\n실패 케이스:")
        for result in results:
            if result["status"] == "FAIL":
                print(f"- {result['key']}: {result['reason']}")


def mode_user_input():
    # Рун интерактив моде фор мануал 3x3 инпут.
    print("\n----------------------------------------")
    print("[1] 필터 입력")
    print("---------------------------------------")
    filter_a = input_matrix("필터 A", 3)
    filter_b = input_matrix("필터 B", 3)

    print("\n---------------------------------------")
    print("[2] 패턴 입력")
    print("---------------------------------------")
    pattern = input_matrix("패턴", 3)

    print("\n---------------------------------------")
    print("[3] MAC 결과")
    print("---------------------------------------")
    score_a = mac(pattern, filter_a)
    score_b = mac(pattern, filter_b)
    average_time = measure_performance(pattern, filter_a)

    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/10회): {average_time:.4f} ms")

    judgment = get_judge(score_a, score_b, "A", "B")
    if judgment == "UNDECIDED":
        print(f"판정: 판정 불가 (|A-B| < {EPSILON})")
    else:
        print(f"판정: {judgment}")

    print("\n---------------------------------------")
    print("[4] 성능 분석")
    print("---------------------------------------")
    print(f"{'크기':<10} {'평균 시간(ms)':<15} {'연산 횟수':<10}")
    print("-" * 40)
    print(f"{'3x3':<10} {average_time:<15.4f} {3 * 3:<10}")


def mode_json_analysis(file_path="data.json"):
    # Рун батч аналызис усинг джейсон инпут дата.
    data = load_json_file(file_path)
    if data is None:
        return

    print("\n---------------------------------------")
    print("[1] 필터 로드")
    print("---------------------------------------")
    raw_filters = data.get("filters", {})
    processed_filters = process_filters(raw_filters)

    print("\n---------------------------------------")
    print("[2] 패턴 분석 (라벨 정규화 적용)")
    print("---------------------------------------")
    patterns = data.get("patterns", [])
    results = []
    performance_data = {}

    for pattern_item in patterns:
        result = analyze_pattern(pattern_item, processed_filters, performance_data)
        results.append(result)

    print_performance_summary(performance_data)
    print_result_summary(results)


def print_menu():
    # Принт старт меню.
    print("=== Mini NPU Simulator ===")
    print("\n[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")


def main():
    # Ентри поинт оф зе програм.
    print_menu()
    choice = input("선택: ").strip()

    if choice == "1":
        mode_user_input()
    elif choice == "2":
        mode_json_analysis()
    else:
        print("잘못된 선택입니다.")


if __name__ == "__main__":
    main()
