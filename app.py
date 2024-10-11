# %%
import streamlit as st
import re
import json 
import pandas as pd
from openai import OpenAI
from collections import Counter
from striprtf.striprtf import rtf_to_text
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

import os

# Specify the root directory containing the subfolders
root_directory = 'Final_Texts_Subdivided'  # Change this to your folder name

# Collect all .txt files in the root directory and its subdirectories
text_files = []
for dirpath, _, filenames in os.walk(root_directory):
    for filename in filenames:
        if filename.endswith('.txt'):
            text_files.append(os.path.join(dirpath, filename))

# Now, text_files contains the paths of all .txt files

OPEN_IA_KEY = "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"
client = OpenAI(api_key=OPEN_IA_KEY)


def convert_to_json(text):
    if text[0]=='{':
        json_object = json.loads(text)
        return json_object
    
    lines = text.splitlines()  # Split the text into a list of lines
    if len(lines) > 2:  # Ensure there are at least three lines
        lines = lines[1:-1]  # Remove the first and last lines
    json_string= "\n".join(lines)  # Join the remaining lines back into a string

    # Convert JSON string to JSON object (Python dictionary)
    json_object = json.loads(json_string)
    return json_object

# Define the list of required fields
required_fields = [
    'Types of Plots', 'Themes', 'Writing Style', 'Pacing',
    'Description', 'Tone', 'Genre', 'Translated Work',
    'Narrative Style', 'Perspective', 'Language',
    'Dialogue Quality', 'Author', 'Title', 'Publication Date'
]

def ensure_fields(obj, fields):
    for field in fields:
        if field not in obj:
            # Add missing field with empty list
            obj[field] = []
    return obj


def sort_json_fields(json_obj):
    order = [
    'Title',
    'Author',   
    'Types of Plots',
    'Themes',
    'Writing Style',
    'Pacing',
    'Description',
    'Tone',
    'Genre',
    'Translated Work',
    'Narrative Style',
    'Perspective',
    'Language',
    'Publication Date',
    'Dialogue Quality',
    ]
    sorted_json = {key: json_obj[key] for key in order if key in json_obj}
    return sorted_json


# Convert non-list values to lists
def Convert_to_list(json_obj):
    for key, value in json_obj.items():
        if not isinstance(value, list):
            json_obj[key] = [value]
    return json_obj

# %%
def sort_json_by_occurrence(json_objects):
    final_json = {}
    
    # Aggregate values for each key
    for key in json_objects[0]:
        values = []
        for json_obj in json_objects:
            value = json_obj[key]
            if isinstance(value, list):
                if len(value) > 0:
                    values.extend(value)
            else:
                if value is not None:  # Ensure None values are not included
                    values.append(value)

        final_json[key] = values if values else []

    # Count occurrences and sort
    sorted_json = {}
    for key, values in final_json.items():
        # Count occurrences of each value
        value_counts = Counter(values)
        # Sort by the number of occurrences, and then by the order of appearance for ties
        sorted_values = [item for item, count in value_counts.most_common()]
        # Keep only the first 5 items
        if key in ['Writing Style', 'Description', 'Pacing', 'Narrative Style']:
            sorted_json[key] = sorted_values[:2]
        elif key =='Tone':
            sorted_json[key] = sorted_values[:4]
        elif  key =="Translated Work":
        
            if len(final_json[key])>2:
                sorted_json[key]='Unkown'
            else: 
                sorted_json[key] = sorted_values if sorted_values else ['Unknown']

        else:
            sorted_json[key] = sorted_values[:10]

    return sorted_json

# %%
def organize_object(result):
    # convert string to json
    json_object=convert_to_json(result)
    # convert non list values to lists
    json_object=Convert_to_list(json_object)
    # Ensure all fields are present in the object
    json_object = ensure_fields(json_object, required_fields)
    # sort fields by the desired order
    json_object=sort_json_fields(json_object)
    
    return json_object

