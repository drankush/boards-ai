"""
Gwet's AC1 and AC2 Calculation for Inter-Rater Reliability.

- AC1: Unweighted chance-corrected agreement coefficient (for nominal categories)
- AC2: Weighted chance-corrected agreement coefficient with quadratic weights (for ordinal categories)

Reference:
Gwet, K.L. (2014). Handbook of Inter-Rater Reliability (4th Edition). Advanced Analytics, LLC.
"""

import csv
import json
import numpy as np
import pandas as pd
from scipy import stats

def parse_pilot_data(csv_path: str) -> pd.DataFrame:
    """
    Parses pilot_responses CSV where survey data is stored as JSON per row.
    Expands q1, q2, q3 sub-questions to produce unique item-level ratings.
    """
    records = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ques_id = row["ques_id"]
            rater = row["email"]
            system = row["system"]
            model = row["model"]
            data = json.loads(row["survey_data"])
            
            for q_num in ["q1", "q2", "q3"]:
                item_id = f"{ques_id}_{q_num}"
                rec = {
                    "item_id": item_id,
                    "ques_id": ques_id,
                    "sub_q": q_num,
                    "rater": rater,
                    "system": system,
                    "model": model,
                }
                for k, v in data.items():
                    if k.startswith(f"{q_num}_"):
                        metric_name = k[len(q_num) + 1 :]
                        rec[metric_name] = v["value"]
                records.append(rec)
    return pd.DataFrame(records)


def calculate_gwet(ratings_df: pd.DataFrame, weights: str = "unweighted", categories: list = None) -> dict:
    """
    Calculates Gwet's AC1 (unweighted) or AC2 (weighted) with standard error and 95% CI.
    
    ratings_df: DataFrame with rows = subjects/items, columns = raters
    weights: 'unweighted' for AC1, 'quadratic' for AC2, or custom 2D ndarray
    categories: list of categories ordered logically
    """
    ratings = ratings_df.values
    n, r = ratings.shape
    if categories is None:
        categories = sorted(list(np.unique(ratings[~pd.isna(ratings)])))
    q = len(categories)
    
    # Construct Weight Matrix w_kl
    if isinstance(weights, str):
        if weights == "unweighted":
            w = np.eye(q)
        elif weights == "quadratic":
            w = np.zeros((q, q))
            for k in range(q):
                for l in range(q):
                    w[k, l] = 1.0 - ((k - l) ** 2) / ((q - 1) ** 2) if q > 1 else 1.0
        else:
            raise ValueError(f"Unknown weight type: {weights}")
    else:
        w = np.array(weights)
        
    # Count matrix n_ik: (n items x q categories)
    agree_mat = np.zeros((n, q))
    for k_idx, k_val in enumerate(categories):
        agree_mat[:, k_idx] = np.sum(ratings == k_val, axis=1)
        
    agree_mat_w = np.dot(agree_mat, w)
    ri_vec = np.sum(agree_mat, axis=1)
    
    sum_q = np.sum(agree_mat * (agree_mat_w - 1), axis=1)
    n2more = np.sum(ri_vec >= 2)
    
    # Observed agreement Pa
    pa = np.sum(sum_q[ri_vec >= 2] / (ri_vec * (ri_vec - 1))[ri_vec >= 2]) / n2more
    
    # Marginal probabilities pi_k
    pi_vec = np.mean(agree_mat / ri_vec[:, None], axis=0)
    weights_mat_sum = np.sum(w)
    
    # Expected chance agreement Pe
    if q >= 2:
        pe = weights_mat_sum * np.sum(pi_vec * (1 - pi_vec)) / (q * (q - 1))
    else:
        pe = 1.0 - 1e-15
        
    # Gwet's Agreement Coefficient
    ac = (pa - pe) / (1.0 - pe) if pe < 1.0 else 1.0
    
    # Standard error calculation via Gwet's linearization (delta method)
    den_ivec = ri_vec * (ri_vec - 1)
    den_ivec[den_ivec == 0] = 1
    pa_ivec = sum_q / den_ivec
    pe_r2 = pe * (ri_vec >= 2)
    ac_ivec = (n / n2more) * (pa_ivec - pe_r2) / (1.0 - pe)
    pe_ivec = (weights_mat_sum / (q * (q - 1))) * np.dot(agree_mat, (1 - pi_vec)) / ri_vec
    ac_ivec_x = ac_ivec - 2 * (1 - ac) * (pe_ivec - pe) / (1.0 - pe)
    
    var_ac = (1.0 / (n * (n - 1))) * np.sum((ac_ivec_x - ac) ** 2)
    se = np.sqrt(var_ac)
    
    t_crit = stats.t.ppf(0.975, df=n - 1)
    ci_low = max(-1.0, ac - t_crit * se)
    ci_high = min(1.0, ac + t_crit * se)
    p_value = 2 * (1 - stats.t.cdf(abs(ac / se), df=n - 1)) if se > 0 else 0.0
    
    return {
        "coeff": ac,
        "se": se,
        "pa": pa,
        "pe": pe,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "p_value": p_value,
    }


