#!/usr/bin/env python3
"""
Generate Table 5 from ETL_Data_Question-wise.csv

Metric Definitions:
- TBA (Top Box Accuracy): At least 2 out of 3 raters = 5
- AS4A (Average Score 4 Accuracy): Average Score >= 4
- 2TBA (Top Two Box Accuracy): All Raters >= 4
- P5A (Perfect 5 Accuracy): All raters = 5

Composite Metrics:
- Question General Accuracy*: Composite Metric of clarity, clinical relevance and option accuracy
- Overall Assessment Accuracy**: Composite metric of assessment accuracy and feedback quality
"""

import pandas as pd
import numpy as np

# Load the data
data = pd.read_csv("./ETL_Data_Question-wise.csv")

# Map model_id to model names
model_map = {
    '4O': 'gpt-4o',
    'CL': 'claude-3.5-sonnet',
    'GM': 'gemini-1.5-flash',
    'LM': 'llama3-70b-8192'
}

# Extract model_id from the unique_id - it's the 4th underscore-separated element
data['model_id_extracted'] = data['unique_id'].str.split('_').str[2]

# Group by case_id + mcq_id + model_id to analyze ratings across raters
# Each question has ratings from 3 raters (MP, VG, BS)
data['question_key'] = data['case_id'].astype(str) + '_' + data['mcq_id'].astype(str) + '_' + data['model_id_extracted'].astype(str)

# Metrics to analyze
metrics = ['clarity', 'clinical_relevance', 'option_accuracy', 'assessment_accuracy', 'feedback_quality']

def calculate_accuracy_metrics(df, metric_col):
    """
    Calculate all accuracy metrics for a given metric column
    
    For each question (case_id + mcq_id + model_id), we have 3 raters.
    """
    # Group by question to get ratings from all 3 raters
    grouped = df.groupby(['case_id', 'mcq_id', 'model_id_extracted'])[metric_col].apply(list).reset_index()
    grouped.columns = ['case_id', 'mcq_id', 'model_id', metric_col + '_ratings']
    
    # Calculate metrics for each question
    results = []
    for _, row in grouped.iterrows():
        ratings = row[metric_col + '_ratings']
        if len(ratings) != 3:
            continue
        
        # TBA: At least 2 out of 3 raters = 5
        tba = sum(1 for r in ratings if r == 5) >= 2
        
        # AS4A: Average Score >= 4
        avg_score = np.mean(ratings)
        as4a = avg_score >= 4
        
        # 2TBA: All Raters >= 4
        ttba = all(r >= 4 for r in ratings)
        
        # P5A: All raters = 5
        p5a = all(r == 5 for r in ratings)
        
        results.append({
            'case_id': row['case_id'],
            'mcq_id': row['mcq_id'],
            'model_id': row['model_id'],
            'TBA': tba,
            'AS4A': as4a,
            '2TBA': ttba,
            'P5A': p5a,
            'avg_score': avg_score
        })
    
    return pd.DataFrame(results)


def calculate_composite_metrics(df, metric_cols):
    """
    Calculate composite accuracy metrics across multiple columns
    For composite metrics, a question is accurate if ALL component metrics meet the criteria
    """
    # Group by question to get ratings from all 3 raters for each metric
    results = []
    
    grouped = df.groupby(['case_id', 'mcq_id', 'model_id_extracted'])
    
    for (case_id, mcq_id, model_id), group in grouped:
        if len(group) != 3:
            continue
        
        # For composite: all metrics must satisfy the condition
        all_tba = True
        all_as4a = True
        all_ttba = True
        all_p5a = True
        
        for metric_col in metric_cols:
            ratings = group[metric_col].tolist()
            
            # TBA: At least 2 out of 3 raters = 5
            tba = sum(1 for r in ratings if r == 5) >= 2
            
            # AS4A: Average Score >= 4
            avg_score = np.mean(ratings)
            as4a = avg_score >= 4
            
            # 2TBA: All Raters >= 4
            ttba = all(r >= 4 for r in ratings)
            
            # P5A: All raters = 5
            p5a = all(r == 5 for r in ratings)
            
            all_tba = all_tba and tba
            all_as4a = all_as4a and as4a
            all_ttba = all_ttba and ttba
            all_p5a = all_p5a and p5a
        
        results.append({
            'case_id': case_id,
            'mcq_id': mcq_id,
            'model_id': model_id,
            'TBA': all_tba,
            'AS4A': all_as4a,
            '2TBA': all_ttba,
            'P5A': all_p5a
        })
    
    return pd.DataFrame(results)


