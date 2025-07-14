import streamlit as st
import pandas as pd

st.title("Client → Latest Event Lookup")

# 1. File uploader
uploaded = st.file_uploader("Upload your events CSV", type="csv")

# 2. If no file yet, show an info message (not a “warning”)
if not uploaded:
    st.info("📤 Please upload a CSV file to see the latest events per client.")
else:
    # 3. Read & parse timestamps (as UTC)
    df = pd.read_csv(
        uploaded,
        parse_dates=["event date"],
        date_parser=lambda x: pd.to_datetime(x, utc=True)
    )
    df["event_dt"] = df["event date"]

    # 4. Sort chronologically by the datetime column
    df = df.sort_values("event_dt")

    # 5. Filter out internal/test emails
    pattern = r"@mndl\.bio|test|sella\.rafaeli|talia\.rapoport04|nony\.ux|elanitleiter"
    df = df[~df["email"].str.contains(pattern, case=False, na=False)]

    # 6. Custom event priority
    priority_order = [
    "download_gb_file_click",     # ← now highest priority (index 0)
    "proj_status_update_final",   # index 1
    "project_submitted",          # index 2
    "gene_added",                 # index 3
    "create_project",             # index 4
    "launch_proj_btn_click",      # index 5
    "login"                       # index 6 (now lowest)
    ]
    priority_map = {e: i for i, e in enumerate(priority_order)}
    df["priority"] = df["event"].map(priority_map).fillna(len(priority_order))

    # 7. Sort by (priority asc, event_dt desc)
    df = df.sort_values(["priority", "event_dt"], ascending=[True, False])

    # 8. Group per email and take the first row
    latest = df.groupby("email", as_index=False).first()

    # 9. Format display date as dd/mm/YYYY
    latest["event date"] = latest["event_dt"].dt.strftime("%d/%m/%Y")

    # 10. Checkbox to choose newest vs oldest
    newest_first = st.checkbox("Show newest events first", value=True)
    if newest_first:
        display_df = latest.sort_values("event_dt", ascending=False)
    else:
        display_df = latest.sort_values("event_dt", ascending=True)

    # 11. Display and download
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
