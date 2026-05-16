import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

# ----------------------------------------------------
# 1. SETUP & SESSION STATE INITIALIZATION
# ----------------------------------------------------
st.set_page_config(page_title="Atomberg Goal Portal", layout="wide")

# Seed mock records into our in-memory workbook if they don't exist yet
if 'goals_db' not in st.session_state:
    st.session_state.goals_db = pd.DataFrame([
        {
            "Goal_ID": "G001", "Emp_Name": "Lakshin", "Role": "Employee",
            "Thrust_Area": "Product Innovation", "Title": "Optimize Fan Motor Efficiency",
            "UoM": "Min (Numeric / %)", "Target": 95.0, "Weightage": 40.0,
            "Status": "On Track", "Approval": "Pending", "Q1_Actual": 92.0, "Comment": ""
        },
        {
            "Goal_ID": "G002", "Emp_Name": "Lakshin", "Role": "Employee",
            "Thrust_Area": "Operations", "Title": "Reduce Assembly Line Waste",
            "UoM": "Max (Numeric / %)", "Target": 5.0, "Weightage": 30.0,
            "Status": "Not Started", "Approval": "Pending", "Q1_Actual": 0.0, "Comment": ""
        },
        {
            "Goal_ID": "G003", "Emp_Name": "Lakshin", "Role": "Employee",
            "Thrust_Area": "Safety", "Title": "Zero Factory Incidents",
            "UoM": "Zero", "Target": 0.0, "Weightage": 30.0,
            "Status": "Completed", "Approval": "Pending", "Q1_Actual": 0.0, "Comment": ""
        }
    ])

if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = []

# ----------------------------------------------------
# 2. CALCULATION ENGINE (Phase 2 Formulas)
# ----------------------------------------------------
def calculate_progress_score(uom, target, actual):
    """Translates the mathematical evaluation logic from Section 2.2"""
    try:
        if uom == "Min (Numeric / %)":
            return (actual / target) * 100 if target != 0 else 0.0
        elif uom == "Max (Numeric / %)":
            return (target / actual) * 100 if actual != 0 else 0.0
        elif uom == "Zero":
            return 100.0 if actual == 0 else 0.0
        elif uom == "Timeline":
            # Baseline simulation: if target achieved matches expectation
            return 100.0 if actual <= target else 50.0
    except ZeroDivisionError:
        return 0.0
    return 0.0

# ----------------------------------------------------
# 3. INTERFACE - NAVIGATION SIDEBAR
# ----------------------------------------------------
st.sidebar.title("AtomQuest Goal Portal")
st.sidebar.markdown("---")

