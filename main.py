import json
import time
import os

EPSILON = 1e-9
STANDARD_LABELS = {"Cross": "Cross", "X": "X"}


def normalize_label(label):
    if not label:
        return label

    l = str(label).lower().strip()
    if l in ["cross", "+"]:
        return "Cross"
    if l == "x":
        return "X"
    return label


def mac_operation(pattern, filter_matrix):
    rows = len(pattern)
    cols = len(pattern[0])
    score = 0.0
    for r in range(rows):
        for c in range(cols):
            score += float(pattern[r][c]) * float(filter_matrix[r][c])
    return score


def get_judge(score_a, score_b, label_a="A", label_b="B"):
    if abs(score_a - score_b) < EPSILON:
        return "UNDECIDED"
    return label_a if score_a > score_b else label_b


def input_matrix(name, size=3):
    print(f"{name} ({size}줄 입력, 공백 구분)")
    matrix = []
    while len(matrix) < size:
        try:
            line = input().strip()
            if not line:
                continue
            row = [float(x) for x in line.split()]
            if len(row) != size:
                print(
                    f"입력 형식 오류: 각 줄에 {size}개의 숫자를 공백으로 구분해 입력하세요."
                )
                continue
            matrix.append(row)
        except ValueError:
            print("입력 형식 오류: 숫자를 입력하세요.")
    return matrix


def measure_performance(pattern, filter_matrix, iterations=10):
    start_time = time.perf_counter()
    for _ in range(iterations):
        mac_operation(pattern, filter_matrix)
    end_time = time.perf_counter()
    avg_time_ms = ((end_time - start_time) / iterations) * 1000
    return avg_time_ms


def mode_user_input():
    print("\n#----------------------------------------")
    print("# [1] 필터 입력")
    print("#---------------------------------------")
    filter_a = input_matrix("필터 A", 3)
    filter_b = input_matrix("필터 B", 3)

    print("\n#---------------------------------------")
    print("# [2] 패턴 입력")
    print("#---------------------------------------")
    pattern = input_matrix("패턴", 3)

    print("\n#---------------------------------------")
    print("# [3] MAC 결과")
    print("#---------------------------------------")
    score_a = mac_operation(pattern, filter_a)
    score_b = mac_operation(pattern, filter_b)

    avg_time = measure_performance(pattern, filter_a, 10)

    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/10회): {avg_time:.4f} ms")

    judgment = get_judge(score_a, score_b, "A", "B")
    if judgment == "UNDECIDED":
        print(f"판정: 판정 불가 (|A-B| < {EPSILON})")
    else:
        print(f"판정: {judgment}")

    print("\n#---------------------------------------")
    print("# [4] 성능 분석")
    print("#---------------------------------------")
    print(f"{'크기':<10} {'평균 시간(ms)':<15} {'연산 횟수':<10}")
    print("-" * 40)
    print(f"{'3x3':<10} {avg_time:<15.4f} {3 * 3:<10}")


def mode_json_analysis():
    if not os.path.exists("data.json"):
        print("Error: data.json file not found.")
        return

    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    print("\n#---------------------------------------")
    print("# [1] 필터 로드")
    print("#---------------------------------------")
    raw_filters = data.get("filters", {})
    processed_filters = {}

    for size_key, f_dict in raw_filters.items():
        size = int(size_key.split("_")[1])
        norm_f_dict = {}
        for k, v in f_dict.items():
            norm_f_dict[normalize_label(k)] = v
        processed_filters[size] = norm_f_dict
        print(f"DONE: {size_key:<7} 필터 로드 완료 ({', '.join(norm_f_dict.keys())})")

    print("\n#---------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#---------------------------------------")
    patterns = data.get("patterns", [])
    results = []
    performance_data = {}

    for p_item in patterns:
        key = p_item.get("key", "unknown")
        input_data = p_item.get("input", [])
        expected = normalize_label(p_item.get("expected"))

        print(f"- -- {key} ---")

        try:
            parts = key.split("_")
            size = int(parts[1])
        except (IndexError, ValueError):
            print(f"FAIL: Invalid key format '{key}'")
            results.append(
                {"key": key, "status": "FAIL", "reason": f"Invalid key format '{key}'"}
            )
            continue

        if len(input_data) != size or (
            len(input_data) > 0 and len(input_data[0]) != size
        ):
            reason = f"패턴 크기 불일치 (Expected {size}x{size}, got {len(input_data)}x{len(input_data[0]) if input_data else 0})"
            print(f"FAIL: {reason}")
            results.append({"key": key, "status": "FAIL", "reason": reason})
            continue

        filters = processed_filters.get(size)
        if not filters:
            reason = f"해당 크기({size})의 필터가 로드되지 않음"
            print(f"FAIL: {reason}")
            results.append({"key": key, "status": "FAIL", "reason": reason})
            continue

        scores = {}
        for label, f_matrix in filters.items():
            if len(f_matrix) != size or (
                len(f_matrix) > 0 and len(f_matrix[0]) != size
            ):
                scores[label] = None
                continue

            score = mac_operation(input_data, f_matrix)
            scores[label] = score
            print(f"{label} 점수: {score}")

            if size not in performance_data:
                performance_data[size] = []
            performance_data[size].append(measure_performance(input_data, f_matrix, 10))

        label_cross = "Cross"
        label_x = "X"
        score_cross = scores.get(label_cross)
        score_x = scores.get(label_x)

        if score_cross is None or score_x is None:
            reason = "필터 데이터 오류"
            print(f"FAIL: {reason}")
            results.append({"key": key, "status": "FAIL", "reason": reason})
            continue

        judgment = get_judge(score_cross, score_x, label_cross, label_x)
        pass_fail = "PASS" if judgment == expected else "FAIL"

        print(f"판정: {judgment} | expected: {expected} | {pass_fail}")

        results.append(
            {
                "key": key,
                "status": pass_fail,
                "reason": f"판정({judgment}) != 기대값({expected})"
                if pass_fail == "FAIL"
                else "",
            }
        )

    print("\n#---------------------------------------")
    print("# [3] 성능 분석 (평균/10회)")
    print("#---------------------------------------")
    print(f"{'크기':<10} {'평균 시간(ms)':<15} {'연산 횟수':<10}")
    print("-" * 40)

    for size in sorted(performance_data.keys()):
        avg_time = sum(performance_data[size]) / len(performance_data[size])
        print(f"{f'{size}x{size}':<10} {avg_time:<15.4f} {size * size:<10}")

    print("\n#---------------------------------------")
    print("# [4] 결과 요약")
    print("#---------------------------------------")
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = total - passed

    print(f"총 테스트: {total}개")
    print(f"통과: {passed}개")
    print(f"실패: {failed}개")

    if failed > 0:
        print("\n실패 케이스:")
        for r in results:
            if r["status"] == "FAIL":
                print(f"- {r['key']}: {r['reason']}")


def main():
    print("=== Mini NPU Simulator ===")
    print("\n[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")

    choice = input("선택: ").strip()

    if choice == "1":
        mode_user_input()
    elif choice == choice == "2":
        mode_json_analysis()
    else:
        print("잘못된 선택입니다.")


if __name__ == "__main__":
    main()
