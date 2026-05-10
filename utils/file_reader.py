import pdfplumber
from docx import Document


def read_txt(file_path):

    with open(file_path, 'r', encoding='utf-8') as f:

        return f.read()


def read_pdf(file_path):

    text = ""

    with pdfplumber.open(file_path) as pdf:

        for page in pdf.pages:

            extracted = page.extract_text()

            if extracted:

                text += extracted + "\n"

    return text


def read_docx(file_path):

    doc = Document(file_path)

    text = "\n".join(
        [para.text for para in doc.paragraphs]
    )

    return text

def extract_text(file_path):

    if file_path.endswith(".txt"):

        return read_txt(file_path)

    elif file_path.endswith(".pdf"):

        return read_pdf(file_path)

    elif file_path.endswith(".docx"):

        return read_docx(file_path)

    else:

        return ""