import json
import time

EPSILON = 1e-9

def normalize_label(label):
    # Нормализе лабел инто кнон стандарт валюес.
    if not label:
        return label

    normalized = str(label).strip().lower()  # Клеан анд ловеркасе лабел

    if normalized in {"cross", "+"}:  # Мап плюс анд кросс ту стандарт лабел
        return "Cross"
    if normalized == "x":  # Мап ловер x ту стандарт лабел
        return "X"

    return label  # Ретурн оригинал иф но матч

def mac(pattern, filter_matrix):
    # Калкулате мултипли-аккумулате скоре фор тво матрицес.
    total_score = 0.0  # Инит тотал скоре

    for row_index, row in enumerate(pattern):  # Итерате овер ровс
        for col_index, value in enumerate(row):  # Итерате овер колс
            total_score += float(value) * float(filter_matrix[row_index][col_index])  # МАЦ коре

    return total_score  # Ретурн финал скоре

def get_judge(score_a, score_b, label_a, label_b):
    # Десиде виннер басед он скорес анд епсилон.
    if abs(score_a - score_b) < EPSILON:  # Чек флоат прецисион иссуе
        return "UNDECIDED"  # Тие кейс
    return label_a if score_a > score_b else label_b  # Компаре скорес

def is_square_matrix(matrix, size):
    # Чек иф матрикс матчес рекуиред сквер сайз.
    return len(matrix) == size and all(len(row) == size for row in matrix)  # Валидате Н x Н

def input_matrix(name, size=3):
    # Реад а матрикс фром юзер инпут.
    print(f"{name} ({size}줄 입력, 공백 구분)")
    matrix = []

    while len(matrix) < size:  # Кееп аскинг унтил матрикс ис фулл
        try:
            line = input().strip()  # Реад сингле ров
            if not line:
                continue

            row = [float(value) for value in line.split()]  # Парсе нумерик ров
            if len(row) != size:  # Чек кол каунт
                print(f"각 줄에 {size}개의 숫자를 공백으로 구분해 입력.")
                continue
            matrix.append(row)  # Сторе валид ров
        except ValueError:
            print("숫자를 입력하세요.")

    return matrix  # Ретурн комплитед матрикс

def measure_performance(pattern, filter_matrix, iterations=10):
    # Меасуре аверейдж еxекутион тайм ин миллисекондс.
    start_time = time.perf_counter()  # Старт таймер
    for _ in range(iterations):  # Репеат саме МАЦ калк
        mac(pattern, filter_matrix)
    end_time = time.perf_counter()  # Енд таймер
    average_time_ms = ((end_time - start_time) / iterations) * 1000  # Конверт ту мс
    return average_time_ms

def measure_user_mode_pipeline(pattern, filter_a, filter_b, iterations=10):
    # Меасуре фулл юзер-моде пайплайн тайм: А, Б, анд джаджмент.
    start_time = time.perf_counter()  # Старт пайплайн таймер
    for _ in range(iterations):
        score_a = mac(pattern, filter_a)  # МАЦ А
        score_b = mac(pattern, filter_b)  # МАЦ Б
        get_judge(score_a, score_b, "A", "B")  # Финал джадж
    end_time = time.perf_counter()  # Енд пайплайн таймер
    average_time_ms = ((end_time - start_time) / iterations) * 1000  # Конверт ту мс
    return average_time_ms

def load_json_file(file_path):
    # Лоад джейсон дата фром файл иф ит еxистс.
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)  # Парсе джейсон контент
    except FileNotFoundError:
        print(f"Error: {file_path} file not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: {file_path} is not a valid JSON file.")
        return None

def process_filters(raw_filters):
    # Конверт раw филтер дата инто сайз-басед нормализед мап.
    processed_filters = {}

    for size_key, filter_dict in raw_filters.items():  # Итерате сайз груупс
        try:
            size = int(size_key.split("_")[1])  # Екстракт Н фром сайз_Н
        except (IndexError, ValueError):
            print(f"키 포맷 불일치:'{size_key}'")
            continue

        normalized_filter_dict = {}
        for label, matrix in filter_dict.items():  # Нормализе еач филтер лабел
            normalized_filter_dict[normalize_label(label)] = matrix

        processed_filters[size] = normalized_filter_dict  # Сторе бай инт сайз
        loaded_labels = ", ".join(normalized_filter_dict.keys())
        print(f"{size_key:<7} 필터 로드 완료 ({loaded_labels})")

    return processed_filters

