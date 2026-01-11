import streamlit as st
import pandas as pd
from utils import load_and_process_stock, filter_stock_data

st.set_page_config(page_title="eBay File Processor", layout="wide")

# --- 1. S3 DATA LOADING ---
S3_PATH = "s3a://pop-eu-prod/390/200_feed/0/0/4e/056920.txt"

@st.cache_data
def get_cached_stock(path):
    return load_and_process_stock(path)

try:
    numerate_stock_df = get_cached_stock(S3_PATH)
except Exception as e:
    st.error(f"S3 Connection Error: {e}")
    st.stop()

# --- 2. SIDEBAR NAVIGATION ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["File Uploader", "Stock Feed Viewer"])

# --- PAGE 1: FILE UPLOADER ---
if page == "File Uploader":
    st.title("📦 eBay Listing Updater")
    st.markdown("Upload your eBay CSV to merge with the current stock feed.")
    
    ebay_file = st.file_uploader("Upload eBay CSV", type=["csv"])

    if ebay_file:
        try:
            # READ EBAY FILE
            ebay_file.seek(0)
            first_line = ebay_file.readline().decode('utf-8').strip()
            metadata_values = first_line.split(',')

            ebay_file.seek(0)
            ebay_listings = pd.read_csv(ebay_file, skiprows=1)

            # JOIN & UPDATE
            stock_subset = numerate_stock_df[['Custom label (SKU)', 'Stock', 'WholeSale Price']]
            ebay_listings_updated = ebay_listings.merge(stock_subset, on='Custom label (SKU)', how='left')

            ebay_listings_updated = ebay_listings_updated.drop(columns=['Available quantity', 'Start price'])
            ebay_listings_updated = ebay_listings_updated.rename(columns={
                'Stock': 'Available quantity',
                'WholeSale Price': 'Start price'
            })

            ebay_listings_updated['Available quantity'] = ebay_listings_updated['Available quantity'].fillna(0).astype(int)
            # Reorder & Clean
            original_cols = ebay_listings.columns.tolist()
            ebay_listings_updated = ebay_listings_updated[original_cols].astype(str).replace('nan', '')

            # Metadata Stacking
            padding = [""] * (len(original_cols) - len(metadata_values))
            metadata_row = pd.DataFrame([metadata_values + padding], columns=original_cols)
            header_row = pd.DataFrame([original_cols], columns=original_cols)
            ebay_listings_final = pd.concat([metadata_row, header_row, ebay_listings_updated], ignore_index=True)

            st.success("File processed successfully!")
            st.dataframe(ebay_listings_final.head(10))

            csv_out = ebay_listings_final.to_csv(index=False, header=False).encode('utf-8')
            st.download_button("Download eBay File", data=csv_out, file_name="ebay_upload.csv", mime="text/csv")

        except Exception as e:
            st.error(f"Error: {e}")

# --- PAGE 2: STOCK FEED VIEWER ---
elif page == "Stock Feed Viewer":
    st.title("🔍 Stock Feed Explorer")
    st.markdown("Search and filter the live data from Aosom.")

    # --- FILTERS ---
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_query = st.text_input("Search by SKU", "").strip()
    
    with col2:
        # Stock Status Filter
        status_filter = st.selectbox(
            "Stock Status",
            options=["All", "In Stock Only", "Out of Stock Only"]
        )

    # --- APPLY FILTERS ---

    filtered_df = filter_stock_data(S3_PATH)

    # Apply SKU Search
    if search_query:
        filtered_df = filtered_df[filtered_df['SKU'].str.contains(search_query, case=False, na=False)]

    # Apply Stock Status Filter
    if status_filter == "In Stock Only":
        filtered_df = filtered_df[filtered_df['Stock'] > 0]
    elif status_filter == "Out of Stock Only":
        filtered_df = filtered_df[filtered_df['Stock'] == 0]

    # --- DISPLAY METRICS ---
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("Total Items (Filtered)", len(filtered_df))
    m_col2.metric("In Stock", len(filtered_df[filtered_df['Stock'] > 0]))
    m_col3.metric("Out of Stock", len(filtered_df[filtered_df['Stock'] == 0]))

    # --- DISPLAY TABLE ---
    st.dataframe(filtered_df, use_container_width=True)