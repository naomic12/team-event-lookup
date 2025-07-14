import streamlit as st
import pandas as pd

st.title("Client → Latest Event Lookup")

# 1. File uploader
uploaded = st.file_uploader("Upload your events CSV", type="csv")
if uploaded is None:
    st.warning("⚠️ Please upload a CSV file first.")
    st.stop()

# 2. Read & parse timestamps
df = pd.read_csv(
    uploaded,
    parse_dates=["event date"],
    date_parser=lambda x: pd.to_datetime(x, utc=True)
)

# 3. Sort chronologically
df = df.sort_values("event date")

# 4. Filter out internal/test emails
pattern = r"@mndl\\.bio|test|sella\\.rafaeli|talia\\.rapoport04|nony\\.ux|elanitleiter"
df = df[~df["email"].str.contains(pattern, case=False, na=False)]

# 5. Format date to dd/mm/yyyy
df["event date"] = df["event date"].dt.strftime("%d/%m/%Y")

# 6. Custom event priority
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

# 7. Sort by (priority asc, date desc)
df = df.sort_values(["priority", "event date"], ascending=[True, False])

# 8. Group per email and take one row
latest = (
    df
    .groupby("email", as_index=False)
    .first()[["first_name", "last_name", "email", "project", "event", "event date"]]
)

# 9. Show and let users download
st.subheader("Latest Event by Client")
st.dataframe(latest, use_container_width=True)

csv_bytes = latest.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download latest events as CSV",
    data=csv_bytes,
    file_name="latest_events.csv",
    mime="text/csv"
)