def get_altman_interpretation(val: float) -> str:
    """Altman (1991) benchmark scale for agreement coefficients."""
    if val < 0.20:
        return "Poor"
    if val < 0.40:
        return "Fair"
    if val < 0.60:
        return "Moderate"
    if val < 0.80:
        return "Good"
    return "Very Good"


def main():
    csv_path = "pilot_responses - pilot_responses.csv"
    df = parse_pilot_data(csv_path)
    
    # Define ordinal category ordering for ordinal scales
    ordinal_categories = {
        "clarity": ["Very Unclear", "Unclear", "Neutral", "Clear", "Very Clear"],
        "clinical_relevance": ["Not Relevant", "Slightly Relevant", "Moderately Relevant", "Very Relevant", "Highly Relevant"],
        "difficulty": ["1 - Easy", "3 - Moderate", "5 - Difficult"],
        "option_accuracy": ["None", "Three", "Two", "One option only"],
        "assessment_accuracy": ["All 4 incorrect", "1 incorrect", "All accurately identified"],
        "feedback_quality": ["Not Helpful", "Slightly Helpful", "Moderately Helpful", "Helpful", "Very Helpful"],
    }
    
    metrics = [
        "clarity",
        "clinical_relevance",
        "difficulty",
        "option_accuracy",
        "assessment_accuracy",
        "feedback_quality",
        "cognitive_level",
    ]
    
    print("=" * 105)
    print("GWET'S AC1 (UNWEIGHTED - NOMINAL AGREEMENT)")
    print("=" * 105)
    print(f"{'Metric':<24} | {'AC1':<8} | {'SE':<8} | {'Pa (Obs)':<8} | {'Pe (Chance)':<11} | {'95% CI':<20} | {'Interpretation':<12}")
    print("-" * 105)
    
    results_ac1 = []
    for m in metrics:
        piv = df.pivot(index="item_id", columns="rater", values=m).dropna()
        cats = ordinal_categories.get(m, None)
        res = calculate_gwet(piv, weights="unweighted", categories=cats)
        interp = get_altman_interpretation(res["coeff"])
        ci_str = f"[{res['ci_low']:.5f}, {res['ci_high']:.5f}]"
        
        results_ac1.append({
            "Metric": m.replace("_", " ").title(),
            "AC1": res["coeff"],
            "SE": res["se"],
            "Pa": res["pa"],
            "Pe": res["pe"],
            "CI": ci_str,
            "Interpretation": interp,
        })
        print(f"{m.replace('_', ' ').title():<24} | {res['coeff']:.5f}  | {res['se']:.5f}  | {res['pa']:.5f}   | {res['pe']:.5f}       | {ci_str:<20} | {interp:<12}")
        
    print("\n" + "=" * 105)
    print("GWET'S AC2 (QUADRATIC WEIGHTED - ORDINAL AGREEMENT)")
    print("=" * 105)
    print(f"{'Metric':<24} | {'AC2':<8} | {'SE':<8} | {'Pa (Obs)':<8} | {'Pe (Chance)':<11} | {'95% CI':<20} | {'Interpretation':<12}")
    print("-" * 105)
    
    results_ac2 = []
    for m in metrics:
        piv = df.pivot(index="item_id", columns="rater", values=m).dropna()
        cats = ordinal_categories.get(m, None)
        res = calculate_gwet(piv, weights="quadratic", categories=cats)
        interp = get_altman_interpretation(res["coeff"])
        ci_str = f"[{res['ci_low']:.5f}, {res['ci_high']:.5f}]"
        
        results_ac2.append({
            "Metric": m.replace("_", " ").title(),
            "AC2": res["coeff"],
            "SE": res["se"],
            "Pa": res["pa"],
            "Pe": res["pe"],
            "CI": ci_str,
            "Interpretation": interp,
        })
        print(f"{m.replace('_', ' ').title():<24} | {res['coeff']:.5f}  | {res['se']:.5f}  | {res['pa']:.5f}   | {res['pe']:.5f}       | {ci_str:<20} | {interp:<12}")


if __name__ == "__main__":
    main()
