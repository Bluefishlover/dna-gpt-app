# Streamlit DNA Analyzer v2 with OpenAI SDK v1.x and summary improvements
import streamlit as st
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="🧬 DNA Analyzer v2", layout="wide")
st.title("🧬 Enhanced DNA Analysis with GPT & Diagnostics")

uploaded_file = st.file_uploader("📄 Upload your 23andMe raw DNA file (.txt)", type="txt")

@st.cache_data
def load_csv(filename):
    df = pd.read_csv(filename)
    df['rsid'] = df['rsid'].astype(str).str.strip().str.lower()
    return df

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
        response = client.chat.completions.create(
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
        response = client.chat.completions.create(
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
        "🧬 ClinVar Conditions", "💊 Drug Sensitivities", "🛡️ Immune Gene Matches", "📝 Summary Report", "💬 Ask GPT", "🧪 Diagnostics"
    ]
    tabs = st.tabs(tab_labels)
    dbs = [trait_db, pharma_db, nutri_db, ancestry_db, clinvar_db, pharmgkb_db, immune_db]

    match_data = []
    match_counts = {}

    for i, db in enumerate(dbs):
        with tabs[i]:
            merged = pd.merge(user_df, db, on="rsid", how="inner")
            match_counts[tab_labels[i]] = len(merged)
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
                    main_item = row.get('trait') or row.get('condition') or row.get('drug') or row.get('region') or row.get('phenotype') or ''
                    extra = row.get('impact') or row.get('effect') or row.get('clinical_annotation') or row.get('notes') or ''
                    if extra:
                        main_item += f" — {extra}"
                    summary += f"- {row['rsid']} ({row['gene']}): {main_item}\n"
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

    with tabs[9]:
        st.subheader("🧪 Match Diagnostics")
        st.write(f"📥 Total uploaded SNPs: {len(user_df)}")
        for name, count in match_counts.items():
            st.write(f"✅ Matches in {name}: {count}")
        if st.checkbox("Show unmatched rsIDs"):
            matched_rsids = pd.concat([df["rsid"] for _, df in match_data]).unique()
            unmatched = user_df[~user_df["rsid"].isin(matched_rsids)]
            st.dataframe(unmatched)

else:
    st.info("👆 Upload your 23andMe raw DNA file to begin analysis.")
