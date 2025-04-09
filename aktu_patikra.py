import streamlit as st
import pandas as pd
import re
from collections import Counter
from PyPDF2 import PdfReader

# Funkcija nuskaityti skyrių kodą iš PDF failo
def extract_skyrius_from_pdf(pdf_file):
    try:
        reader = PdfReader(pdf_file)
        first_page = reader.pages[0]
        text = first_page.extract_text()

        if text:
            match = re.search(r'\b[A-ZĄČĘĖĮŠŲŪŽ]{3}\.[A-ZĄČĘĖĮŠŲŪŽ]\.[A-ZĄČĘĖĮŠŲŪŽ]\.[A-ZĄČĘĖĮŠŲŪŽ0-9]{1,3}\b', text, flags=re.UNICODE)
            if match:
                return match.group()
        return None
    except Exception:
        return None

st.title("🔍 Aktų palyginimas su Excel sąrašu (kiekiai ir pavadinimai)")

# Įkėlimas
uploaded_excel = st.file_uploader("📥 Įkelk Excel failą su skyrių sąrašu", type=["xlsx"])
uploaded_pdfs = st.file_uploader("📥 Įkelk PDF aktų failus", type=["pdf"], accept_multiple_files=True)

if uploaded_excel and uploaded_pdfs:
    try:
        # Skaityti visus Excel sheet'us
        sheets = pd.read_excel(uploaded_excel, sheet_name=None)
        df = pd.concat(sheets.values(), ignore_index=True)

        if "Skyrius" not in df.columns:
            st.error("❗ Excel faile nerastas stulpelis 'Skyrius'. Patikrink failą.")
        else:
            skyriai_excel = df["Skyrius"].dropna().tolist()
            skyriai_excel = [s.strip() for s in skyriai_excel]

            aktai_su_skyrium = []
            failai_be_skiriaus = []

            for file in uploaded_pdfs:
                skyrius = extract_skyrius_from_pdf(file)
                if skyrius:
                    aktai_su_skyrium.append(skyrius)
                else:
                    failai_be_skiriaus.append(file.name)

            excel_counter = Counter(skyriai_excel)
            failu_counter = Counter(aktai_su_skyrium)

            truksta_aktu = {}
            perdaug_aktu = {}

            for skyrius, kiekis in excel_counter.items():
                if failu_counter[skyrius] < kiekis:
                    truksta_aktu[skyrius] = kiekis - failu_counter.get(skyrius, 0)

            for skyrius, kiekis in failu_counter.items():
                if excel_counter.get(skyrius, 0) < kiekis:
                    perdaug_aktu[skyrius] = kiekis - excel_counter.get(skyrius, 0)

            # REZULTATAI
            st.subheader("📊 Rezultatai:")
            st.info(f"🔹 Nuskaityta PDF failų: {len(uploaded_pdfs)}")
            st.info(f"🔹 Aktų su rastu skyriumi: {len(aktai_su_skyrium)}")
            st.info(f"🔹 Aktų be skyriaus: {len(failai_be_skiriaus)}")

            if truksta_aktu:
                st.error("❗ Trūkstami aktai (Excel nurodyta daugiau nei yra):")
                st.dataframe(pd.DataFrame(list(truksta_aktu.items()), columns=["Skyrius", "Trūksta kiekio"]))
            else:
                st.success("✅ Nėra trūkstamų aktų!")

            if perdaug_aktu:
                st.warning("⚠️ Pertekliniai aktai (failuose daugiau nei reikia):")
                st.dataframe(pd.DataFrame(list(perdaug_aktu.items()), columns=["Skyrius", "Perdaug kiekio"]))
            else:
                st.success("✅ Nėra perteklinių aktų!")

            if failai_be_skiriaus:
                st.warning("⚠️ Failai, kuriuose nerastas skyrius:")
                st.dataframe(pd.DataFrame(sorted(failai_be_skiriaus), columns=["Failo pavadinimas"]))
    except Exception as e:
        st.error(f"❗ Klaida: {e}")
else:
    st.info("🟦 Įkelk Excel failą ir PDF aktus, kad pradėtum tikrinimą.")
