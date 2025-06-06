# -*- coding: utf-8 -*-
"""app.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1ivmtu2UhKD3bm_qMf0O8S4hBVD41kRtB
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from PIL import Image

# --- Config ---
st.set_page_config(page_title="Invoice Risk Dashboard", layout="wide")
logo = Image.open("logo.png")
st.sidebar.image(logo, use_container_width=True)

# --- Load & clean ---
df = pd.read_csv("final_supplier_risk.csv", parse_dates=["Invoice_Date", "Due_Date", "Payment_Date"])
df["Status"] = df["Status"].astype(str).str.strip().str.title()
df["Payment_Status"] = df["Payment_Status"].astype(str).str.strip().str.title()

# Ensure Due_Date is datetime
df["Due_Date"] = pd.to_datetime(df["Due_Date"])

# Define today's date
today = datetime.today().date()

# Create dynamic flags
df["Unpaid_LatePayNow_Flag"] = df["Due_Date"].dt.date < today
df["Unpaid_TodayPayNow_Flag"] = df["Due_Date"].dt.date == today
df["Unpaid_HighPriority_Flag"] = df["Due_Date"].dt.date == today + timedelta(days=2)
df["Unpaid_Priority_Flag"] = df["Due_Date"].dt.date == today + timedelta(days=7)
df["Unpaid_Flag"] = df["Due_Date"].dt.date > today + timedelta(days=7)


# ---------- SIDEBAR FILTERS ----------
st.sidebar.header("Filters")

# Step 1: Supplier Type
supplier_type = st.sidebar.multiselect(
    "Supplier Type",
    sorted(df["Supplier_Type"].dropna().unique())
)

# Step 2: Service Category (depends on supplier type)
if supplier_type:
    filtered_df = df[df["Supplier_Type"].isin(supplier_type)]
else:
    filtered_df = df.copy()

service_cat = st.sidebar.multiselect(
    "Service Category",
    sorted(filtered_df["Service_Category"].dropna().unique())
)

# Step 3: Supplier Name (depends on both type + service category)
if service_cat:
    filtered_df = filtered_df[filtered_df["Service_Category"].isin(service_cat)]

supplier_name = st.sidebar.multiselect(
    "Supplier Name",
    sorted(filtered_df["Name"].dropna().unique())
)

# Step 4: Optional Date Range with Toggle
enable_date_filter = st.sidebar.checkbox("Filter by Invoice Date Range")

if enable_date_filter:
    invoice_date_range = st.sidebar.date_input(
        "Invoice Date Range",
        value=(df["Invoice_Date"].min(), df["Invoice_Date"].max()),
        min_value=df["Invoice_Date"].min(),
        max_value=df["Invoice_Date"].max()
    )
else:
    invoice_date_range = None


# ---------- APPLY FILTERS ----------
df_filtered = df.copy()
for col in [
    "Unpaid_LatePayNow_Flag",
    "Unpaid_TodayPayNow_Flag",
    "Unpaid_HighPriority_Flag",
    "Unpaid_Priority_Flag",
    "Unpaid_Flag"
]:
    df_filtered[col] = df[col]

if supplier_type:
    df_filtered = df_filtered[df_filtered["Supplier_Type"].isin(supplier_type)]
if service_cat:
    df_filtered = df_filtered[df_filtered["Service_Category"].isin(service_cat)]
if supplier_name:
    df_filtered = df_filtered[df_filtered["Name"].isin(supplier_name)]
# Apply date range filter only if both start and end dates are selected
if invoice_date_range:
    if isinstance(invoice_date_range, tuple) and len(invoice_date_range) == 2:
        start_date, end_date = invoice_date_range
        if start_date and end_date:
            df_filtered = df_filtered[
                (df_filtered["Invoice_Date"] >= pd.to_datetime(start_date)) &
                (df_filtered["Invoice_Date"] <= pd.to_datetime(end_date))
            ]


# --- Tabs ---
st.markdown("""<h1 style="text-align:left; color:#1f77b4;">Agri Cross Invoice Dashboard</h1>""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["Key Insights", "Risk Overview", "To Pay Hub", "Supplier Profile"])


