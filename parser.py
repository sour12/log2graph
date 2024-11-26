import re

def find_longest_unique_string(log_data):
    unique_strings = set()                # 유니크한 문자열을 저장할 set
    longest_word  = ""                    # 가장 긴 단어를 저장할 변수
    longest_index = -1                    # 가장 긴 단어의 인덱스
    words = re.findall(r'\S+', log_data)  # \S+는 공백이 아닌 문자들의 연속을 찾음

    for idx, word in enumerate(words):
        # 숫자가 포함되지 않은 유니크한 단어만 찾기
        if not re.search(r'\d', word) and word not in unique_strings:
            unique_strings.add(word)
            # 현재 단어가 가장 긴 단어라면 갱신
            if len(word) > len(longest_word):
                longest_word = word
                longest_index = idx

    return longest_index, longest_word

def find_pattern_index(text, pattern_offset):
    lines = text.split("\n")
    # selected_text = lines[pattern_offset[0] - 1][pattern_offset[1]:pattern_offset[3]]

    tokens = []
    for line_num, line in enumerate(lines, start=1):
        line_tokens = line.split()
        tokens.extend((token, line_num, line.find(token)) for token in line_tokens)  # 단어, 라인번호, 각 단어의 시작 오프셋 추가

    for global_index, (token, line_num, token_start_offset) in enumerate(tokens):
        token_end_offset = token_start_offset + len(token)  # 토큰의 끝 오프셋 계산
        # 지정된 라인 & 지정된 오프셋 범위 내에 위치한 단어만 찾기
        if pattern_offset[0] == line_num and (pattern_offset[1] >= token_start_offset and pattern_offset[3] <= token_end_offset):
            return global_index, token

    return -1, ""

def extract_first_number(text):
    # 정규 표현식으로 첫 번째 숫자 (정수 또는 소수 포함) 추출
    match = re.search(r'-?\d+(\.\d+)?', text)
    if match:
        return float(match.group())
    else:
        return None

def parser_main(logdata, repeat_line, pattern_offset):
    unique_idx = -1
    unique_str = ""
    pattern_idx = [-1] * len(pattern_offset)
    pattern_str = [""] * len(pattern_offset)
    return_data = []

    select_line = logdata.splitlines()[repeat_line[0]-1:repeat_line[1]]
    select_str  = '\n'.join(select_line)

    # find idx
    unique_idx, unique_str = find_longest_unique_string(select_str)
    print("[Unique] idx : {} / str : '{}'".format(unique_idx, unique_str))
    for i in range(len(pattern_offset)):
        if pattern_offset[i] != [0, 0, 0, 0]:
            pattern_idx[i], pattern_str[i] = find_pattern_index(select_str, pattern_offset[i])
            print("[Pattern][{}] idx : {} / str : '{}'".format(i, pattern_idx[i], pattern_str[i]))

    # find data
    split_logdata = logdata.split()
    for idx, data in enumerate(split_logdata):
        if data == unique_str:
            parsing_data = [None] * len(pattern_offset)
            parsing_num  = [None] * len(pattern_offset)
            for i in range(len(pattern_offset)):
                if pattern_offset[i] != [0, 0, 0, 0]:
                    parsing_data[i] = split_logdata[idx + (pattern_idx[i] - unique_idx)]
                    parsing_num[i]  = extract_first_number(parsing_data[i])
                    print("[PatternData][{}] {} / {}".format(i, extract_first_number(parsing_data[i]), parsing_data[i]))
            return_data.append(parsing_num)

    # return data array
    return return_data