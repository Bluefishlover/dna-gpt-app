# DNA Analyzer with GPT-Powered SNP Explanation & Summary Report
import streamlit as st
import pandas as pd
import openai
from dotenv import load_dotenv
import os

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="🧬 DNA Analyzer", layout="wide")
st.title("🧬 AI-Powered DNA Analysis & Summary Generator")

uploaded_file = st.file_uploader("📄 Upload your 23andMe raw DNA file (.txt)", type="txt")

@st.cache_data
def load_csv(filename):
    return pd.read_csv(filename)

# Load datasets
trait_db = load_csv("snp_traits.csv")
pharma_db = load_csv("pharma_snps.csv")
nutri_db = load_csv("nutrigenomics_snps.csv")
ancestry_db = load_csv("ancestry_snps.csv")
clinvar_db = load_csv("clinvar_filtered.csv")
pharmgkb_db = load_csv("pharmgkb_filtered.csv")
immune_db = load_csv("innatedb_gene_matches.csv")

def explain_snp(row):
    label = row.get("trait") or row.get("condition") or row.get("drug") or row.get("nutrient") or row.get("phenotype") or "a known variant"
    prompt = f"What does it mean if someone has the genotype {row['genotype']} at {row['rsid']} ({row['gene']}) which is associated with {label}? Explain clearly and comprehensively."
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ GPT Error: {e}"

def ask_gpt(question):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": question}],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ GPT Error: {e}"

if uploaded_file:
    data = [line.decode("utf-8").strip() for line in uploaded_file.readlines() if not line.decode("utf-8").startswith("#")]
    parsed = [line.split("\t") for line in data if len(line.split("\t")) == 4]
    user_df = pd.DataFrame(parsed, columns=["rsid", "chromosome", "position", "genotype"])
    user_df['rsid'] = user_df['rsid'].str.strip().str.lower()

    tab_labels = [
        "🧠 Traits", "💊 Pharmacogenomics", "🥗 Nutrigenomics", "🌍 Ancestry",
        "🧬 ClinVar Conditions", "💊 Drug Sensitivities", "🛡️ Immune Gene Matches", "📝 Summary Report", "💬 Ask GPT"
    ]
    tabs = st.tabs(tab_labels)
    dbs = [trait_db, pharma_db, nutri_db, ancestry_db, clinvar_db, pharmgkb_db, immune_db]

    match_data = []

    for i, db in enumerate(dbs):
        db['rsid'] = db['rsid'].astype(str).str.strip().str.lower()
        with tabs[i]:
            merged = pd.merge(user_df, db, on="rsid", how="inner")
            match_count = len(merged)
            st.write(f"✅ {match_count} SNPs matched in this category.")
            if not merged.empty:
                st.dataframe(merged)
                match_data.append((tab_labels[i], merged))
                selected = st.selectbox("Select a SNP for GPT explanation:", merged["rsid"].unique(), key=f"sel_{i}")
                row = merged[merged["rsid"] == selected].iloc[0]
                if st.button("🧠 Explain with GPT", key=f"explain_{i}"):
                    explanation = explain_snp(row)
                    st.markdown(f"**GPT Explanation:** {explanation}")
            else:
                st.info("No matches found in this category.")

    with tabs[7]:
        st.subheader("📝 One-Click Summary Report")
        if st.button("📄 Generate Summary"):
            summary = ""
            for label_text, df in match_data:
                summary += f"\n### {label_text}\n"
                for _, row in df.iterrows():
                    item = row.get('trait') or row.get('condition') or row.get('drug') or row.get('region') or row.get('phenotype') or ''
                    summary += f"- {row['rsid']} ({row['gene']}): {item}\n"
            st.text_area("Your Genetic Summary:", summary.strip(), height=300)
            st.download_button("📥 Download Summary", summary.strip(), file_name="dna_summary.txt")

    with tabs[8]:
        st.subheader("💬 Ask GPT Anything")
        question = st.text_input("Type your question about genetics, SNPs, or health:")
        if st.button("Ask GPT"):
            if question:
                response = ask_gpt(question)
                st.markdown(f"**GPT Response:** {response}")
            else:
                st.warning("Please enter a question before submitting.")

else:
    st.info("👆 Upload your 23andMe raw DNA file to begin analysis.")