def calculate_model_percentages(metric_df, model_id):
    """Calculate percentages for a specific model"""
    model_data = metric_df[metric_df['model_id'] == model_id]
    n = len(model_data)
    
    if n == 0:
        return {'TBA': 0, 'AS4A': 0, '2TBA': 0, 'P5A': 0}
    
    return {
        'TBA': (model_data['TBA'].sum() / n) * 100,
        'AS4A': (model_data['AS4A'].sum() / n) * 100,
        '2TBA': (model_data['2TBA'].sum() / n) * 100,
        'P5A': (model_data['P5A'].sum() / n) * 100
    }


# Calculate metrics for each individual metric column
print("Calculating individual metrics...")
clarity_metrics = calculate_accuracy_metrics(data, 'clarity')
clinical_relevance_metrics = calculate_accuracy_metrics(data, 'clinical_relevance')
option_accuracy_metrics = calculate_accuracy_metrics(data, 'option_accuracy')
assessment_accuracy_metrics = calculate_accuracy_metrics(data, 'assessment_accuracy')
feedback_quality_metrics = calculate_accuracy_metrics(data, 'feedback_quality')

# Calculate composite metrics
print("Calculating composite metrics...")
# Question General Accuracy*: Composite of clarity, clinical_relevance, option_accuracy
question_general_metrics = calculate_composite_metrics(data, ['clarity', 'clinical_relevance', 'option_accuracy'])

# Overall Assessment Accuracy**: Composite of assessment_accuracy and feedback_quality
overall_assessment_metrics = calculate_composite_metrics(data, ['assessment_accuracy', 'feedback_quality'])

# Build Table 5
print("\nBuilding Table 5...")

model_order = ['4O', 'CL', 'GM', 'LM']
model_labels = {
    '4O': 'gpt-4o (4O)',
    'CL': 'claude-3.5-sonnet (CL)',
    'GM': 'gemini-1.5-flash (GM)',
    'LM': 'llama3-70b-8192 (LM)'
}

# Create results dictionary
results = {}

# Clarity
print("\nClarity:")
for m in model_order:
    pct = calculate_model_percentages(clarity_metrics, m)
    results[f'Clarity_{m}'] = pct
    print(f"  {model_labels[m]}: TBA={pct['TBA']:.1f}%, AS4A={pct['AS4A']:.1f}%, 2TBA={pct['2TBA']:.1f}%, P5A={pct['P5A']:.1f}%")

# Clinical Relevance
print("\nClinical Relevance:")
for m in model_order:
    pct = calculate_model_percentages(clinical_relevance_metrics, m)
    results[f'ClinicalRelevance_{m}'] = pct
    print(f"  {model_labels[m]}: TBA={pct['TBA']:.1f}%, AS4A={pct['AS4A']:.1f}%, 2TBA={pct['2TBA']:.1f}%, P5A={pct['P5A']:.1f}%")

# Option Accuracy
print("\nOption Accuracy:")
for m in model_order:
    pct = calculate_model_percentages(option_accuracy_metrics, m)
    results[f'OptionAccuracy_{m}'] = pct
    print(f"  {model_labels[m]}: TBA={pct['TBA']:.1f}%, AS4A={pct['AS4A']:.1f}%, 2TBA={pct['2TBA']:.1f}%, P5A={pct['P5A']:.1f}%")

# Question General Accuracy*
print("\nQuestion General Accuracy*:")
for m in model_order:
    pct = calculate_model_percentages(question_general_metrics, m)
    results[f'QuestionGeneral_{m}'] = pct
    print(f"  {model_labels[m]}: TBA={pct['TBA']:.1f}%, AS4A={pct['AS4A']:.1f}%, 2TBA={pct['2TBA']:.1f}%, P5A={pct['P5A']:.1f}%")

