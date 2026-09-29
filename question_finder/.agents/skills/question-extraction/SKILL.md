# Skill: Question Extraction Workflow

## Purpose
Extracts structured questions, options, answer keys, and explanations from diverse web page markups.

## Procedure
1. **Structured Data Inspection**: Check for JSON-LD Question/Quiz schema (`@type: "Question"`, `suggestedAnswer`, `acceptedAnswer`).
2. **Framework-Specific Quiz Parsing**: Detect known WordPress quiz plugins (WP Quiz, Quiz Maker, Sensei) and embedded JSON state objects.
3. **Semantic HTML Traversal**: Identify question blocks delimited by headings (`h2`, `h3`, `h4`), paragraphs with question patterns (`Q1.`, `Question 1:`, `1. `), followed by ordered/unordered lists (`ol`, `ul`) or radio input wrappers.
4. **Accordion & FAQ Parsing**: Parse interactive accordion elements (`<details><summary>`, collapsible cards) where answers and explanations are hidden behind expanders.
5. **Table-Based Quiz Parsing**: Extract tabular question/answer sets.
6. **PDF Parsing**: Utilize PyMuPDF to extract text with layout preservation, splitting on question number patterns.
7. **Option & Answer Key Extraction**:
   - Normalize option labels (A/B/C/D, 1/2/3/4, Roman numerals -> A/B/C/D).
   - Detect correct answer flags (`class="correct"`, `checked`, text markers like "Answer: B", "Correct Option: C").
   - Parse multi-select keys (e.g., "Choose TWO", "Answers: A, D").
8. **Explanation & Context Extraction**: Locate explanation paragraphs following answers or reveal buttons.
9. **Validation**: Enforce non-empty stems, >= 2 options, valid answer references, and minimum length.
