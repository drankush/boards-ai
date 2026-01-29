"""
Gwet's AC1 and AC2 calculation for inter-rater reliability.
AC1 = unweighted (for nominal data)
AC2 = weighted (for ordinal data)

Reference: Gwet, K.L. (2014). Handbook of Inter-Rater Reliability (4th Edition)
"""
import pandas as pd
import numpy as np
from scipy import stats

def calculate_gwet_ac1(pivoted_df, categories):
    """
    Calculates Gwet's AC1 (unweighted) for ordinal data.
    pivoted_df: rows = items, columns = raters, values = ratings
    categories: list of possible rating values
    """
    n = len(pivoted_df)  # number of items
    q = len(categories)  # number of categories
    ratings = pivoted_df.values
    r = ratings.shape[1]  # number of raters per item (assuming constant)
    
    # For each item i and category k, count how many raters assigned category k
    # n_ik matrix: (n_items x q_categories)
    n_ik = np.zeros((n, q))
    for i in range(n):
        for k_idx, k_val in enumerate(categories):
            n_ik[i, k_idx] = np.sum(ratings[i, :] == k_val)
    
    # Marginal proportions: pi_k = (1/n) * sum_i (n_ik / r)
    pi_k = np.mean(n_ik / r, axis=0)
    
    # Observed agreement (proportion of concordant pairs)
    # Pa = (1/n) * sum_i [ (1 / (r*(r-1))) * sum_k n_ik * (n_ik - 1) ]
    pa_items = []
    for i in range(n):
        sum_k = 0
        for k in range(q):
            sum_k += n_ik[i, k] * (n_ik[i, k] - 1)
        pa_items.append(sum_k / (r * (r - 1)))
    pa = np.mean(pa_items)
    
    # Chance agreement for AC1
    # Pe = sum_k pi_k * (1 - pi_k) / (q - 1)
    pe = np.sum(pi_k * (1 - pi_k)) / (q - 1)
    
    # Gwet's AC1
    if pe >= 1:
        ac1 = 1.0
    else:
        ac1 = (pa - pe) / (1 - pe)
    
    # Variance estimation (using delta method approximation)
    # This is a simplified version
    var_pa = np.var(pa_items) / n
    se = np.sqrt(var_pa) / (1 - pe) if pe < 1 else 0
    
    return ac1, se


def calculate_gwet_ac2_quadratic(pivoted_df, categories):
    """
    Calculates Gwet's AC2 with quadratic weights for ordinal data.
    """
    n = len(pivoted_df)
    q = len(categories)
    ratings = pivoted_df.values
    r = ratings.shape[1]
    
    # Create quadratic weight matrix
    # w_kl = 1 - (k - l)^2 / (q - 1)^2
    w = np.zeros((q, q))
    for k in range(q):
        for l in range(q):
            w[k, l] = 1 - ((k - l)**2) / ((q - 1)**2)
    
    # Count matrix n_ik
    n_ik = np.zeros((n, q))
    for i in range(n):
        for k_idx, k_val in enumerate(categories):
            n_ik[i, k_idx] = np.sum(ratings[i, :] == k_val)
    
    # Marginal proportions
    pi_k = np.mean(n_ik / r, axis=0)
    
    # Weighted observed agreement
    # Pa_w = (1/n) * sum_i [ (1/(r*(r-1))) * sum_k sum_l w_kl * n_ik * (n_il - delta_kl) ]
    pa_w_items = []
    for i in range(n):
        total = 0
        for k in range(q):
            for l in range(q):
                delta_kl = 1 if k == l else 0
                total += w[k, l] * n_ik[i, k] * (n_ik[i, l] - delta_kl)
        pa_w_items.append(total / (r * (r - 1)))
    pa_w = np.mean(pa_w_items)
    
    # Weighted chance agreement for AC2
    # Pe_w = ( sum_k sum_l w_kl * pi_k * pi_l - (1/q) * sum_k w_kk ) / (1 - 1/q)
    # Simplified: Pe_w = sum_{k!=l} w_kl * pi_k * pi_l / (1 - sum_k pi_k^2)
    # Actually for AC2: Pe_w = T_w * sum_k pi_k * (1 - pi_k) / (q - 1)
    # where T_w = mean of off-diagonal weights = sum_{k!=l} w_kl / (q * (q-1))
    
    # T_w calculation
    off_diag_sum = np.sum(w) - np.trace(w)
    t_w = off_diag_sum / (q * (q - 1))
    
    pe_w = t_w * np.sum(pi_k * (1 - pi_k)) / (q - 1)
    
    # AC2
    if pe_w >= 1:
        ac2 = 1.0
    else:
        ac2 = (pa_w - pe_w) / (1 - pe_w)
    
    # SE estimation
    var_pa_w = np.var(pa_w_items) / n
    se = np.sqrt(var_pa_w) / (1 - pe_w) if pe_w < 1 else 0
    
    return ac2, se