# Assessment Accuracy
print("\nAssessment Accuracy:")
for m in model_order:
    pct = calculate_model_percentages(assessment_accuracy_metrics, m)
    results[f'AssessmentAccuracy_{m}'] = pct
    print(f"  {model_labels[m]}: TBA={pct['TBA']:.1f}%, AS4A={pct['AS4A']:.1f}%, 2TBA={pct['2TBA']:.1f}%, P5A={pct['P5A']:.1f}%")

# Feedback Quality
print("\nFeedback Quality:")
for m in model_order:
    pct = calculate_model_percentages(feedback_quality_metrics, m)
    results[f'FeedbackQuality_{m}'] = pct
    print(f"  {model_labels[m]}: TBA={pct['TBA']:.1f}%, AS4A={pct['AS4A']:.1f}%, 2TBA={pct['2TBA']:.1f}%, P5A={pct['P5A']:.1f}%")

# Overall Assessment Accuracy**
print("\nOverall Assessment Accuracy**:")
for m in model_order:
    pct = calculate_model_percentages(overall_assessment_metrics, m)
    results[f'OverallAssessment_{m}'] = pct
    print(f"  {model_labels[m]}: TBA={pct['TBA']:.1f}%, AS4A={pct['AS4A']:.1f}%, 2TBA={pct['2TBA']:.1f}%, P5A={pct['P5A']:.1f}%")


# Generate CSV output
print("\n\nGenerating Accuracy_Metrics_Calculated.csv...")

csv_lines = []
csv_lines.append('Supplemental Table 1: Model Accuracy Across Various Evaluation Metrics,,,,')
csv_lines.append(',,,,')
csv_lines.append(',"TBA\n 2+ raters = 5","AS4A\n Avg Score >= 4","2TBA\n All raters >= 4","P5A\n All raters = 5"')
csv_lines.append('Metric and Model,%,%,%,%')

# Add each metric section
metric_sections = [
    ('Clarity', 'Clarity'),
    ('Clinical Relevance', 'ClinicalRelevance'),
    ('Option Accuracy', 'OptionAccuracy'),
    ('Question General Accuracy*', 'QuestionGeneral'),
    ('Assessment Accuracy', 'AssessmentAccuracy'),
    ('Feedback Quality', 'FeedbackQuality'),
    ('Overall Assessment Accuracy**', 'OverallAssessment')
]

for metric_label, metric_key in metric_sections:
    csv_lines.append(f'{metric_label},,,,')
    for m in model_order:
        key = f'{metric_key}_{m}'
        pct = results[key]
        csv_lines.append(f'{model_labels[m]},{pct["TBA"]:.1f},{pct["AS4A"]:.1f},{pct["2TBA"]:.1f},{pct["P5A"]:.1f}')

csv_lines.append(',,,,')
csv_lines.append('"Note.-- TBA: Top box accuracy (at least 2 out of 3 raters = 5); AS4A: Average Score 4 Accuracy (Average Score >= 4); 2TBA: Top Two Box Accuracy (Top Two Boxes i.e, All Raters >= 4); P5A: Perfect 5 Accuracy (Perfect 5 from all raters). *Composite Metric of clarity, clinical relevance and option accuracy. **Composite metric of assessment accuracy and feedback quality.",,,,')

# Write to file
output_path = "./Accuracy_Metrics_Calculated.csv"
with open(output_path, 'w') as f:
    f.write('\n'.join(csv_lines))

print(f"\n\nTable saved to: {output_path}")

# Also print some diagnostic info
print("\n\n=== Diagnostic Info ===")
print(f"Total rows in data: {len(data)}")
print(f"Unique models: {data['model_id_extracted'].unique()}")
print(f"Unique questions per model:")
for m in model_order:
    n = len(clarity_metrics[clarity_metrics['model_id'] == m])
    print(f"  {m}: {n} questions")
