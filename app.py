import streamlit as st
import pandas as pd
import plotly.express as px
import uuid

# ----------------------------------------------------
# 1. SETUP, BRANDING & GLOBALS
# ----------------------------------------------------
st.set_page_config(page_title="Atomberg Goal Portal", page_icon="⚛️", layout="wide")

st.markdown("""
    <style>
    .brand-header { font-size: 32px; font-weight: bold; color: #1E3A8A; margin-bottom: 0px; }
    .brand-sub { font-size: 16px; color: #64748B; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 2. IN-MEMORY DATABASE & STATE MANAGEMENT
# ----------------------------------------------------
INITIAL_GOALS = [
    {
        "Goal_ID": "G001", "Emp_Name": "Lakshin", "Role": "Employee",
        "Thrust_Area": "Product Innovation", "Title": "Optimize Fan Motor Efficiency",
        "UoM": "Maximize (Higher is Better)", "Target": 95.0, "Weightage": 20.0,
        "Status": "On Track", "Approval": "Pending", "Q1_Actual": 92.0,
        "Manager_Note": "", "Checkin_Feedback": ""
    },
    {
        "Goal_ID": "G002", "Emp_Name": "Lakshin", "Role": "Employee",
        "Thrust_Area": "Operations", "Title": "Reduce Assembly Line Waste",
        "UoM": "Minimize (Lower is Better)", "Target": 5.0, "Weightage": 20.0,
        "Status": "Not Started", "Approval": "Pending", "Q1_Actual": 0.0,
        "Manager_Note": "", "Checkin_Feedback": ""
    },
    {
        "Goal_ID": "G003", "Emp_Name": "Lakshin", "Role": "Employee",
        "Thrust_Area": "Safety", "Title": "Zero Factory Incidents",
        "UoM": "Zero (Binary)", "Target": 0.0, "Weightage": 30.0,
        "Status": "Completed", "Approval": "Pending", "Q1_Actual": 0.0,
        "Manager_Note": "", "Checkin_Feedback": ""
    }
]

if "goals_db" not in st.session_state:
    st.session_state.goals_db = pd.DataFrame(INITIAL_GOALS)

# FIX: current_user in session state so it can be switched per persona
if "current_user" not in st.session_state:
    st.session_state.current_user = "Lakshin"

# FIX: escalation log persisted in session state
if "escalation_log" not in st.session_state:
    st.session_state.escalation_log = []


def calculate_progress_score(uom, target, actual):
    """
    FIX: Minimize with target=0 now treated as Zero (Binary).
    All other logic retained with floor 0 / ceiling 100.
    """
    try:
        if uom == "Maximize (Higher is Better)":
            if target == 0:
                return 0.0
            score = (actual / target) * 100.0

        elif uom == "Minimize (Lower is Better)":
            # FIX: target=0 for Minimize is identical to Zero (Binary)
            if target == 0:
                return 100.0 if actual == 0 else 0.0
            if actual == 0:
                return 100.0
            score = (target / actual) * 100.0

        elif uom == "Zero (Binary)":
            score = 100.0 if actual == 0 else 0.0

        elif uom == "Timeline":
            score = 100.0 if actual <= target else 0.0

        else:
            return 0.0

        return max(0.0, min(score, 100.0))

    except Exception:
        return 0.0


def update_goal_by_id(goal_id, updates: dict):
    """
    FIX: All dataframe updates now go through Goal_ID lookup,
    never through the raw Pandas index. This prevents wrong-row
    updates when the dataframe is filtered before iteration.
    """
    mask = st.session_state.goals_db["Goal_ID"] == goal_id
    for col, val in updates.items():
        st.session_state.goals_db.loc[mask, col] = val


def generate_goal_id():
    """FIX: UUID-based IDs prevent duplicate keys on app restart."""
    return "G" + str(uuid.uuid4())[:6].upper()


# ----------------------------------------------------
# 3. INTERFACE - NAVIGATION SIDEBAR
# ----------------------------------------------------
with st.sidebar:
    st.markdown("<h1 style='color: #1E3A8A; margin-top: 0px;'>⚛️ Atomberg</h1>", unsafe_allow_html=True)
    st.markdown("### Goal Portal v1.3")
    st.markdown("---")

    # FIX: Persona selector also updates current_user in session state
    persona = st.radio(
        "Select User Persona Journey:",
        ["Employee View", "Manager View (L1)", "HR / Admin Dashboard"]
    )
    if persona == "Employee View":
        st.session_state.current_user = "Lakshin"

    st.markdown("---")
    st.warning("⚠️ **Role Isolation Disabled:** Shared session state active for multi-role demo testing.")

CURRENT_USER = st.session_state.current_user

# ----------------------------------------------------
# 4. VIEW RENDERING ENGINE
# ----------------------------------------------------

# --- JOURNEY A: EMPLOYEE INTERFACE ---
if persona == "Employee View":
    st.markdown(f'<p class="brand-header">🎯 Employee Workspace: {CURRENT_USER}</p>', unsafe_allow_html=True)
    st.markdown('<p class="brand-sub">Draft, align, and track your quarterly objectives.</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📝 Create & Submit Goals", "📈 Quarterly Progress"])

    with tab1:
        with st.expander("➕ Draft a New Performance Goal", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                thrust = st.selectbox("Thrust Area", ["Product Innovation", "Operations", "Customer Success", "Sustainability"])
                title = st.text_input("Goal Title")
            with col2:
                uom_type = st.selectbox("Unit of Measurement (UoM)", [
                    "Maximize (Higher is Better)",
                    "Minimize (Lower is Better)",
                    "Timeline",
                    "Zero (Binary)"
                ])
                target_val = st.number_input("Target Value", min_value=0.0, value=100.0)
                weight = st.number_input("Weightage (%)", min_value=0.0, max_value=100.0, step=5.0, value=10.0)

            if st.button("Add to Drafts", type="secondary"):
                current_employee_goals = st.session_state.goals_db[
                    st.session_state.goals_db["Emp_Name"] == CURRENT_USER
                ]
                current_weight = round(current_employee_goals["Weightage"].sum(), 2)

                if len(current_employee_goals) >= 8:
                    st.error("⛔ Max 8 goals allowed.")
                elif weight < 10.0:
                    st.error("⛔ Minimum weightage is 10%.")
                # FIX: Consistent float tolerance — matches the submit check
                elif round(current_weight + weight, 2) > 100.0:
                    st.error("⛔ Weightage exceeds 100%.")
                elif not title.strip():
                    st.warning("⚠️ Title cannot be blank.")
                else:
                    new_id = generate_goal_id()
                    new_row = {
                        "Goal_ID": new_id, "Emp_Name": CURRENT_USER, "Role": "Employee",
                        "Thrust_Area": thrust, "Title": title, "UoM": uom_type,
                        "Target": target_val, "Weightage": weight,
                        "Status": "Not Started", "Approval": "Pending",
                        "Q1_Actual": 0.0, "Manager_Note": "", "Checkin_Feedback": ""
                    }
                    st.session_state.goals_db = pd.concat(
                        [st.session_state.goals_db, pd.DataFrame([new_row])],
                        ignore_index=True
                    )
                    st.toast("Goal added successfully!", icon="✅")
                    st.rerun()

        st.divider()
        st.subheader("Your Active Ledger")
        my_current_sheet = st.session_state.goals_db[
            st.session_state.goals_db["Emp_Name"] == CURRENT_USER
        ]
        clean_display_sheet = my_current_sheet[[
            "Goal_ID", "Thrust_Area", "Title", "UoM", "Target", "Weightage", "Status", "Approval"
        ]]
        st.dataframe(clean_display_sheet, use_container_width=True, hide_index=True)

        # FIX: Allow deletion of Pending AND Returned (not just Pending) goals
        deletable_goals = my_current_sheet[my_current_sheet["Approval"] != "Approved"]
        if not deletable_goals.empty:
            st.markdown("🗑️ **Remove a Draft**")
            id_map = {
                f"{row['Goal_ID']} - {row['Title']}": row["Goal_ID"]
                for _, row in deletable_goals.iterrows()
            }
            del_c1, del_c2 = st.columns([3, 1])
            with del_c1:
                # FIX: label_visibility="hidden" preserves accessible label
                selected_del = st.selectbox(
                    "Select goal to delete",
                    list(id_map.keys()),
                    label_visibility="hidden"
                )
            with del_c2:
                confirm_del = st.checkbox("I am sure", key="del_confirm")
                if confirm_del and st.button("Delete Goal", type="secondary"):
                    target_id = id_map[selected_del]
                    st.session_state.goals_db = st.session_state.goals_db[
                        st.session_state.goals_db["Goal_ID"] != target_id
                    ]
                    st.toast(f"Removed Goal {target_id}", icon="🗑️")
                    st.rerun()

        st.divider()

        total_allocated_weight = round(my_current_sheet["Weightage"].sum(), 2)
        st.metric(label="Total Weightage Allocation", value=f"{total_allocated_weight}%")

        if abs(total_allocated_weight - 100.0) < 0.01:
            if st.button("Submit Final Goal Sheet", type="primary"):
                # FIX: Use Goal_ID-based update, not raw index
                pending_ids = my_current_sheet.loc[
                    my_current_sheet["Approval"] == "Pending", "Goal_ID"
                ].tolist()
                for gid in pending_ids:
                    update_goal_by_id(gid, {"Approval": "Submitted"})
                st.balloons()
                st.success("🚀 Sheet submitted securely to manager.")
                st.rerun()
        else:
            st.warning("⚠️ Complete allocation to exactly 100% to submit.")

    with tab2:
        st.subheader("Quarterly Achievement Log")
        editable_sheet = st.session_state.goals_db[
            st.session_state.goals_db["Emp_Name"] == CURRENT_USER
        ].copy()

        # FIX: Collect all pending changes first, then apply + rerun once
        # This avoids stale iterrows() state from mid-loop reruns
        pending_saves = {}

        for _, row in editable_sheet.iterrows():
            goal_id = row["Goal_ID"]
            is_locked = row["Approval"] == "Approved"

            with st.container(border=True):
                lock_label = "🔒 Locked (Approved)" if is_locked else ""
                st.markdown(f"**{row['Title']}** ({row['Thrust_Area']}) {lock_label}")

                c1, c2, c3 = st.columns(3)
                with c1:
                    new_status = st.selectbox(
                        "Status",
                        ["Not Started", "On Track", "Completed"],
                        key=f"stat_{goal_id}",
                        index=["Not Started", "On Track", "Completed"].index(row["Status"]),
                        # FIX: Disable editing on approved goals
                        disabled=is_locked
                    )
                with c2:
                    new_act = st.number_input(
                        f"Actual (Target: {row['Target']})",
                        min_value=0.0,
                        value=float(row["Q1_Actual"]),
                        key=f"act_input_{goal_id}",
                        # FIX: Disable editing on approved goals
                        disabled=is_locked
                    )
                with c3:
                    calc_score = calculate_progress_score(row["UoM"], row["Target"], new_act)
                    st.metric("Computed Score", f"{calc_score:.1f}%")

                if not is_locked:
                    if st.button("Save Progress", key=f"save_prog_{goal_id}", type="secondary"):
                        pending_saves[goal_id] = {
                            "Status": new_status,
                            "Q1_Actual": new_act
                        }

        # FIX: Apply all saves after the loop, then rerun once
        if pending_saves:
            for gid, changes in pending_saves.items():
                update_goal_by_id(gid, changes)
            st.toast("Progress saved!", icon="✅")
            st.rerun()


# --- JOURNEY B: MANAGER (L1) WORKSPACE ---
elif persona == "Manager View (L1)":
    st.markdown('<p class="brand-header">👔 Manager Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="brand-sub">Verify goals and conduct quarterly check-ins.</p>', unsafe_allow_html=True)

    mgr_tab1, mgr_tab2 = st.tabs(["✔️ Goal Approvals", "💬 Quarterly Check-ins"])

    with mgr_tab1:
        pending_sheets = st.session_state.goals_db[
            st.session_state.goals_db["Approval"] == "Submitted"
        ].copy()

        if pending_sheets.empty:
            st.info("✨ Clean Queue: No pending reviews.")
        else:
            for _, row in pending_sheets.iterrows():
                goal_id = row["Goal_ID"]
                with st.container(border=True):
                    st.write(f"**{row['Emp_Name']}** | {row['Title']} ({row['Weightage']}%)")

                    draft_app_key = f"draft_app_{goal_id}"
                    if draft_app_key not in st.session_state:
                        st.session_state[draft_app_key] = ""

                    comment_text = st.text_input(
                        "Manager Approval Note",
                        value=st.session_state[draft_app_key],
                        key=f"mgr_app_com_{goal_id}"
                    )
                    st.session_state[draft_app_key] = comment_text

                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("Approve & Lock", key=f"app_{goal_id}", type="primary"):
                            # FIX: Goal_ID-based update
                            update_goal_by_id(goal_id, {
                                "Approval": "Approved",
                                "Manager_Note": comment_text
                            })
                            st.session_state[draft_app_key] = ""
                            st.toast("Goal locked and approved.", icon="🔒")
                            st.rerun()
                    with col_btn2:
                        if st.button("Return for Rework", key=f"rej_{goal_id}"):
                            # FIX: Goal_ID-based update
                            update_goal_by_id(goal_id, {
                                "Approval": "Pending",
                                "Manager_Note": comment_text
                            })
                            st.session_state[draft_app_key] = ""
                            st.toast("Returned to employee.", icon="↩️")
                            st.rerun()

    with mgr_tab2:
        approved_goals = st.session_state.goals_db[
            st.session_state.goals_db["Approval"] == "Approved"
        ].copy()

        pending_checkin = approved_goals[approved_goals["Checkin_Feedback"] == ""]
        done_checkin = approved_goals[approved_goals["Checkin_Feedback"] != ""]

        if pending_checkin.empty:
            st.info("✨ Complete: All approved goals have been finalized with structured check-in notes.")
        else:
            for _, row in pending_checkin.iterrows():
                goal_id = row["Goal_ID"]
                with st.container(border=True):
                    st.markdown(f"**{row['Emp_Name']}** | {row['Title']}")
                    current_score = calculate_progress_score(row["UoM"], row["Target"], row["Q1_Actual"])
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Target", f"{row['Target']}")
                    c2.metric("Logged Actual", row["Q1_Actual"])
                    c3.metric("Score", f"{current_score:.1f}%")

                    draft_chk_key = f"draft_checkin_{goal_id}"
                    if draft_chk_key not in st.session_state:
                        st.session_state[draft_chk_key] = ""

                    checkin_comment = st.text_area(
                        "Q1 Check-in Feedback (Required)",
                        value=st.session_state[draft_chk_key],
                        key=f"chk_com_{goal_id}"
                    )
                    st.session_state[draft_chk_key] = checkin_comment

                    if st.button("Save Official Review", key=f"save_chk_{goal_id}", type="primary"):
                        if not checkin_comment.strip():
                            st.warning("⚠️ Feedback comments cannot be completely empty.")
                        else:
                            # FIX: Goal_ID-based update
                            update_goal_by_id(goal_id, {"Checkin_Feedback": checkin_comment})
                            st.session_state[draft_chk_key] = ""
                            st.toast("Check-in logged securely.", icon="💾")
                            st.rerun()

        # FIX: Show completed reviews in a read-only expander
        if not done_checkin.empty:
            with st.expander(f"✅ Completed Reviews ({len(done_checkin)})", expanded=False):
                for _, row in done_checkin.iterrows():
                    with st.container(border=True):
                        st.markdown(f"**{row['Emp_Name']}** | {row['Title']}")
                        st.info(f"💬 {row['Checkin_Feedback']}")


# --- JOURNEY C: HR / ADMIN ENGINE ---
else:
    st.markdown('<p class="brand-header">🛡️ Admin Control Center</p>', unsafe_allow_html=True)
    st.markdown('<p class="brand-sub">System governance, analytics, and rule enforcement.</p>', unsafe_allow_html=True)

    hr_tab1, hr_tab2, hr_tab3, hr_tab4 = st.tabs([
        "📊 KPI Dashboard", "📈 Analytics", "📥 Export Ledger", "⭐ Escalations"
    ])

    with hr_tab1:
        st.subheader("Q1 Check-in Completion")
        total_goals = len(st.session_state.goals_db)
        completed_reviews = len(st.session_state.goals_db[
            st.session_state.goals_db["Checkin_Feedback"] != ""
        ])
        completion_rate = (completed_reviews / total_goals) * 100 if total_goals > 0 else 0.0

        dash_c1, dash_c2, dash_c3 = st.columns(3)
        dash_c1.metric("Total Goals Tracked", total_goals)
        dash_c2.metric("Check-ins Finalized", completed_reviews)
        dash_c3.metric("Org Completion Rate", f"{completion_rate:.1f}%")

        st.progress(completion_rate / 100)
        st.dataframe(
            st.session_state.goals_db[[
                "Emp_Name", "Title", "Status", "Approval", "Checkin_Feedback"
            ]],
            use_container_width=True,
            hide_index=True
        )

    with hr_tab2:
        # FIX: Guard charts against empty dataframe
        if st.session_state.goals_db.empty:
            st.info("No goal data available to chart yet.")
        else:
            c_m1, c_m2 = st.columns(2)
            with c_m1:
                fig1 = px.pie(
                    st.session_state.goals_db,
                    names="Thrust_Area",
                    title="Goals by Thrust Area",
                    hole=0.4
                )
                fig1.update_layout(legend=dict(bgcolor="rgba(0,0,0,0)"))
                st.plotly_chart(fig1, use_container_width=True)
            with c_m2:
                fig2 = px.histogram(
                    st.session_state.goals_db,
                    x="Status",
                    color="Status",
                    title="Status Distribution"
                )
                fig2.update_layout(legend=dict(bgcolor="rgba(0,0,0,0)"))
                st.plotly_chart(fig2, use_container_width=True)

    with hr_tab3:
        st.info("System Audit Trail: Active.")
        csv_buffer = st.session_state.goals_db.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Export Master Data (CSV)",
            data=csv_buffer,
            file_name="Master_Ledger.csv",
            mime="text/csv",
            type="primary"
        )

    with hr_tab4:
        st.subheader("System Escalations")

        days_elapsed = st.slider("Simulate Days Elapsed (Demo Mode)", 0, 30, 0)

        # FIX: Escalation log persists in session_state, not recomputed fresh each render
        new_escalations = []
        for _, row in st.session_state.goals_db.iterrows():
            if row["Approval"] == "Pending" and days_elapsed >= 10:
                msg = f"EMPLOYEE ESCALATION: {row['Emp_Name']} has unsubmitted goal '{row['Title']}'"
                if msg not in st.session_state.escalation_log:
                    new_escalations.append(msg)
            if row["Approval"] == "Submitted" and days_elapsed >= 5:
                msg = f"MANAGER ESCALATION: '{row['Title']}' by {row['Emp_Name']} is stuck in review"
                if msg not in st.session_state.escalation_log:
                    new_escalations.append(msg)

        if new_escalations:
            st.session_state.escalation_log.extend(new_escalations)

        if st.session_state.escalation_log:
            for entry in st.session_state.escalation_log:
                if "EMPLOYEE" in entry:
                    st.error(f"⚠️ **{entry}**")
                else:
                    st.error(f"🚨 **{entry}**")
            if st.button("Clear Escalation Log"):
                st.session_state.escalation_log = []
                st.rerun()
        else:
            st.success("✔️ All workflows are within acceptable SLAs.")
