# Prompt Engineering Experiment Report

## 1. Summary of Results

The following table summarizes the performance of three prompting strategies across 5 test scenarios. The **ROUGE-L (F1 Score)** was used as the quantitative metric to measure the similarity between the Model Output and the Ground Truth.

| Strategy                 | Avg ROUGE-L (F1) | Avg Latency (s) | Avg Output Tokens | Cost Efficiency |
| :----------------------- | :--------------: | :-------------: | :---------------: | :-------------: |
| **Baseline (Zero-Shot)** |      0.078       |      5.99       |        774        |       Low       |
| **Few-Shot (k=3)**       |      0.309       |      1.92       |        217        |    **High**     |
| **Few-Shot (k=5)**       |    **0.313**     |    **1.86**     |        249        |    **High**     |
| **Meta-Prompt**          |      0.164       |      2.65       |        301        |    Moderate     |

### Key Findings:

- **Most Accurate:** The **Few-Shot** strategies achieved the highest overlap with the ground truth (~0.31), likely because the examples conditioned the model to mimic the exact formatting and conciseness of the desired answer.
- **Fastest:** **Few-Shot (k=5)** was the fastest strategy (1.86s), reducing latency by **69%** compared to the Baseline.
- **Most Efficient:** The **Few-Shot** strategies used the fewest tokens (~220-250), making them significantly cheaper to run than the Zero-Shot strategy (774 tokens).
- **Formatting Issue:** The **Zero-Shot** strategy scored very low (0.078) largely due to "fluff" (conversational fillers like "Okay, based on...") and inconsistent markdown usage, which diluted the informational density.

---

## 2. Strategies Used

1. **Baseline (Zero-Shot):** A simple instruction: _"Based on the following reviews, list key success factors and potential pitfalls..."_

   - _Result:_ Conversational, verbose, and unstructured.

2. **Example-Driven (Few-Shot):** Included 3 or 5 pairs of (Input Reviews -> Desired Output List).

   - _Result:_ Concise, strictly formatted, and high adherence to the "Ground Truth" style.

3. **Advanced (Meta-Prompt):** A structured persona-based prompt: _"You are an expert Restaurant Consultant. RULES: Be brutal but constructive..."_
   - _Result:_ Professional tone and good structure, but slightly more verbose than the Few-Shot examples.

---

## 3. Quantitative Analysis

### Metric: ROUGE-L (F1)

The ROUGE-L metric measures the longest common subsequence between the model's output and the ground truth.

- **Winner:** **Few-Shot (k=5)** (Score: 0.313).
- **Insight:** The Few-Shot prompt effectively "trained" the model to strip away introduction text and focus purely on the bullet points, matching the Ground Truth format almost perfectly. The Zero-Shot model's tendency to write essays ("In Summary", "Okay...") severely punished its score.

### Metric: Latency & Tokens

- **Winner:** **Few-Shot (k=5)**.
- **Insight:** Providing examples allows the model to "copy" the format immediately without "thinking" about how to structure the response. This resulted in a **~3x speedup** compared to the Zero-Shot baseline. The Meta-Prompt was also efficient but required slightly more tokens to establish the persona.

---

## 4. Qualitative Observations (Human-in-the-Loop)

To complement the automated metrics, our group of three students performed a manual evaluation of the outputs. We defined a rubric to grade "Helpfulness & Adherence to Instructions" on a 1-5 scale and averaged our independent scores.

### **4.1. The Grading Rubric**

| Score | Definition     | Criteria                                                                             |
| :---- | :------------- | :----------------------------------------------------------------------------------- |
| **5** | **Perfect**    | Matches Ground Truth logic; perfect formatting; no "fluff" or conversational filler. |
| **4** | **Good**       | Useful advice and good format, but minor unnecessary text or missed a small detail.  |
| **3** | **Acceptable** | captured main points but had formatting errors (nested lists) or was too wordy.      |
| **2** | **Poor**       | Significant "hallucinations" (advice not in text) or extremely difficult to parse.   |
| **1** | **Failure**    | Did not follow instructions or output was irrelevant.                                |

### **4.2. Team Scorecard (Averaged)**

We graded 5 scenarios independently. The table below shows the average scores across all scenarios for each student.

| Strategy                 | Salik (Avg) | Ahmad (Avg) | Fizza (Avg) | **FINAL SCORE** |
| :----------------------- | :---------: | :---------: | :---------: | :-------------: |
| **Baseline (Zero-Shot)** |     2.2     |     2.5     |     2.0     |   **2.2 / 5**   |
| **Few-Shot (k=3)**       |     4.6     |     4.8     |     4.4     |   **4.6 / 5**   |
| **Few-Shot (k=5)**       |     5.0     |     4.8     |     5.0     |   **4.9 / 5**   |
| **Meta-Prompt**          |     3.8     |     4.0     |     3.5     |   **3.8 / 5**   |

### **4.3. Insights**

- **Zero-Shot (Score: 2.2):** All three of us penalized this strategy heavily for "conversational fluff." In an API context, phrases like _"Okay, based on the reviews provided..."_ and _"Good luck!"_ were considered noise that would require extra post-processing code to remove.
- **Few-Shot (Score: 4.9):** This was the unanimous winner. The `k=5` strategy was slightly more consistent than `k=3` in catching edge cases (like the specific tomato sauce complaint in Scenario 4).
- **Meta-Prompt (Score: 3.8):** While the advice was high-quality and "professional," we rated it lower than Few-Shot because the headings were inconsistent. Sometimes it used **"Risks"** and other times **"Potential Pitfalls,"** making it harder to standardize than the Few-Shot output.

---

## 5. Conclusion

For the objective of extracting business insights from reviews, the **Few-Shot (k=5)** strategy is the recommended approach.

1.  **Quantitative Win:** It achieved the highest ROUGE-L score (0.313) and the lowest latency (1.86s).
2.  **Qualitative Win:** It received a near-perfect human rating (**4.9/5**) from our evaluation for its precision and lack of conversational noise.
3.  **Efficiency:** It reduces token costs by ~70% compared to the baseline.

While the **Meta-Prompt** produced high-quality "consultant-style" text, the **Few-Shot** strategy is superior for building a reliable, automated data extraction pipeline.
