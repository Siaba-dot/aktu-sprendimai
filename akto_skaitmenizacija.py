import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import base64
import os

# Funkcija įterpti tekstą į PDF puslapį
def add_text_to_page(page, text, x=50, y=750):
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.drawString(x, y, text)
    can.save()
    packet.seek(0)
    new_pdf = PdfReader(packet)
    page.merge_page(new_pdf.pages[0])
    return page

# Funkcija parodyti PDF naršyklėje
def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f"""
        <iframe 
            src="data:application/pdf;base64,{base64_pdf}" 
            width="100%" 
            height="800px" 
            type="application/pdf">
        </iframe>
    """
    st.markdown(pdf_display, unsafe_allow_html=True)

# Streamlit aplikacija
st.set_page_config(page_title="Akto skaitmenizacija", layout="wide")
st.title("Akto skaitmenizacija iš daugiaaktinio PDF")

uploaded_file = st.file_uploader("Įkelk vieną PDF su daug aktų", type="pdf")

if uploaded_file is not None:
    input_pdf_path = "input_full.pdf"
    with open(input_pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    pdf_reader = PdfReader(input_pdf_path)
    num_pages = len(pdf_reader.pages)

    st.success(f"Įkeltas failas turi {num_pages} puslapius (aktus).")

    if not os.path.exists("output_files"):
        os.makedirs("output_files")

    for idx, page in enumerate(pdf_reader.pages):
        st.divider()
        st.subheader(f"Akto {idx+1} peržiūra")

        temp_writer = PdfWriter()
        temp_writer.add_page(page)
        temp_page_path = f"temp_page_{idx}.pdf"
        with open(temp_page_path, "wb") as f:
            temp_writer.write(f)

        # Rodome PDF
        show_pdf(temp_page_path)

        # Įvedamas kodas
        skyriaus_kodas = st.text_input(f"Įvesk skyrių kodą aktui {idx+1}:", key=f"input_{idx}")

        # Mygtukas
        if st.button(f"Išsaugoti aktą {idx+1} su kodu", key=f"button_{idx}"):
            modified_page = add_text_to_page(page, skyriaus_kodas)

            first_three_letters = skyriaus_kodas[:3]
            folder_path = os.path.join("output_files", first_three_letters)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            base_filename = f"{first_three_letters}_aktas_{idx+1}_su_kodu.pdf"
            output_path = os.path.join(folder_path, base_filename)

            counter = 1
            while os.path.exists(output_path):
                base_filename = f"{first_three_letters}_aktas_{idx+1}_su_kodu_{counter}.pdf"
                output_path = os.path.join(folder_path, base_filename)
                counter += 1

            output_writer = PdfWriter()
            output_writer.add_page(modified_page)
            with open(output_path, "wb") as f:
                output_writer.write(f)

            st.success(f"Aktas {idx+1} su kodu išsaugotas į aplanką {first_three_letters}!")

            with open(output_path, "rb") as f:
                st.download_button(
                    label=f"Atsisiųsti aktą {idx+1}",
                    data=f,
                    file_name=os.path.basename(output_path),
                    mime="application/pdf"
                )