# %%
def get_commun_words(text,sorted_json ):
    if sorted_json['Language'][0]=='French':
        # Load stopwords from a .txt file
        with open('stop_words/stop_words_frensh.txt', 'r', encoding='utf-8') as file:
            stop_words = set(line.strip() for line in file)
    elif sorted_json['Language'][0]=='English':
        # Load stopwords from a .txt file
        with open('stop_words/stop_words_english.txt', 'r', encoding='utf-8') as file:
            stop_words = set(line.strip() for line in file)
    else: 
        # Load stopwords from a .txt file
        with open('stop_words/stop_words_spanish.txt', 'r', encoding='utf-8') as file:
            stop_words = set(line.strip() for line in file)
    # Tokenize the text by splitting on non-alphabetic characters
    words = re.findall(r'\b\w+\b', text.lower())

    # Remove stopwords
    filtered_words = [word for word in words if word not in stop_words]

    # Count the frequency of each word
    word_counts = Counter(filtered_words)
    # Get the most common words
    most_common_words = word_counts.most_common(300)  # Change 5 to get more words

    # Print the most common words
    words=''
    for word, count in most_common_words:
        words=words + word + '\n'

    return words


# Function to read and process the uploaded file
def process_uploaded_file(uploaded_file):
    if uploaded_file.name.endswith('.txt'):
        # Read the text file content
        content = uploaded_file.read().decode('utf-8')
    elif uploaded_file.name.endswith('.rtf'):
        # Read and convert the RTF file content
        rtf_content = uploaded_file.read().decode('utf-8')
        content = rtf_to_text(rtf_content)
    else:
        content = "Unsupported file type"

    try: # Find the start and end indices
        start_index = content.find("START OF THE PROJECT GUTENBERG EBOOK")
        end_index = content.find("END OF THE PROJECT GUTENBERG EBOOK")

        if start_index != -1 and end_index != -1:
            first_page= content[:start_index]
            # Extract the text between the start and end markers
            extracted_text = content[start_index:end_index + len("END OF THE PROJECT GUTENBERG EBOOK")]
        else:
            first_page= content[:1500]
            extracted_text=content
    except:
        first_page=''
        extracted_text="Unsupported file type"
    return first_page, extracted_text



