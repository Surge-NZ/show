import os
from PyPDF2 import PdfReader
import re
import pandas as pd

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    pdf_reader = PdfReader(open(pdf_path, 'rb'))
    text = ''
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Function to parse the extracted text and return the options and comments for the specified section
def parse_section_options(text, section):
    lines = text.split('\n')
    submissions = []
    submission_data = {
        'Submission #': '',
        'First name': '',
        'Last name': '',
        f'{section} Option': '',
        f'{section} Comments': ''
    }

    option_pattern = re.compile(r'(Option \d+|Something else \(state below\)|Don\'t know)')
    comments_pattern = re.compile(r'Submit(?:ter|ted) Comments:')
    section_pattern = re.compile(r'([A-Z][a-z]+ [A-Z][a-z]+)')
    end_of_submission_pattern = re.compile(r'^Submission #')

    for i in range(len(lines)):
        line = lines[i].strip()

        if line.startswith('Submission #'):
            if submission_data['Submission #']:  # Save the previous submission
                submissions.append(submission_data.copy())
                submission_data = {key: '' for key in submission_data}  # Reset for the next submission
            submission_data['Submission #'] = line.split('#')[-1].strip()
        elif line.startswith('First name:'):
            submission_data['First name'] = line.split(':')[-1].strip()
        elif line.startswith('Last name:'):
            submission_data['Last name'] = line.split(':')[-1].strip()

        if section in line:
            print(f"Found section: {section} at line {i}")  # Debugging statement
            # Extract option
            for j in range(i+1, len(lines)):
                option_line = lines[j].strip()
                match = option_pattern.search(option_line)
                if match:
                    submission_data[f'{section} Option'] = match.group(0)
                    print(f"Found option for {section}: {match.group(0)}")  # Debugging statement
                    break
                elif comments_pattern.search(option_line):
                    # Stop if we reach submitter comments without finding an option
                    break

            # Extract comments
            comments_found = False
            comments = []
            for k in range(j, len(lines)):
                comments_line = lines[k].strip()
                if comments_pattern.search(comments_line):
                    comments_line = comments_line.split('Submitter Comments:')[-1].strip()  # Get text after 'Submitter Comments:'
                    comments.append(comments_line)
                    comments_found = True
                    print(f"Found comments for {section} at line {k}: {comments_line}")  # Debugging statement
                elif end_of_submission_pattern.search(comments_line):
                    break
                elif section_pattern.search(comments_line) and not comments_pattern.search(comments_line):
                    break
                elif comments_found:
                    if "Mainstreet hanging flower baskets" in comments_line:
                        break
                    comments.append(comments_line)

            if comments_found:
                submission_data[f'{section} Comments'] = ' '.join(comments)
            else:
                submission_data[f'{section} Comments'] = ''

    if submission_data['Submission #']:  # Append the last submission
        submissions.append(submission_data)

    return submissions

# Main code
folder_path = './submissions'
all_submissions = []

# Process all PDF files in the folder
for filename in os.listdir(folder_path):
    if filename.endswith('.pdf'):
        pdf_path = os.path.join(folder_path, filename)
        text = extract_text_from_pdf(pdf_path)
        submissions = parse_section_options(text, "Rotokawau/Virginia Lake Aviary")
        all_submissions.extend(submissions)

# Create a DataFrame for the submissions
df = pd.DataFrame(all_submissions)

# Clean up comments to remove any remaining section headers and unwanted phrases
unwanted_phrases = [
    'Our preferred option is to remove the hanging flower baskets. Which option do you prefer?',
    'Mainstreet hanging flower baskets'
]
for phrase in unwanted_phrases:
    df['Rotokawau/Virginia Lake Aviary Comments'] = df['Rotokawau/Virginia Lake Aviary Comments'].str.replace(phrase, '', regex=False).str.strip()

# Save the DataFrame to a CSV file
df.to_csv('aviary_options_with_comments.csv', index=False)

print("Data has been saved to aviary_options_with_comments.csv")
