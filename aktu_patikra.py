import streamlit as st
import os
import pandas as pd
import re
from collections import Counter
from PyPDF2 import PdfReader

# Funkcija nuskaityti skyrių kodą iš PDF failo
def extract_skyrius_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        first_page = reader.pages[0]
        text = first_page.extract_text()

        if text:
            # Regex su lietuviškomis raidėmis
            match = re.search(r'\b[A-ZĄČĘĖĮŠŲŪŽ]{3}\.[A-ZĄČĘĖĮŠŲŪŽ]\.[A-ZĄČĘĖĮŠŲŪŽ]\.[A-ZĄČĘĖĮŠŲŪŽ0-9]{1,3}\b', text, flags=re.UNICODE)
            if match:
                return match.group()
        return None
    except Exception as e:
        return None

st.title("🔍 Aktų palyginimas su Excel sąrašu (kiekiai ir pavadinimai)")

# Įkeliam Excel failą
uploaded_file = st.file_uploader("Įkelk Excel failą su skyrių sąrašu", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Nuskaitom visus sheet'us ir sujungiame
        sheets = pd.read_excel(uploaded_file, sheet_name=None)
        df = pd.concat(sheets.values(), ignore_index=True)

        if "Skyrius" not in df.columns:
            st.error("❗ Excel faile nerastas stulpelis 'Skyrius'. Patikrink failo struktūrą.")
        else:
            skyriai_excel = df["Skyrius"].dropna().tolist()
            skyriai_excel = [s.strip() for s in skyriai_excel]

            # Nuskaityti visus aktų failus
            aktai_folder = "output_files"
            aktai_su_skyrium = []
            failai_be_skiriaus = []
            total_files = 0

            for root, dirs, files in os.walk(aktai_folder):
                for file in files:
                    if file.endswith(".pdf"):
                        total_files += 1
                        file_path = os.path.join(root, file)
                        skyrius = extract_skyrius_from_pdf(file_path)
                        if skyrius:
                            aktai_su_skyrium.append(skyrius)
                        else:
                            failai_be_skiriaus.append(file)

            # SUSKAIČIUOJAM kiek kartų kiekvienas skyrius pasikartoja
            excel_counter = Counter(skyriai_excel)
            failu_counter = Counter(aktai_su_skyrium)

            # Palyginam kiekį
            truksta_aktu = {}
            perdaug_aktu = {}

            for skyrius, kiekis in excel_counter.items():
                if failu_counter[skyrius] < kiekis:
                    truksta_aktu[skyrius] = kiekis - failu_counter.get(skyrius, 0)

            for skyrius, kiekis in failu_counter.items():
                if excel_counter.get(skyrius, 0) < kiekis:
                    perdaug_aktu[skyrius] = kiekis - excel_counter.get(skyrius, 0)

            # Rezultatai
            st.subheader("📊 Rezultatai:")

            st.info(f"🔹 Nuskaityta PDF failų: {total_files}")
            st.info(f"🔹 Aktų, iš kurių ištrauktas skyrius: {len(aktai_su_skyrium)}")
            st.info(f"🔹 Aktų, kuriuose skyrius nerastas: {len(failai_be_skiriaus)}")

            if truksta_aktu:
                st.error("❗ Trūkstami aktai pagal kiekius (failuose per mažai nei reikia Excel'e):")
                st.dataframe(pd.DataFrame(list(truksta_aktu.items()), columns=["Skyrius", "Trūksta kiekio"]))
            else:
                st.success("✅ Visi skyriai pagal kiekius sutampa!")

            if perdaug_aktu:
                st.warning("⚠️ Pertekliniai aktai pagal kiekius (failuose per daug nei reikia Excel'e):")
                st.dataframe(pd.DataFrame(list(perdaug_aktu.items()), columns=["Skyrius", "Perdaug kiekio"]))
            else:
                st.success("✅ Nėra perteklinių aktų failuose!")

            if failai_be_skiriaus:
                st.warning("⚠️ PDF failai, kuriuose nepavyko rasti skyriaus:")
                st.dataframe(pd.DataFrame(sorted(failai_be_skiriaus), columns=["Failo pavadinimas"]))

    except Exception as e:
        st.error(f"❗ Klaida skaitant failą: {e}")
else:
    st.info("🔹 Įkelk Excel failą, kad pradėtum tikrinimą.")