# %%
def combined_text_processing_single_call(text_for_author_title, text_for_features):
    results=[]
    for chunk in text_for_features:
        response = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18-2024-07-18",
           # temperature=0.3,
            messages=[
                {"role": "system", "content": """You are a helpful text categorization assistant. Your task is to analyze the provided extracts from a book and generate two separate JSON objects. Ensure that the returned JSON objects contain only values in the format: {feature : [list of variants]}, with no nested objects.
    

                1. first JSON object :
                    - Analyze the first text to identify the **Author**, **Title**, **Publication Date**, and whether the book is a **Translated work**. If nothing is found for any of these, return 'Unknown'.
                
                2. second JSON object: 
                    - Analyze the second text to identify various literary features provided bellow. Provide a JSON object with these features and their corresponding variants found in the text.
                here are features: 
                    1. **Types of Plots**: For this feature, return a list where the first element should be either **Linear** (Events occur in chronological order) or **Non-linear** (Events are presented out of sequence). If the text does not explicitly indicate whether it is linear or non-linear, you may omit this and move directly to the other variants:

                        - **Quest**: Protagonist embarks on a journey to achieve a goal.
                        - **Tragedy**: Protagonist experiences downfall or destruction.
                        - **Comedy**: Light-hearted, aiming to entertain and amuse.
                        - **Mystery**: Focuses on solving a puzzle or crime.
                        - **Revenge**: Protagonist seeks vengeance for a wrong done to them.
                        - **Transformation & Growth**: Characters undergo significant personal change or rise to success, often overcoming adversity.
                        - **Conflict & Struggle**: Characters face challenging obstacles, such as against nature or society, highlighting resilience.
                        - **Escape & Rescue**: Thrilling plots about escaping danger or rescuing others, emphasizing survival and bravery.

                    2. **Themes**

                        - **Love**: Relationships, romance, and affection.
                        - **Power**: Authority, influence, and control.
                        - **Identity**: Self-discovery and personal growth.
                        - **Freedom**: Desire to be free from constraints.
                        - **Justice**: Fairness, retribution, and law.
                        - **Revenge**: Retaliation for a wrong.
                        - **Betrayal**: Deception and treachery.
                        - **Sacrifice**: Giving up something valuable for a cause.
                        - **Courage**: Bravery and facing fears.
                        - **War**: Conflicts and military themes.
                        - **Peace**: Harmony and non-violence.
                        - **Morality**: Ethical dilemmas and good vs. evil.
                        - **Death**: Mortality, loss, and grief.
                        - **Hope**: Optimism and aspirations.
                        - **Tradition vs. Change**: Conflict between old and new ways.
                        - **Isolation**: Loneliness and being apart from others.
                        - **Family**: Kinship and family dynamics.

                    3. **Writing Style**

                        - **Descriptive**: Rich in detail and sensory experience.
                        - **Concise**: Direct and to the point.
                        - **Poetic**: Lyrical and rhythmic language.
                        - **Conversational**: Casual and akin to spoken language.
                        - **Formal**: Structured and complex language.
                        - **Humorous**: Light-hearted and funny.
                        - **Sparse**: Minimalistic with few words.
                        - **Flowery**: Elaborate and decorative language.

                    4. **Pacing**

                        - **Fast-paced**: Quick and action-oriented.
                        - **Slow-paced**: Deliberate, focusing on character development.
                        - **Moderate**: Balanced between action and character exploration.

                    5. **Description**

                        - **Detailed Descriptions**: Rich and vivid details.
                        - **Minimal Descriptions**: Just enough to set the scene.
                        - **Balanced**: A mix of detailed and minimal descriptions.

                    6. **Tone**

                        - **Reflective**: Contemplative and introspective.
                        - **Humorous**: Light-hearted and funny.
                        - **Sarcastic**: Ironic and mocking.
                        - **Dark**: Grim and somber.
                        - **Uplifting**: Positive and encouraging.
                        - **Romantic**: Passionate and focused on love.
                        - **Suspenseful**: Tense and filled with anticipation.
                        - **Cynical**: Distrustful and pessimistic.

                    7. **Genre**
                    
                            - **Fantasy**: Imaginary worlds with magical elements.
                            - **Science Fiction**: Futuristic concepts and technology.
                            - **Mystery**: Solving crimes or uncovering secrets.
                            - **Thriller**: Suspenseful and action-filled.
                            - **Romance**: Focus on love and relationships.
                            - **Horror**: Designed to scare and unsettle.
                            - **Historical Fiction**: Set in a historical period with fictional elements.
                            - **Literary Fiction**: Focus on style and character development.
                            - **Young Adult**: Targeted at teenage readers.
                            - **Coming of Age**: Focus on the growth of a young protagonist.
                            - **Contemporary Fiction**: Set in modern times.
                            - **Genre-bending**: Combines elements of multiple genres.
                            - **Dystopian**: Bleak, oppressive societies.
                            - **Urban Fantasy**: Fantasy set in a modern city.
                            - **Cyberpunk**: High-tech, dystopian futures.
                            - **Gothic**: Dark, mysterious settings often with romance.
                            - **Chick Lit**: Light-hearted stories focusing on women's experiences.
                            - **Paranormal Romance**: Romance with supernatural elements.
                            - **Epic Fantasy**: Large-scale fantasy with complex world-building.
                            - **Political Thriller**: Political intrigue and power struggles.
                            - **Historical Romance**: Romance set in a historical context.
                            - **Psychological Thriller**: Focuses on mental states and manipulation.
                            - **Humor/Satire**: Entertaining through humor and critique.
                            - **Space Opera**: Epic space adventures with complex politics.

                
                            - **Biography/Autobiography**: True life stories.
                            - **Memoir**: Personal reflections and stories.
                            - **Self-Help**: Advice and strategies for personal improvement.
                            - **Psychology**: Exploration of human mind and behavior.
                            - **Spirituality/Religion**: Beliefs and practices.
                            - **Philosophy**: Fundamental questions about existence and knowledge.
                            - **Essays**: Collections of short non-fiction pieces.
                            - **History**: Accounts of past events.
                            - **Politics**: Analysis of political systems and events.
                            - **True Crime**: Real criminal cases.
                            - **Science**: Scientific concepts and discoveries.
                            - **Business**: Entrepreneurship and management topics.
                            - **Other**: Miscellaneous non-fiction topics.

                    8. **Narrative Style**

                        - **First-person**: Story told from a character’s perspective.
                        - **Third-person limited**: Narrator knows thoughts of one character.
                        - **Third-person omniscient**: All-knowing narrator.
                        - **Other**: Different narrative style.

                    9. **Perspective**

                        - **BIPOC**: Stories from BIPOC perspectives.
                        - **LGBTQ+ Perspectives**: Narratives exploring LGBTQ+ themes.
                        - **Stories of Diverse Abilities**: Experiences of individuals with disabilities or neurodivergent conditions.
                        - **Indigenous Perspectives**: Narratives from Indigenous cultures.
                        - **Refugee/Immigrant Stories**: Experiences of displacement and adaptation.
                        - **Gender Perspectives**: Exploration of gender identity and roles.
                        - **Other**: Other perspectives.

                    10. **Language**

                        - **French**: Text in French.
                        - **English**: Text in English.
                        - **Spanish**: Text in Spanish.

                    11. **Dialogue Quality**

                        - **Natural**: Realistic and life-like dialogue.
                        - **Witty**: Clever and sharp exchanges.
                        - **Sparse**: Minimal dialogue, focusing more on narrative.
                        - **Philosophical**: Deep, reflective dialogue on ideas and thoughts.
                 
            Ensure that the returned JSON objects contain only values in the format: {feature : [list of variants]}, with no nested objects.
        """},
                {"role": "user", "content": text_for_author_title},
                {"role": "user", "content": chunk}

            ]
        )

        # Extract and organize the two JSON objects from the response
        response_content = response.choices[0].message.content
        try:
            indexes1 = [index for index, char in enumerate(response_content) if char == '}']
            indexes2 = [index for index, char in enumerate(response_content) if char == '{']
            author_title_data=organize_object(response_content[indexes2[0]:indexes1[0]+1])
            feature_data=organize_object(response_content[indexes2[1]:indexes1[1]+1])
    
            # Combine the results into a single dictionary
            combined_results = {
                "author_title_data": author_title_data,
                "feature_data": feature_data
            }
            results.append(combined_results)
        except:
            results=['null']
            break
    return results