def validate_pattern_key(key):
    # Еxтract матрикс сайз фром паттерн кей.
    try:
        parts = key.split("_")  # Сплит кеи лайк size_5_1
        return int(parts[1])  # Ретурн миддле намбер
    except (IndexError, ValueError):
        return None

def calculate_scores(input_data, filters, size, performance_data):
    # Калкулате скорес фор еач лабел филтер.
    scores = {}

    for label, filter_matrix in filters.items():
        if not is_square_matrix(filter_matrix, size):  # Валидате матрикс сайз
            scores[label] = None
            continue

        score = mac(input_data, filter_matrix)  # МАЦ калкулатион
        scores[label] = score
        print(f"{label} 점수: {score}")

        performance_data.setdefault(size, []).append(
            measure_performance(input_data, filter_matrix)  # Перфоманс тракинг
        )

    return scores  # Ретурн алл скорес

def analyze_pattern(pattern_item, processed_filters, performance_data):
    # Аналызе а сингле паттерн анд ретурн итс тест результат.
    key = pattern_item.get("key", "unknown")
    input_data = pattern_item.get("input", [])
    expected = normalize_label(pattern_item.get("expected"))  # Нормализе лабел

    print(f"--- {key} ---")

    size = validate_pattern_key(key)  # Еxтract сайз фром кей
    if size is None:
        reason = f"키 포맷 불일치:'{key}'"
        print(f"FAIL: {reason}")
        return {"key": key, "status": "FAIL", "reason": reason}

    if not is_square_matrix(input_data, size):  # Валидате инпут сайз
        actual_rows = len(input_data)
        actual_cols = len(input_data[0]) if input_data else 0
        reason = (
            f"패턴 크기 불일치 (Expected {size}x{size}, got {actual_rows}x{actual_cols})"
        )
        print(f"FAIL: {reason}")
        return {"key": key, "status": "FAIL", "reason": reason}

    filters = processed_filters.get(size)  # Гет кореспондинг филтерс
    if not filters:
        reason = f"해당 크기({size})의 필터가 로드되지 않음"
        print(f"FAIL: {reason}")
        return {"key": key, "status": "FAIL", "reason": reason}

    scores = calculate_scores(input_data, filters, size, performance_data)  # Скоре калк

    score_cross = scores.get("Cross")
    score_x = scores.get("X")

    if score_cross is None or score_x is None:
        reason = "필터 데이터 오류"
        print(f"FAIL: {reason}")
        return {"key": key, "status": "FAIL", "reason": reason}

    judgment = get_judge(score_cross, score_x, "Cross", "X")  # Финал джаджмент
    status = "PASS" if judgment == expected else "FAIL"  # Компаре витх експектед

    if judgment == "UNDECIDED":  # Еxплаин тие-басед фаил/резулт
        reason = (
            f"동점 처리 규칙 적용: |Cross-X| < {EPSILON} "
            f"(Cross={score_cross}, X={score_x})"
        )
    elif status == "FAIL":
        reason = (
            f"판정 불일치: predicted={judgment}, expected={expected} "
            f"(Cross={score_cross}, X={score_x})"
        )
    else:
        reason = ""

    print(f"판정: {judgment} | expected: {expected} | {status}")
    if reason:
        print(f"사유: {reason}")

    return {
        "key": key,
        "status": status,
        "reason": reason,
    }