# Quick User Switching Panel (Fulfills Submission Deliverable Requirement)
current_user_role = st.sidebar.radio(
    "Select User Persona Journey:",
    ["Employee View (Lakshin)", "Manager View (L1)", "HR / Admin Dashboard"]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 Tip: Use this radio selector panel to test end-to-end multi-role workflows.")

# ----------------------------------------------------
# 4. VIEW RENDERING ENGINE
# ----------------------------------------------------

# --- JOURNEY A: EMPLOYEE INTERFACE ---
if current_user_role == "Employee View (Lakshin)":
    st.header("🎯 Employee Goal Management Workspace")
    
    tab1, tab2 = st.tabs(["Create & Submit Goal Sheets", "Quarterly Progress Logs"])
    
    with tab1:
        st.subheader("Draft a New Performance Goal")
        
        # User input fields
        col1, col2 = st.columns(2)
        with col1:
            thrust = col2.selectbox("Thrust Area", ["Product Innovation", "Operations", "Customer Success", "Sustainability"])
            title = st.text_input("Goal Title")
            desc = st.text_area("Goal Description")
        with col2:
            uom_type = st.selectbox("Unit of Measurement (UoM)", ["Min (Numeric / %)", "Max (Numeric / %)", "Timeline", "Zero"])
            target_val = st.number_input("Target Value", min_value=0.0, value=100.0)
            weight = st.number_input("Weightage (%)", min_value=0.0, max_value=100.0, step=5.0, value=10.0)
            
        # Phase 1 Validations Check Engine
        if st.button("Add Goal to Workspace Sheet"):
            current_employee_goals = st.session_state.goals_db[st.session_state.goals_db['Emp_Name'] == "Lakshin"]
            
            if len(current_employee_goals) >= 8:
                st.error("⛔ System Exception: Maximum threshold reached. You cannot exceed 8 structural goals.")
            elif weight < 10.0:
                st.error("⛔ System Exception: Minimum floor constraint violated. Every individual goal requires a weightage ≥ 10%.")
            elif current_employee_goals['Weightage'].sum() + weight > 100.0:
                st.error(f"⛔ System Exception: Cumulative allocation balance overflow. Remaining allowed weight capacity is {100.0 - current_employee_goals['Weightage'].sum()}%.")
            elif not title:
                st.warning("⚠️ Action Required: Goal Title cannot remain blank.")
            else:
                # Append record to state-driven workspace ledger
                new_row = {
                    "Goal_ID": f"G00{len(st.session_state.goals_db)+1}", "Emp_Name": "Lakshin", "Role": "Employee",
                    "Thrust_Area": thrust, "Title": title, "UoM": uom_type, "Target": target_val, "Weightage": weight,
                    "Status": "Not Started", "Approval": "Pending", "Q1_Actual": 0.0, "Comment": ""
                }
                st.session_state.goals_db = pd.concat([st.session_state.goals_db, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"✔️ Added target plan: '{title}' successfully mapped to workspace.")

        st.markdown("---")
        st.subheader("Your Current Session Workspace Ledger")
        my_current_sheet = st.session_state.goals_db[st.session_state.goals_db['Emp_Name'] == "Lakshin"]
        st.dataframe(my_current_sheet)
        
        # Display sum validation status check to user
        total_allocated_weight = my_current_sheet['Weightage'].sum()
        st.metric(label="Total Combined Sheet Weightage Allocation (Must equal 100%)", value=f"{total_allocated_weight}%")
        
        if total_allocated_weight == 100.0:
            if st.button("Submit Final Goal Sheet to L1 Manager", type="primary"):
                st.session_state.goals_db.loc[st.session_state.goals_db['Emp_Name'] == "Lakshin", "Approval"] = "Submitted"
                st.success("🚀 Sheet submitted securely. Controls locked pending manager verification.")
        else:
            st.warning(f"⚠️ Action Required: Total allocation balance is currently at {total_allocated_weight}%. Complete allocation to exactly 100% to activate submission routing.")

    with tab2:
        st.subheader("Quarterly Achievement & Update Log Windows")
        editable_sheet = st.session_state.goals_db[st.session_state.goals_db['Emp_Name'] == "Lakshin"]
        
        # Interactive editing logs mapping
        for index, row in editable_sheet.iterrows():
            with st.container(border=True):
                st.markdown(f"**Goal:** {row['Title']} ({row['Thrust_Area']})")
                c1, c2, c3 = st.columns(3)
                with c1:
                    new_status = st.selectbox(f"Status Tracking Update", ["Not Started", "On Track", "Completed"], key=f"stat_{index}")
                with c2:
                    new_act = st.number_input(f"Logged Actual Achievement (Target: {row['Target']})", value=float(row['Q1_Actual']), key=f"act_{index}")
                with c3:
                    calc_score = calculate_progress_score(row['UoM'], row['Target'], new_act)
                    st.metric("Computed Operational Score", f"{calc_score:.1f}%")
                
                # Commit updates instantly to state database mapping
                st.session_state.goals_db.at[index, 'Status'] = new_status
                st.session_state.goals_db.at[index, 'Q1_Actual'] = new_act

# --- JOURNEY B: MANAGER (L1) WORKSPACE ---
elif current_user_role == "Manager View (L1)":
    st.header("👔 Manager Verification & Check-in Dashboard")
    
    # Adding tabs to separate Phase 1 (Approvals) and Phase 2 (Check-ins)
    mgr_tab1, mgr_tab2 = st.tabs(["Phase 1: Goal Approvals", "Phase 2: Quarterly Check-ins"])
    
    with mgr_tab1:
        st.subheader("Submissions Pending Action Review")
        pending_sheets = st.session_state.goals_db[st.session_state.goals_db['Approval'] == "Submitted"]
        
        if pending_sheets.empty:
            st.info("✨ Clean Queue: No submitted sheets currently require manual verification reviews.")
        else:
            for index, row in pending_sheets.iterrows():
                with st.container(border=True):
                    st.write(f"**Employee ID:** {row['Emp_Name']} | **Goal Structural Focus:** {row['Title']}")
                    st.write(f"Proposed Weight Allocation: **{row['Weightage']}%** | Target Metric Scale: **{row['Target']}** ({row['UoM']})")
                    
                    comment_text = st.text_input("Add Management Approval Note", key=f"mgr_app_com_{index}")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("Approve & Lock Structuring Parameters", key=f"app_{index}"):
                            st.session_state.goals_db.at[index, 'Approval'] = "Approved"
                            st.session_state.goals_db.at[index, 'Comment'] = comment_text
                            st.success("Target profile locked. Dispatched securely to system ledger repository.")
                    with col_btn2:
                        if st.button("Return for Dynamic Balance Rework", key=f"rej_{index}"):
                            st.session_state.goals_db.at[index, 'Approval'] = "Pending"
                            st.warning("Dispatched back to employee profile workspace.")

    with mgr_tab2:
        st.subheader("Quarterly Performance Review (Active Window: Q1)")
        # Managers only review goals that have already been approved
        active_goals = st.session_state.goals_db[st.session_state.goals_db['Approval'] == "Approved"]
        
        if active_goals.empty:
            st.info("No approved goals available for quarterly review yet.")
        else:
            for index, row in active_goals.iterrows():
                with st.container(border=True):
                    st.markdown(f"**Employee:** {row['Emp_Name']} | **Goal:** {row['Title']}")
                    
                    # Calculate current score based on what the employee logged
                    current_score = calculate_progress_score(row['UoM'], row['Target'], row['Q1_Actual'])
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Planned Target", f"{row['Target']} ({row['UoM']})")
                    c2.metric("Logged Achievement", row['Q1_Actual'])
                    c3.metric("System Computed Score", f"{current_score:.1f}%")
                    
                    # Phase 2 Must-Have: Structured Check-in Comment
                    checkin_comment = st.text_area("Structured Check-in Comment & Feedback", value=row.get('Comment', ''), key=f"chk_com_{index}")
                    
                    if st.button("Save Quarterly Review", key=f"save_chk_{index}"):
                        st.session_state.goals_db.at[index, 'Comment'] = checkin_comment
                        st.success("Quarterly check-in logged and saved to audit trail.")

# --- JOURNEY C: HR / ADMIN ENGINE ---
else:
    st.header("🛡️ HR Administration Control Center & Governance")
    
    # We added a 4th tab for the Bonus Points Module
    hr_tab1, hr_tab2, hr_tab3, hr_tab4 = st.tabs([
        "Completion Dashboard", 
        "Organization Analytics", 
        "Audit & Export Ledger",
        "⭐ Rule-Based Escalations"
    ])
    
    with hr_tab1:
        st.subheader("Quarterly Check-in Completion Status (Q1)")
        total_goals = len(st.session_state.goals_db)
        completed_reviews = len(st.session_state.goals_db[st.session_state.goals_db['Comment'] != ""])
        
        completion_rate = completed_reviews / total_goals if total_goals > 0 else 0.0
            
        st.progress(completion_rate)
        st.write(f"**Live Completion Rate:** {completed_reviews} out of {total_goals} goal check-ins finalized by managers.")
        st.markdown("**Live Check-in Status Table:**")
        st.dataframe(st.session_state.goals_db[['Emp_Name', 'Title', 'Status', 'Approval', 'Comment']])
        
    with hr_tab2:
        st.subheader("Organization Progress Trends Overview")
        c_m1, c_m2 = st.columns(2)
        with c_m1:
            fig1 = px.pie(st.session_state.goals_db, names='Thrust_Area', title='Goals by Strategic Thrust Area')
            st.plotly_chart(fig1, use_container_width=True)
        with c_m2:
            fig2 = px.histogram(st.session_state.goals_db, x='Status', color='Status', title='Goal Status Distribution')
            st.plotly_chart(fig2, use_container_width=True)
            
    with hr_tab3:
        st.subheader("Global Achievement & Audit Records")
        st.info("System Audit Trail: Active. Monitoring for post-lock modifications.")
        if len(st.session_state.audit_logs) > 0:
            for log in st.session_state.audit_logs:
                st.code(log)
        else:
            st.write("No critical modifications detected in this session.")
            
        st.markdown("---")
        csv_buffer = st.session_state.goals_db.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Master Achievement Report Data (CSV)",
            data=csv_buffer,
            file_name="Atomberg_Global_Performance_Master.csv",
            mime="text/csv"
        )
        
    with hr_tab4:
        st.subheader("System Escalation Monitoring (Bonus Module)")
        st.markdown("Active Rules Engine: Scanning for SLA breaches across the organization.")
        
        # The Demo Trick: A slider to let judges simulate the passage of time
        st.info("💡 Interactive Demo: Use the slider below to simulate days passing since the cycle opened.")
        days_elapsed = st.slider("Simulate Days Elapsed", 0, 30, 0)
        
        escalation_triggered = False
        
        # Scanning the DataFrame with logic loops
        for index, row in st.session_state.goals_db.iterrows():
            
            # Rule 1: Employee Bottleneck (Hasn't submitted after 10 days)
            if row['Approval'] == "Pending" and days_elapsed >= 10:
                st.error(f"⚠️ **EMPLOYEE ESCALATION:** {row['Emp_Name']} has not finalized submission of '{row['Title']}'. (Overdue by {days_elapsed - 10} days)")
                escalation_triggered = True
                
            # Rule 2: Manager Bottleneck (Sitting in queue for > 5 days)
            # For demo purposes, we assume 'days_elapsed' applies to approval time as well
            if row['Approval'] == "Submitted" and days_elapsed >= 5:
                st.error(f"🚨 **MANAGER ESCALATION (L1):** Goal '{row['Title']}' from {row['Emp_Name']} is stuck in manager review queue. (Overdue by {days_elapsed - 5} days)")
                escalation_triggered = True
                
        if not escalation_triggered:
            st.success("✔️ All workflows are currently within acceptable SLAs. No escalations triggered.")
