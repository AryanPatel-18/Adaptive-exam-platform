"""
Centralized prompt templates for Ollama LLM interactions.

All prompts used across the processing pipeline are defined here
to keep them consistent and easy to update.
"""

PROMPT_TEMPLATE_CLEAN_PAGE = """
Analyze the following OCR text from a study notes page.
Identify and extract all potential headings, subheadings, and key conceptual topics discussed on this page.
Return ONLY a JSON array of strings. Do not include variables, coding syntax, commands, or explanations.

OCR Text:
{ocr_text}
"""

PROMPT_TEMPLATE_FILTER_HEADINGS = """
You are a conceptual topic filter.
You will be given:
1. A reference list of actual topics and subtopics from a question bank.
2. A candidate list of headings/topics extracted from handwritten study notes.

Your task:
Filter the candidate list and return ONLY a JSON array of strings containing **at most 40** unique candidate headings that meet BOTH of the following criteria:
1. They are proper English sentences or conceptual topics (e.g., "Pandas Series", "Data Cleaning", "Handling Missing Values", "Data Science vs Data Analytics").
2. They are relevant or related to the reference list of topics (i.e. they cover the same or closely related subject matter).

Constraints:
- You MUST return at most 40 unique topic names. If there are more than 40 candidate headings that are valid and relevant, select and return only the top 40 most important and core conceptual topics.
- STRICTLY EXCLUDE/REMOVE all Python commands, variables, functions, expressions, syntax symbols, or any form of actual code (e.g. "import pandas", "pd.DataFrame(data)", "df.iloc[2]", "df.loc[rows columns]", "df.loc[new_index]", "fillna()", "df.sample(5)", "inplace=True", "axis=axis", "NaN").
- Keep ONLY clean English sentences, headings, and conceptual topics. Remove anything containing brackets, math operators, code assignments, method calls, or raw variable names.

Return ONLY the raw JSON array of strings in the same order as in the candidate list. Do not include any explanation or markdown formatting outside the JSON array.

Reference Topics:
{reference_topics}

Candidate Headings to Filter:
{candidate_headings}
"""

PROMPT_TEMPLATE_QUESTION_TOPICS = """
Analyze each question and extract a specific, descriptive topic and subtopic that represents the precise programming or mathematical concept a student needs to study/prepare to answer it.

Do NOT use generic or vague topics like "Pandas", "Python", "Set Theory", "Data Structures", or "Unknown".
The topic and subtopic should be specific, descriptive, and directly tell the user what particular concept they need to prepare (e.g. including function names, parameters, or mathematical principles tested).

CRITICAL: Maintain strict consistency across similar questions. If multiple questions test similar or related concepts, group them under the EXACT SAME topic name so that the topics are normalized and clean (e.g., use "Handling Missing Data in Pandas DataFrames" consistently instead of inventing different names like "DataFrame Missing Values" or "Pandas Data Cleaning").

Example 1:
Question: "Which attribute of dropna() can be used to select the columns from which null values are to be considered for removing rows?"
Output:
{{
    "topic": "Handling Missing Data in Pandas DataFrames",
    "subtopic": "Configuring row-filtering columns with dropna(subset=...)"
}}

Example 2:
Question: "In a survey of 60 people it was found that 25 people read newspapers H, 26 read newspaper I, 26 read newspapers T, 9 read both H and I... Find the numbers of students who read exactly one newspaper?"
Output:
{{
    "topic": "Inclusion-Exclusion Principle & Venn Diagrams",
    "subtopic": "Solving three-set cardinality problems for exactly one subset"
}}

Example 3:
Question: "What is the output of the below code? df.dropna(thresh=3,axis=1,inplace=True)"
Output:
{{
    "topic": "Handling Missing Data in Pandas DataFrames",
    "subtopic": "Column-wise dropping of NaNs using threshold values (dropna with axis and thresh)"
}}

Return ONLY a JSON array of objects with keys "topic" and "subtopic", with one element corresponding to each question in the input list in the same order.

Questions:

{questions}
"""