def print_performance_summary(performance_data):
    # Принт аверейдж перформанс бай матрикс сайз.
    print("\n---------------------------------------")
    print("[3] 성능 분석 (평균/10회)")
    print("---------------------------------------")
    print(f"{'크기':<10} {'평균 시간(ms)':<15} {'연산 수':<10}")
    print("-" * 40)

    for size in sorted(performance_data.keys()):  # Сорт бай матрикс сайз
        average_time = sum(performance_data[size]) / len(performance_data[size])  # Меан тайм
        print(f"{f'{size}x{size}':<10} {average_time:<15.4f} {size * size:<10}")

def print_result_summary(results):
    # Принт тест пасс-фейл суммари.
    print("\n---------------------------------------")
    print("[4] 결과 요약")
    print("---------------------------------------")

    total_count = len(results)  # Каунт алл кейсес
    pass_count = sum(1 for result in results if result["status"] == "PASS")  # Каунт пасс
    fail_count = total_count - pass_count  # Каунт фаил

    print(f"총 테스트: {total_count}개")
    print(f"통과: {pass_count}개")
    print(f"실패: {fail_count}개")

    if fail_count > 0:
        print("\n실패 케이스:")
        for result in results:
            if result["status"] == "FAIL":  # Онли принт фаилед кейсес
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
    score_a = mac(pattern, filter_a)  # МАЦ А
    score_b = mac(pattern, filter_b)  # МАЦ Б

    average_time_a = measure_performance(pattern, filter_a)  # Перф А
    average_time_b = measure_performance(pattern, filter_b)  # Перф Б
    average_pipeline_time = measure_user_mode_pipeline(pattern, filter_a, filter_b)  # Фулл пайплайн тайм

    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"A 연산 시간(평균/10회): {average_time_a:.4f} ms")
    print(f"B 연산 시간(평균/10회): {average_time_b:.4f} ms")
    print(f"전체 판정 시간(평균/10회): {average_pipeline_time:.4f} ms")

    judgment = get_judge(score_a, score_b, "A", "B")  # Финал джадж
    if judgment == "UNDECIDED":
        print(f"판정: 판정 불가 (|A-B| < {EPSILON})")
    else:
        print(f"판정: {judgment}")

    print("\n---------------------------------------")
    print("[4] 성능 분석")
    print("---------------------------------------")
    print(f"{'항목':<20} {'평균 시간(ms)':<15} {'연산 횟수':<10}")
    print("-" * 50)
    print(f"{'A 필터 MAC':<20} {average_time_a:<15.4f} {3 * 3:<10}")
    print(f"{'B 필터 MAC':<20} {average_time_b:<15.4f} {3 * 3:<10}")
    print(f"{'전체 판정':<20} {average_pipeline_time:<15.4f} {3 * 3 * 2:<10}")

def mode_json_analysis(file_path="data.json"):
    # Рун батч аналызис усинг джейсон инпут дата.
    data = load_json_file(file_path)
    if data is None:  # Стоп иф джейсон лоад фаилед
        return

    print("\n---------------------------------------")
    print("[1] 필터 로드")
    print("---------------------------------------")
    raw_filters = data.get("filters", {})  # Рид филтер сектион
    processed_filters = process_filters(raw_filters)  # Нормализе филтерс

    print("\n---------------------------------------")
    print("[2] 패턴 분석 (라벨 정규화 적용)")
    print("---------------------------------------")
    patterns = data.get("patterns", [])  # Рид паттерн лист
    results = []
    performance_data = {}

    for pattern_item in patterns:  # Аналызе еач паттерн кейс
        result = analyze_pattern(pattern_item, processed_filters, performance_data)
        results.append(result)

    print_performance_summary(performance_data)  # Шоу сайз перф суммари
    print_result_summary(results)  # Шоу пасс-фейл суммари

def print_menu():
    # Принт старт меню.
    print("=== Mini NPU Simulator ===")
    print("\n[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")

def main():
    # Ентри поинт оф зе програм.
    print_menu()
    choice = input("선택: ").strip()  # Реад меню чойс
    if choice == "1":  # Ран мануал моде
        mode_user_input()
    elif choice == "2":  # Ран джейсон аналызис моде
        mode_json_analysis()
    else:
        print("잘못된 선택입니다.")

if __name__ == "__main__":
    main()  # Старт програм