# ---------------- Tab 1: Key Insights ----------------
with tab1:
    st.header("Key Insights")

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Invoices", len(df_filtered))
    col2.metric("Total Invoice Amount", f"${df_filtered['Invoice_Amount'].sum():,.0f}")
    col3.metric("Paid On Time", df_filtered[df_filtered["Status"] == "On Time"].shape[0])
    col4.metric("Paid Late", df_filtered[df_filtered["Status"] == "Late"].shape[0])

    col5, col6, col7 = st.columns(3)
    total_invoices = len(df_filtered)
    late_invoices = df_filtered[df_filtered["Status"] == "Late"].shape[0]
    avg_invoice_amt = df_filtered["Invoice_Amount"].mean()
    df_filtered["Days_Late"] = (df_filtered["Payment_Date"] - df_filtered["Due_Date"]).dt.days
    avg_days_late = df_filtered[df_filtered["Days_Late"] > 0]["Days_Late"].mean()

    col5.metric("% Paid Late", f"{(late_invoices / total_invoices * 100):.1f}%" if total_invoices else "0%")
    col6.metric("Avg Invoice Amount", f"${avg_invoice_amt:,.2f}")
    col7.metric("Avg Days Late", f"{avg_days_late:.1f}" if not pd.isna(avg_days_late) else "N/A")

    # Line Chart - Monthly Invoice Totals
    st.markdown(f"""<div style="background-color:#e6f2ff; padding:10px; border:1px solid #1f77b4; border-radius:5px; margin-bottom:10px;"><strong>{"Invoice Amount Over Time"}</strong></div>""", unsafe_allow_html=True)
    monthly = df_filtered.copy()
    monthly["Month"] = monthly["Invoice_Date"].dt.to_period("M").astype(str)
    monthly_sum = monthly.groupby("Month")["Invoice_Amount"].sum().reset_index()
    st.plotly_chart(px.line(monthly_sum, x="Month", y="Invoice_Amount"), use_container_width=True)

    # Late Payment % Over Time
    st.markdown(f"""<div style="background-color:#e6f2ff; padding:10px; border:1px solid #1f77b4; border-radius:5px; margin-bottom:10px;"><strong>{"Late Payment % Over Time"}</strong></div>""", unsafe_allow_html=True)
    monthly_late = df_filtered.copy()
    monthly_late["Month"] = monthly_late["Invoice_Date"].dt.to_period("M").astype(str)
    monthly_late_grouped = monthly_late.groupby("Month")["Paid_Late_Flag"].mean().reset_index()
    monthly_late_grouped["Late %"] = monthly_late_grouped["Paid_Late_Flag"] * 100
    fig_late = px.line(monthly_late_grouped, x="Month", y="Late %")
    st.plotly_chart(fig_late, use_container_width=True)

    # Donut Chart - Invoice Status
    st.markdown(f"""<div style="background-color:#e6f2ff; padding:10px; border:1px solid #1f77b4; border-radius:5px; margin-bottom:10px;"><strong>{"Invoice Status Distribution"}</strong></div>""", unsafe_allow_html=True)
    status_counts = df_filtered["Status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    st.plotly_chart(px.pie(status_counts, names="Status", values="Count", hole=0.5), use_container_width=True)

    # Top 10 Suppliers by Amount
    st.markdown(f"""<div style="background-color:#e6f2ff; padding:10px; border:1px solid #1f77b4; border-radius:5px; margin-bottom:10px;"><strong>{"Top 10 Suppliers by Amount"}</strong></div>""", unsafe_allow_html=True)
    top_amt = df_filtered.groupby(["Supplier_ID", "Name"])["Invoice_Amount"].sum().nlargest(10).reset_index()
    st.dataframe(top_amt)

    # Top 10 Suppliers by Frequency
    st.markdown(f"""<div style="background-color:#e6f2ff; padding:10px; border:1px solid #1f77b4; border-radius:5px; margin-bottom:10px;"><strong>{"Top 10 Suppliers by Frequency of Invoices"}</strong></div>""", unsafe_allow_html=True)
    top_freq = df_filtered.groupby(["Supplier_ID", "Name"]).size().nlargest(10).reset_index(name="Invoice Count")
    st.dataframe(top_freq)


# ---------------- Tab 2: Risk Overview ----------------
with tab2:
    st.header("Risk Overview")

    # ---- Risk KPI Cards ----
    col7, col8, col9 = st.columns(3)
    col7.metric("Duplicate ABNs", int(df_filtered["Duplicate_ABN"].sum()))
    col8.metric("Duplicate Invoices", int(df_filtered["Duplicate_Invoice"].sum()))
    col9.metric("High Amount Invoices > 30k", int(df_filtered["High_Amount"].sum()))

    # ----- Risk Heatmap -----
    st.markdown(f"""<div style="background-color:#e6f2ff; padding:10px; border:1px solid #1f77b4; border-radius:5px; margin-bottom:10px;"><strong>{"Risk Heatmap"}</strong></div>""", unsafe_allow_html=True)
    st.caption("Average Risk Score by Service Category and Supplier Type")

    heatmap_data = df_filtered.copy()
    pivot_data = (
        heatmap_data
        .groupby(["Service_Category", "Supplier_Type"])["Risk_Score"]
        .mean()
        .reset_index()
    )

    fig_heatmap = px.density_heatmap(
        pivot_data,
        x="Supplier_Type",
        y="Service_Category",
        z="Risk_Score",
        color_continuous_scale="Reds",
        height=500,
        width=800,
    )

    fig_heatmap.update_layout(
        font=dict(size=14),
        xaxis_title="Supplier Type",
        yaxis_title="Service Category",
        margin=dict(l=60, r=40, t=60, b=60),
        coloraxis_colorbar=dict(title="Avg Risk Score", ticks="outside"),
    )

    st.plotly_chart(fig_heatmap, use_container_width=False)

    # ---- Risk Score Bar Chart (Excluding 0) ----

    st.markdown(f"""<div style="background-color:#e6f2ff; padding:10px; border:1px solid #1f77b4; border-radius:5px; margin-bottom:10px;"><strong>{"Invoices by Risk Score (1-3 Only)"}</strong></div>""", unsafe_allow_html=True)

    if "Risk_Score" in df_filtered.columns and not df_filtered["Risk_Score"].dropna().empty:
        filtered_risks = df_filtered[df_filtered["Risk_Score"].isin([1, 2, 3])]
        risk_counts = filtered_risks["Risk_Score"].value_counts().sort_index().reset_index()
        risk_counts.columns = ["Risk Score", "Count"]

        colour_map = {
            1: "#FFD700",  # Yellow
            2: "#FFA500",  # Orange
            3: "#FF4500"   # Red
        }
        risk_counts["Colour"] = risk_counts["Risk Score"].map(colour_map)

        fig = px.bar(
            risk_counts,
            x="Count",
            y="Risk Score",
            orientation="h",
            color="Risk Score",
            color_discrete_map=colour_map,
            log_x=True
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No risk score data available to display.")

    # ---- Risk Score Filtered Invoice Table ----
    st.markdown(f"""<div style="background-color:#e6f2ff; padding:10px; border:1px solid #1f77b4; border-radius:5px; margin-bottom:10px;"><strong>{"List of Invoices with Risk"}</strong></div>""", unsafe_allow_html=True)

    display_risk_labels = {
        1: "🟨 Low Risk (Score 1)",
        2: "🟧 Medium Risk (Score 2)",
        3: "🟥 High Risk (Score 3)"
    }
    reverse_risk_lookup = {v: k for k, v in display_risk_labels.items()}

    selected_risk_label = st.radio(
        "Select Risk Category",
        [display_risk_labels[k] for k in [1, 2, 3]],
        horizontal=True
    )

    selected_risk_score = reverse_risk_lookup[selected_risk_label]
    risk_filtered_df = df_filtered[df_filtered["Risk_Score"] == selected_risk_score]

    st.dataframe(
        risk_filtered_df[["Invoice_ID", "Name", "Invoice_Amount", "Due_Date", "Risk_Score"]],
        use_container_width=True
    )



# ---------------- Tab 3: To Pay Hub ----------------
with tab3:
    st.header("To Pay Hub")

    from datetime import datetime

    # Dynamically create derived status using flags
    unpaid_df = df_filtered.copy()
    unpaid_df["Payment_Status_Derived"] = "Other"
    unpaid_df.loc[unpaid_df["Unpaid_Flag"] == 1, "Payment_Status_Derived"] = "Unpaid"
    unpaid_df.loc[unpaid_df["Unpaid_HighPriority_Flag"] == 1, "Payment_Status_Derived"] = "Unpaid_HighPriority"
    unpaid_df.loc[unpaid_df["Unpaid_LatePayNow_Flag"] == 1, "Payment_Status_Derived"] = "Unpaid_LatePayNow"
    unpaid_df.loc[unpaid_df["Unpaid_TodayPayNow_Flag"] == 1, "Payment_Status_Derived"] = "Unpaid_TodayPayNow"
    unpaid_df.loc[unpaid_df["Unpaid_Priority_Flag"] == 1, "Payment_Status_Derived"] = "Unpaid_Priority"

    # Keep only these
    unpaid_statuses = [
        "Unpaid_LatePayNow",
        "Unpaid_TodayPayNow",
        "Unpaid_HighPriority",
        "Unpaid_Priority",
        "Unpaid"
    ]
    unpaid_df = unpaid_df[unpaid_df["Payment_Status_Derived"].isin(unpaid_statuses)]

    # Donut Chart
    st.markdown(f"""<div style="background-color:#e6f2ff; padding:10px; border:1px solid #1f77b4; border-radius:5px; margin-bottom:10px;"><strong>Unpaid Invoice Categories as of {datetime.today().strftime('%d %b %Y')}</strong></div>""", unsafe_allow_html=True)
    unpaid_summary = unpaid_df["Payment_Status_Derived"].value_counts().reset_index()
    unpaid_summary.columns = ["Unpaid Status", "Count"]

    if not unpaid_summary.empty:
        st.plotly_chart(
            px.pie(unpaid_summary, names="Unpaid Status", values="Count", hole=0.4),
            use_container_width=True
        )
    else:
        st.warning("No unpaid invoice categories found.")

    # Display name mapping
    display_labels = {
        "Unpaid_LatePayNow": "🔴 Overdue",
        "Unpaid_TodayPayNow": "🔵 Due Today",
        "Unpaid_HighPriority": "🟠 Due in 2 Days",
        "Unpaid_Priority": "🟡 Due in 1 Week",
        "Unpaid": "🟢 Due Soon"
    }
    reverse_lookup = {v: k for k, v in display_labels.items()}

    st.markdown(f"""<div style="background-color:#e6f2ff; padding:10px; border:1px solid #1f77b4; border-radius:5px; margin-bottom:10px;"><strong>{"List of Invoices by Status"}</strong></div>""", unsafe_allow_html=True)
    selected_label = st.radio(
        "Select Category",
        [display_labels[k] for k in unpaid_statuses],
        horizontal=True
    )

    selected_unpaid_type = reverse_lookup[selected_label]
    filtered_table = unpaid_df[unpaid_df["Payment_Status_Derived"] == selected_unpaid_type]
    st.dataframe(filtered_table[["Invoice_ID", "Name", "Due_Date", "Invoice_Amount", "Payment_Status_Derived"]], use_container_width=True)

# ---------------- Tab 4: Supplier Profile ----------------
with tab4:
    st.header("Supplier Profile")

    supplier_selected = st.selectbox("Select Supplier", sorted(df_filtered["Name"].dropna().unique()))

    if supplier_selected:
        supplier_df = df_filtered[df_filtered["Name"] == supplier_selected]

        # Display Supplier Info in tiles
        info_cols = st.columns(4)
        info_cols[0].markdown(f"**Name:** {supplier_df['Name'].iloc[0]}")
        info_cols[1].markdown(f"**ABN:** {supplier_df['ABN'].iloc[0]}")
        info_cols[2].markdown(f"**Country:** {supplier_df['Country'].iloc[0]}")
        info_cols[3].markdown(f"**Service Category:** {supplier_df['Service_Category'].iloc[0]}")

        info_cols2 = st.columns(3)
        info_cols2[0].markdown(f"**Supplier Type:** {supplier_df['Supplier_Type'].iloc[0]}")
        info_cols2[1].markdown(f"**Terms (Days):** {supplier_df['Terms (Days)'].iloc[0]}")
        info_cols2[2].markdown(f"**Contact:** {supplier_df['Contact_Name'].iloc[0]} ({supplier_df['Contact_Email'].iloc[0]})")

        st.markdown(f"""<div style="background-color:#e6f2ff; padding:10px; border:1px solid #1f77b4; border-radius:5px; margin-bottom:10px;"><strong>{"Invoice Summary Stats"}</strong></div>""", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Invoices", len(supplier_df))
        col2.metric("Total Amount", f"${supplier_df['Invoice_Amount'].sum():,.0f}")
        col3.metric("Avg Invoice Amount", f"${supplier_df['Invoice_Amount'].mean():,.2f}")

        st.markdown(f"""<div style="background-color:#e6f2ff; padding:10px; border:1px solid #1f77b4; border-radius:5px; margin-bottom:10px;"><strong>{"Payment Performance Over Time"}</strong></div>""", unsafe_allow_html=True)
        monthly = supplier_df.copy()
        monthly["Month"] = monthly["Invoice_Date"].dt.to_period("M").astype(str)
        payment_perf = monthly.groupby("Month")["Paid_Late_Flag"].mean().reset_index()
        payment_perf["Late %"] = payment_perf["Paid_Late_Flag"] * 100

        import plotly.express as px
        fig1 = px.line(payment_perf, x="Month", y="Late %")
        st.plotly_chart(fig1, use_container_width=True)

        st.markdown(f"""<div style="background-color:#e6f2ff; padding:10px; border:1px solid #1f77b4; border-radius:5px; margin-bottom:10px;"><strong>{"Risk Score Distribution"}</strong></div>""", unsafe_allow_html=True)
        risk_dist = supplier_df["Risk_Score"].value_counts().sort_index().reset_index()
        risk_dist.columns = ["Risk Score", "Count"]
        fig2 = px.bar(risk_dist, x="Risk Score", y="Count")
        st.plotly_chart(fig2, use_container_width=True)