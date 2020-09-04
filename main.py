import itertools
from pprint import pprint
from collections import defaultdict

def damerau_levenshtein_distance(str_a, str_b, *, deletion_cost=1, insertion_cost=1, substitution_cost=1, transposition_cost=1):
    v0 = [0] * (len(str_b) + 1)
    v1 = [i * insertion_cost for i in range(len(str_b) + 1)]
    v2 = [0] * (len(str_b) + 1)

    for i in range(len(str_a)):
        v2[0] = (i + 1) * deletion_cost

        for j in range(len(str_b)):
            v2[j + 1] = min(
                v1[j + 1] + deletion_cost,
                v2[j] + insertion_cost,
                v1[j] + (str_a[i] != str_b[j]) * substitution_cost)
            if i > 0 and j > 0 and str_a[i] == str_b[j - 1] and str_a[i - 1] == str_b[j]:
                v2[j + 1] = min(
                    v2[j + 1],
                    v0[j - 1] + transposition_cost)

        v0, v1, v2 = v1, v2, v0
    return v1[-1]

def is_partial_fuzzy_match(partial_str, full_str):
    if partial_str in full_str:
        return True

    max_error = len(partial_str) // 8 + 1 if len(partial_str) > 1 else 0
    for i in range(max(0, len(full_str) - len(partial_str) - max_error) + 1):
        window_str = full_str[i:i + len(partial_str) + max_error]
        score = damerau_levenshtein_distance(partial_str, window_str)
        if score <= max_error:
            return True
    return False

def split_and_normalize(text: str):
    return [token for token in text.lower().split(" ") if token != " "]

def match_token_initials(query_token, result_tokens, start=0):
    if start >= len(result_tokens):
        return None

    query_index = 0
    token_index = start
    char_index = 0
    used_result_token_indices = set()
    while query_index < len(query_token):
        current_char = query_token[query_index]
        while True:
            if token_index >= len(result_tokens):
                return match_token_initials(query_token, result_tokens, start + 1)
            result_token = result_tokens[token_index]
            if char_index < len(result_token) and result_token[char_index] == current_char:
                used_result_token_indices.add(token_index)
                query_index += 1
                char_index += 1
                break
            token_index += 1
            char_index = 0
    return used_result_token_indices

def matches_single_token_start(query, result_tokens):
    for i, result_token in enumerate(result_tokens):
        if result_token.startswith(query):
            return i
    return -1

def query_match_score(query, result):
    '''
    Returns a score that is smaller the better the query and result match.
    If they don't seem to match at all, None is returned.
    '''
    query_tokens = split_and_normalize(query)
    result_tokens = split_and_normalize(result)
    result_token_count_at_start = len(result_tokens)

    for query_token_index, query_token in enumerate(query_tokens):
        # Check if a result token begins with the query token.
        exact_start_index = matches_single_token_start(query_token, result_tokens)
        if exact_start_index >= 0:
            del result_tokens[exact_start_index]
            continue

        # Try to match token initials.
        used_token_indices = match_token_initials(query_token, result_tokens)
        if used_token_indices is not None:
            for i in sorted(used_token_indices, reverse=True):
                del result_tokens[i]
            continue

        # Fuzzy match against tokens.
        for i, result_token in enumerate(result_tokens):
            if is_partial_fuzzy_match(query_token, result_token):
                del result_tokens[i]
                break
        else:
            return -1

    matched_token_count = result_token_count_at_start - len(result_tokens)
    return matched_token_count

def filter_results(query, results):
    results_by_score = defaultdict(list)
    for result in results:
        score = query_match_score(query, result)
        results_by_score[score].append(result)
    results_by_score[-1].clear()
    found_scores = list(results_by_score.keys())
    final_results = []
    for score in sorted(found_scores, reverse=True):
        final_results.extend(sorted(results_by_score[score]))
    return final_results

print(query_match_score("presusre", "pressure"))
