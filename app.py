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
    pattern = r"@mndl\.bio|test|sella\.rafaeli|talia\.rapoport04|nony\.ux|elanitleiter|eugenia\.vovk|kfir@shapira|eranmilddf|talimiller|username\.com"
    df = df[~df["email"].str.contains(pattern, case=False, na=False)]

    # 6. Custom event priority
    priority_order = [
        "download_gb_file_click",     # ← now highest priority (index 0)
        "proj_status_update_final",   # index 1
        "project_submitted",          # index 2
        "gene_added",                 # index 3
        "create_project",             # index 4
        "launch_proj_btn_click",      # index 5
        "login"                       # index 6 (lowest)
    ]
    priority_map = {e: i for i, e in enumerate(priority_order)}
    df["priority"] = df["event"].map(priority_map).fillna(len(priority_order))

    # --- NEW: normalize project names for deduping (case/space-insensitive) ---
    df["project_norm"] = (
        df["project"]
        .astype(str)
        .str.strip()
        .str.lower()
        .replace({"": pd.NA, "nan": pd.NA, "none": pd.NA})
    )

    # 7. Sort by (priority asc, event_dt desc)
    df = df.sort_values(["priority", "event_dt"], ascending=[True, False])

    # 8a) Registered = first activity
    registered = (
        df.groupby("email", as_index=False)
          .agg({"event_dt":"min"})
          .rename(columns={"event_dt":"registered"})
    )
    
    # 8b) Started project = latest create_project (using normalized names, ignore blanks)
    create_events = df[(df["event"] == "create_project") & df["project_norm"].notna()]
    started = (
        create_events.groupby("email", as_index=False)
                     .agg({"event_dt":"max"})
                     .rename(columns={"event_dt":"started_project"})
    )
    
    # 8c) Submitted project = latest project_submitted
    submitted = (
        df[df["event"]=="project_submitted"]
          .groupby("email", as_index=False)
          .agg({"event_dt":"max"})
          .rename(columns={"event_dt":"submitted_project"})
    )

    # 8c.1) Count of UNIQUE project names per email (dedup by project_norm)
    project_count = (
        create_events
          .groupby("email", as_index=False)
          .agg(project_count=("project_norm", "nunique"))
    )
    
    # 8d) Base info (one row per email for names/project based on newest create_project)
    #     We keep the *latest* create_project row per email (after filtering blanks)
    newest_created_project = (
        create_events
          .sort_values("event_dt", ascending=False)
          .groupby("email", as_index=False)
          .first()[["email", "first_name", "last_name", "project"]]
    )

    # ─── 8e) Merge all date tables together ───
    merged = (
        newest_created_project
        .merge(registered, on="email", how="left")
        .merge(started,    on="email", how="left")
        .merge(submitted,  on="email", how="left")
        .merge(project_count, on="email", how="left")
    )
    merged["project_count"] = merged["project_count"].fillna(0).astype(int)

    # ─── 8f) Remove exact duplicates only (same name + same email) ───
    merged["first_name_lower"] = merged["first_name"].str.lower()
    merged["last_name_lower"] = merged["last_name"].str.lower()
    merged["email_lower"] = merged["email"].str.lower()
    merged = (
        merged
        .drop_duplicates(
            subset=["first_name_lower", "last_name_lower", "email_lower"],
            keep="first"
        )
        .drop(columns=["first_name_lower", "last_name_lower", "email_lower"])
    )

    # 9. Create formatted date display columns, keep original for sorting
    for col in ["registered", "started_project", "submitted_project"]:
        merged[col + "_display"] = merged[col].dt.strftime("%B %d, %Y").fillna("")
    
    # ─── 10. Checkbox to choose newest vs oldest ───
    newest_first = st.checkbox("Show newest registrations first", value=True)
    if newest_first:
        display_df = merged.sort_values("registered", ascending=False)
    else:
        display_df = merged.sort_values("registered", ascending=True)

    # ─── 11. Display and download (MUST be inside the else!) ───
    st.subheader("Latest Events by Client")

    cols = [
        "first_name",
        "last_name",
        "email",
        "project",
        "project_count",
        "registered_display",
        "started_project_display",
        "submitted_project_display"
    ]
    renamed_df = (
        display_df[cols]
        .rename(columns={
            "first_name": "First Name",
            "last_name": "Last Name",
            "email": "Email",
            "project": "Project Name",
            "project_count": "Distinct Project Count",
            "registered_display": "Registered",
            "started_project_display": "Started Project",
            "submitted_project_display": "Submitted Project"
        })
    )

    st.dataframe(renamed_df, use_container_width=True)

    csv_bytes = renamed_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download latest events as CSV",
        data=csv_bytes,
        file_name="latest_events.csv",
        mime="text/csv"
    )