# %%
def model_knowledge_base_categorization(title, common_words):
    knowledge_base_categorization = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        #temperature=0.3,
        messages=[
            {
                "role": "system",
                "content": """You are a helpful text categorization assistant. Your task is to analyze the provided text and generate two separate JSON objects. Ensure that the returned JSON objects contain only values in the format: {feature : [list of variants]}, with no nested objects.
                         
                1. **First JSON Object**:   
                   - Based on the given set of common words extracted from the book, identify and return the variants of the following features found in the text:

                    **Themes**
                        - **Love**: Relationships, romance, and affection.
                        - **Power**: Authority, influence, and control.
                        - **Identity**: Self-discovery and personal growth.
                        - **Freedom**: Desire to be free from constraints.
                        - **Justice**: Fairness, retribution, and law.
                        - **Revenge**: Retaliation for a wrong.
                        - **Betrayal**: Deception and treachery.
                        - **Sacrifice**: Giving up something valuable for a cause.
                        - **Courage**: Bravery and facing fears.
                        - **War**: Conflicts and military themes.
                        - **Peace**: Harmony and non-violence.
                        - **Morality**: Ethical dilemmas and good vs. evil.
                        - **Death**: Mortality, loss, and grief.
                        - **Hope**: Optimism and aspirations.
                        - **Tradition vs. Change**: Conflict between old and new ways.
                        - **Isolation**: Loneliness and being apart from others.
                        - **Family**: Kinship and family dynamics.
                    
                    **Types of Plots**
                        - For this feature, return a list where the first element should be either **Linear** (events occur in chronological order) or **Non-linear** (events are presented out of sequence). If the text does not explicitly indicate whether it is linear or non-linear, you may omit this and move directly to the other variants:
                        - **Quest**: Protagonist embarks on a journey to achieve a goal.
                        - **Tragedy**: Protagonist experiences downfall or destruction.
                        - **Comedy**: Light-hearted, aiming to entertain and amuse.
                        - **Mystery**: Focuses on solving a puzzle or crime.
                        - **Revenge**: Protagonist seeks vengeance for a wrong done to them.
                        - **Transformation & Growth**: Characters undergo significant personal change or rise to success, often overcoming adversity.
                        - **Conflict & Struggle**: Characters face challenging obstacles, such as against nature or society, highlighting resilience.
                        - **Escape & Rescue**: Thrilling plots about escaping danger or rescuing others, emphasizing survival and bravery.

                    **Pacing**
                        - **Fast-paced**: Quick and action-oriented.
                        - **Slow-paced**: Deliberate, focusing on character development.
                        - **Moderate**: Balanced between action and character exploration.
            
                2. **Second JSON Object**:
                   - Based on your knowledge of the provided book title and author, return the variants of the following features that are found in the text:

                    **Types of Plots**
                        - For this feature, return a list where the first element should be either **Linear** (events occur in chronological order) or **Non-linear** (events are presented out of sequence). If the text does not explicitly indicate whether it is linear or non-linear, you may omit this and move directly to the other variants:
                        - **Quest**: Protagonist embarks on a journey to achieve a goal.
                        - **Tragedy**: Protagonist experiences downfall or destruction.
                        - **Comedy**: Light-hearted, aiming to entertain and amuse.
                        - **Mystery**: Focuses on solving a puzzle or crime.
                        - **Revenge**: Protagonist seeks vengeance for a wrong done to them.
                        - **Transformation & Growth**: Characters undergo significant personal change or rise to success, often overcoming adversity.
                        - **Conflict & Struggle**: Characters face challenging obstacles, such as against nature or society, highlighting resilience.
                        - **Escape & Rescue**: Thrilling plots about escaping danger or rescuing others, emphasizing survival and bravery.

                    **Themes**
                        - **Love**: Relationships, romance, and affection.
                        - **Power**: Authority, influence, and control.
                        - **Identity**: Self-discovery and personal growth.
                        - **Freedom**: Desire to be free from constraints.
                        - **Justice**: Fairness, retribution, and law.
                        - **Revenge**: Retaliation for a wrong.
                        - **Betrayal**: Deception and treachery.
                        - **Sacrifice**: Giving up something valuable for a cause.
                        - **Courage**: Bravery and facing fears.
                        - **War**: Conflicts and military themes.
                        - **Peace**: Harmony and non-violence.
                        - **Morality**: Ethical dilemmas and good vs. evil.
                        - **Death**: Mortality, loss, and grief.
                        - **Hope**: Optimism and aspirations.
                        - **Tradition vs. Change**: Conflict between old and new ways.
                        - **Isolation**: Loneliness and being apart from others.
                        - **Family**: Kinship and family dynamics.

                    **Writing Style**
                        - **Descriptive**: Rich in detail and sensory experience.
                        - **Concise**: Direct and to the point.
                        - **Poetic**: Lyrical and rhythmic language.
                        - **Conversational**: Casual and akin to spoken language.
                        - **Formal**: Structured and complex language.
                        - **Humorous**: Light-hearted and funny.
                        - **Sparse**: Minimalistic with few words.
                        - **Flowery**: Elaborate and decorative language.

                    **Pacing**
                        - **Fast-paced**: Quick and action-oriented.
                        - **Slow-paced**: Deliberate, focusing on character development.
                        - **Moderate**: Balanced between action and character exploration.

                    **Tone**
                        - **Reflective**: Contemplative and introspective.
                        - **Humorous**: Light-hearted and funny.
                        - **Sarcastic**: Ironic and mocking.
                        - **Dark**: Grim and somber.
                        - **Uplifting**: Positive and encouraging.
                        - **Romantic**: Passionate and focused on love.
                        - **Suspenseful**: Tense and filled with anticipation.
                        - **Cynical**: Distrustful and pessimistic.

                    **Genre**
                        - **Fantasy**: Imaginary worlds with magical elements.
                        - **Science Fiction**: Futuristic concepts and technology.
                        - **Mystery**: Solving crimes or uncovering secrets.
                        - **Thriller**: Suspenseful and action-filled.
                        - **Romance**: Focus on love and relationships.
                        - **Horror**: Designed to scare and unsettle.
                        - **Historical Fiction**: Set in a historical period with fictional elements.
                        - **Literary Fiction**: Focus on style and character development.
                        - **Young Adult**: Targeted at teenage readers.
                        - **Coming of Age**: Focus on the growth of a young protagonist.
                        - **Contemporary Fiction**: Set in modern times.
                        - **Genre-bending**: Combines elements of multiple genres.
                        - **Dystopian**: Bleak, oppressive societies.
                        - **Urban Fantasy**: Fantasy set in a modern city.
                        - **Cyberpunk**: High-tech, dystopian futures.
                        - **Gothic**: Dark, mysterious settings often with romance.
                        - **Chick Lit**: Light-hearted stories focusing on women's experiences.
                        - **Paranormal Romance**: Romance with supernatural elements.
                        - **Epic Fantasy**: Large-scale fantasy with complex world-building.
                        - **Political Thriller**: Political intrigue and power struggles.
                        - **Historical Romance**: Romance set in a historical context.
                        - **Psychological Thriller**: Focuses on mental states and manipulation.
                        - **Humor/Satire**: Entertaining through humor and critique.
                        - **Space Opera**: Epic space adventures with complex politics.
                        - **Biography/Autobiography**: True life stories.
                        - **Memoir**: Personal reflections and stories.
                        - **Self-Help**: Advice and strategies for personal improvement.
                        - **Psychology**: Exploration of human mind and behavior.
                        - **Spirituality/Religion**: Beliefs and practices.
                        - **Philosophy**: Fundamental questions about existence and knowledge.
                        - **Essays**: Collections of short non-fiction pieces.
                        - **History**: Accounts of past events.
                        - **Politics**: Analysis of political systems and events.
                        - **True Crime**: Real criminal cases.
                        - **Science**: Scientific concepts and discoveries.
                        - **Business**: Entrepreneurship and management topics.
                        - **Other**: Miscellaneous non-fiction topics.

                    **Narrative Style**

                        - **First-person**: Story told from a character’s perspective.
                        - **Third-person limited**: Narrator knows thoughts of one character.
                        - **Third-person omniscient**: All-knowing narrator.
                        - **Other**: Different narrative style.

                    **Perspective**

                        - **BIPOC**: Stories from BIPOC perspectives.
                        - **LGBTQ+ Perspectives**: Narratives exploring LGBTQ+ themes.
                        - **Stories of Diverse Abilities**: Experiences of individuals with disabilities or neurodivergent conditions.
                        - **Indigenous Perspectives**: Narratives from Indigenous cultures.
                        - **Refugee/Immigrant Stories**: Experiences of displacement and adaptation.
                        - **Gender Perspectives**: Exploration of gender identity and roles.
                        - **Other**: Other perspectives.

                    **Language**

                        - **French**: Text in French.
                        - **English**: Text in English.
                        - **Spanish**: Text in Spanish.
                    
                    **Description**
                        - **Detailed Descriptions**: Rich and vivid details.
                        - **Minimal Descriptions**: Just enough to set the scene.
                        - **Balanced**: A mix of detailed and minimal descriptions.


                    **Dialogue Quality**

                        - **Natural**: Realistic and life-like dialogue.
                        - **Witty**: Clever and sharp exchanges.
                        - **Sparse**: Minimal dialogue, focusing more on narrative.
                        - **Philosophical**: Deep, reflective dialogue on ideas and thoughts.
            
            Ensure that the returned JSON objects contain only values in the format: {feature : [list of variants]}, with no nested objects.
              
                    """
            },
            {"role": "user", "content": title},
            {"role": "user", "content": common_words}
        ],
    )
    response_content=knowledge_base_categorization.choices[0].message.content
    try:
        indexes1 = [index for index, char in enumerate(response_content) if char == '}']
        indexes2 = [index for index, char in enumerate(response_content) if char == '{']
        cummon_words_data=organize_object(response_content[indexes2[0]:indexes1[0]+1])
        knowledge_base_data=organize_object(response_content[indexes2[1]:indexes1[1]+1])

        # Combine the results into a single dictionary
        combined_results = {
            "cummon_words_data": cummon_words_data,
            "knowledge_base_data": knowledge_base_data
        }
    except:
        combined_results=['null']
    return combined_results