def get_interpretation(val):
    if val < 0.20: return "Poor"
    if val < 0.40: return "Fair"
    if val < 0.60: return "Moderate"
    if val < 0.80: return "Good"
    return "Very Good"


# Main execution
input_csv = 'pilot_responses_simplified.csv'
df = pd.read_csv(input_csv)

metrics = ['clarity', 'clinical_relevance', 'difficulty', 'option_accuracy', 'assessment_accuracy', 'feedback_quality']
categories = [1, 2, 3, 4, 5]

print("=" * 80)
print("Gwet's AC1 (unweighted, for nominal comparison)")
print("=" * 80)
results_ac1 = []
for metric in metrics:
    df['question_id'] = df['unique_id'].str.rsplit('_', n=1).str[0]
    pivoted = df.pivot(index='question_id', columns='rater', values=metric)
    pivoted = pivoted.dropna()
    
    ac1, se = calculate_gwet_ac1(pivoted, categories)
    ci_low = ac1 - 1.96 * se
    ci_high = ac1 + 1.96 * se
    
    results_ac1.append({
        'Metric': metric.replace('_', ' ').title(),
        'AC1': round(ac1, 5),
        'SE': round(se, 5),
        'CI': f"[{ci_low:.5f}, {ci_high:.5f}]",
        'Interpretation': get_interpretation(ac1)
    })
    print(f"{metric}: AC1={ac1:.5f}, SE={se:.5f}, CI=[{ci_low:.5f}, {ci_high:.5f}], {get_interpretation(ac1)}")

print("\n" + "=" * 80)
print("Gwet's AC2 with quadratic weights (for ordinal data)")
print("=" * 80)
results_ac2 = []
for metric in metrics:
    df['question_id'] = df['unique_id'].str.rsplit('_', n=1).str[0]
    pivoted = df.pivot(index='question_id', columns='rater', values=metric)
    pivoted = pivoted.dropna()
    
    ac2, se = calculate_gwet_ac2_quadratic(pivoted, categories)
    ci_low = ac2 - 1.96 * se
    ci_high = ac2 + 1.96 * se
    
    results_ac2.append({
        'Metric': metric.replace('_', ' ').title(),
        'AC2': round(ac2, 5),
        'SE': round(se, 5),
        'CI': f"[{ci_low:.5f}, {ci_high:.5f}]",
        'Interpretation': get_interpretation(ac2)
    })
    print(f"{metric}: AC2={ac2:.5f}, SE={se:.5f}, CI=[{ci_low:.5f}, {ci_high:.5f}], {get_interpretation(ac2)}")

print("\n" + "=" * 80)
print("Debug: Examining Difficulty ratings")
print("=" * 80)
df['question_id'] = df['unique_id'].str.rsplit('_', n=1).str[0]
difficulty_pivot = df.pivot(index='question_id', columns='rater', values='difficulty')
print(difficulty_pivot)
