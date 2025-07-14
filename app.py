import streamlit as st
import pandas as pd

st.title("Client → Latest Event Lookup")

uploaded = st.file_uploader("Upload your events CSV", type="csv")
if uploaded is None:
    st.warning("⚠️ Please upload a CSV file first.")
    st.stop()

df = pd.read_csv(
    uploaded,
    parse_dates=["event date"],
    date_parser=lambda x: pd.to_datetime(x, utc=True)
)

df = df.sort_values("event date")

pattern = r"@mndl\\.bio|test|sella\\.rafaeli|talia\\.rapoport04|nony\\.ux|elanitleiter"
df = df[~df["email"].str.contains(pattern, case=False, na=False)]

df["event date"] = df["event date"].dt.strftime("%d/%m/%Y")

priority_order = [
    "login",
    "launch_proj_btn_click",
    "create_project",
    "gene_added",
    "project_submitted",
    "proj_status_update_final",
    "download_gb_file_click"
]
priority_map = {e: i for i, e in enumerate(priority_order)}
df["priority"] = df["event"].map(priority_map).fillna(len(priority_order))

df = df.sort_values(["priority", "event date"], ascending=[True, False])

latest = (
    df
    .groupby("email", as_index=False)
    .first()[["first_name", "last_name", "email", "project", "event", "event date"]]
)

# New: sort direction control
newest_first = st.checkbox("Show newest events first", value=True)
if newest_first:
    display_df = latest.sort_values("event date", ascending=False)
else:
    display_df = latest.sort_values("event date", ascending=True)

st.subheader("Latest Event by Client")
st.dataframe(display_df, use_container_width=True)

csv_bytes = display_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download latest events as CSV",
    data=csv_bytes,
    file_name="latest_events.csv",
    mime="text/csv"
)
