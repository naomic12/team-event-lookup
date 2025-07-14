import streamlit as st
import pandas as pd

st.title("Client → Latest Event Lookup")

# 1. File uploader
uploaded = st.file_uploader("Upload your events CSV", type="csv")

# 2. Read & parse timestamps (as UTC)
df = pd.read_csv(
    uploaded,
    parse_dates=["event date"],
    date_parser=lambda x: pd.to_datetime(x, utc=True)
)
# keep the real datetime for sorting
df["event_dt"] = df["event date"]

# 3. Sort chronologically by the datetime column
df = df.sort_values("event_dt")

# 4. Filter out internal/test emails
pattern = r"@mndl\.bio|test|sella\.rafaeli|talia\.rapoport04|nony\.ux|elanitleiter"
df = df[~df["email"].str.contains(pattern, case=False, na=False)]

# 5. Custom event priority
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

# 6. Sort by (priority asc, event_dt desc) so grouping picks highest-priority & newest
df = df.sort_values(["priority", "event_dt"], ascending=[True, False])

# 7. Group per email and take the first row of each group
latest = df.groupby("email", as_index=False).first()

# 8. Format the display date as dd/mm/YYYY
latest["event date"] = latest["event_dt"].dt.strftime("%d/%m/%Y")

# 9. Let user choose newest-first vs oldest-first
newest_first = st.checkbox("Show newest events first", value=True)
if newest_first:
    display_df = latest.sort_values("event_dt", ascending=False)
else:
    display_df = latest.sort_values("event_dt", ascending=True)

# 10. Display and download
st.subheader("Latest Event by Client")
st.dataframe(
    display_df[["first_name","last_name","email","project","event","event date"]],
    use_container_width=True
)

csv_bytes = display_df[["first_name","last_name","email","project","event","event date"]] \
    .to_csv(index=False).encode("utf-8")
st.download_button(
    "Download latest events as CSV",
    data=csv_bytes,
    file_name="latest_events.csv",
    mime="text/csv"
)