def count_plot_types(json_objects):
        linear_count = 0
        non_linear_count = 0
        
        for obj in json_objects:
            plot_types = obj.get("Types of Plots", [])
            linear_count += plot_types.count("Linear")
            non_linear_count += plot_types.count("Non-linear")
        
        return {"Linear": linear_count, "Non-linear": non_linear_count}


def remove_low_occurrence_plot(json_objects, counts):
    # Determine which plot type has the higher count
    if counts['Linear'] > counts['Non-linear']:
        to_remove = 'Non-linear'
    else:
        to_remove = 'Linear'

    # Remove the plot type with lower occurrence from all objects
    for obj in json_objects:
        if "Types of Plots" in obj:
            obj["Types of Plots"] = [plot for plot in obj["Types of Plots"] if plot != to_remove]

    return json_objects

def process_and_analyze_file(content,first_page, text_splitter):
    
    if content == "Unsupported file type":
        st.write("Unsupported file type")
        return None

    texts = text_splitter.split_text(content)
    try:
        if len(texts) > 3:
            group1 = sorted(texts[:len(texts)//3], key=len, reverse=True)[0]
            group2 = sorted(texts[len(texts)//3:(len(texts)*2)//3], key=len, reverse=True)[0]
            group3 = sorted(texts[(len(texts)*2)//3:], key=len, reverse=True)[0]
            texts = [group1, group2, group3]
        
        combined_results = combined_text_processing_single_call(first_page, texts)
        if combined_results==['null']:
            final_object=['null']
        else: 
            chunking_results = [result['feature_data'] for result in combined_results]
            author_result = [result['author_title_data'] for result in combined_results]
            
            chunking_result = sort_json_by_occurrence(chunking_results)
            author_title_result = sort_json_by_occurrence(author_result)
            
            title = f"{author_title_result['Title'][0]} - {author_title_result['Author'][0]}"
            words = get_commun_words(content, chunking_result)
            
            knowledge_base_categorization = model_knowledge_base_categorization(title, words)

            if knowledge_base_categorization==['null']:
                final_object=['null']
            else:
                objects = [
                    chunking_result,
                    author_title_result,
                    knowledge_base_categorization['knowledge_base_data'],
                    knowledge_base_categorization['cummon_words_data']
                ]
                
                counts = count_plot_types(objects)
                final_object = sort_json_by_occurrence(remove_low_occurrence_plot(objects, counts))
    except:
        final_object=['null']
    return final_object

# Function to check if file is already processed
def is_file_processed(file_name):
    return file_name in st.session_state.file_contents

def main():
    # Initialize session state for storing file contents
    if 'file_contents' not in st.session_state:
        st.session_state.file_contents = {}
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = []
    if 'non_processed_files' not in st.session_state:
        st.session_state.non_processed_files = []
    if 'objects_list' not in st.session_state:
        st.session_state.objects_list = []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=7000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    # Set page config to use a wide layout (optional)
    st.set_page_config(layout="wide")

    # Initialize the sidebar with empty elements
    st.sidebar.title("")
    st.sidebar.empty()  # This creates an empty placeholder in the sidebar
    st.title("Text Classification")

    # File uploader in the sidebar (allow multiple file uploads)
    uploaded_files = st.file_uploader("Upload books", type=["txt", "rtf"], accept_multiple_files=True)
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name
            if not is_file_processed(file_name):
                first_page, content = process_uploaded_file(uploaded_file)
                if content == "Unsupported file type":
                    st.write("Unsupported file type")
                else:
                    # Store the file content in session state
                    st.session_state.file_contents[file_name] = [content, first_page]
        
        # Process each file one by one
        #objects_list = []
        
        
        for file_name, data in list(st.session_state.file_contents.items()):
            if file_name not in st.session_state.processed_files:
                final_object = process_and_analyze_file(data[0], data[1], text_splitter)
                if final_object:
                    if final_object == ['null']:
                        st.session_state.non_processed_files.append(file_name)
                    else:
                        st.subheader(f"Generated JSON for {file_name}:")
                        st.json(final_object)
                        st.session_state.objects_list.append(final_object)
                # Mark the file as processed regardless of the result and remove it from session state
                st.session_state.processed_files.append(file_name)
                del st.session_state.file_contents[file_name]

        st.sidebar.subheader("Files that could not be processed:")
        st.sidebar.write(st.session_state.non_processed_files)
        

        if  st.session_state.objects_list:
            # Process each JSON object
            processed_data_list = []
            for json_object in  st.session_state.objects_list:
                processed_data = {key: ', '.join(value) if value else 'Unknown' for key, value in json_object.items()}
                processed_data_list.append(processed_data)

            # Convert the list of processed data to a DataFrame
            df = pd.DataFrame(processed_data_list)

            # Convert the combined DataFrame to CSV
            csv = df.to_csv(index=False).encode('utf-8')

            # Streamlit download button for the combined CSV in the sidebar
            st.sidebar.download_button(
                label="Download JSON as CSV",
                data=csv,
                file_name='combined_output.csv',
                mime='text/csv',
            )



if __name__ == '__main__':
    main()
