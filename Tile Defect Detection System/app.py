# ============================================================
# TILE DEFECT DETECTION SYSTEM
# ------------------------------------------------------------
# Features:
# - Dark mode UI
# - Signup & Login (JSON based)
# - Image upload + camera capture
# - Crack & spot detection (OpenCV)
# - Per-user inspection history
# - Visualization dashboard
# - Excel export
# - Sign out option
# ============================================================

import streamlit as st
import cv2
import numpy as np
import pandas as pd
import os
import io
from datetime import datetime
import matplotlib.pyplot as plt
import hashlib

#----for prevent repiding data----
def get_image_hash(img):
    img_small = cv2.resize(img, (64, 64))
    return hashlib.md5(img_small.tobytes()).hexdigest()

# Authentication functions
from auth import login, signup

# Image processing logic
from utils import inspect_tile

# ============================================================
# CREATE REQUIRED FOLDERS (auto if not exist)
# ============================================================

os.makedirs("inspection_data", exist_ok=True)   # per-user CSV
os.makedirs("output_tiles", exist_ok=True)      # saved images
os.makedirs("defective_tiles", exist_ok=True)   # bad tiles


# ============================================================
# STREAMLIT PAGE CONFIGURATION
# ============================================================

st.set_page_config(layout="wide")

# Dark-mode CSS styling
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background-color:#0f172a;
    color:white;
}
[data-testid="stSidebar"] {
    background-color:#020617;
}
h1,h2,h3 { color:#e5e7eb; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION VARIABLES
# ============================================================

# Tracks login state
if "login" not in st.session_state:
    st.session_state["login"] = False

# Controls history visibility
if "show_history" not in st.session_state:
    st.session_state["show_history"] = False

# Controls visualization visibility
if "show_visual" not in st.session_state:
    st.session_state["show_visual"] = False

if "show_tiles" not in st.session_state:
    st.session_state["show_tiles"] = False

if "processed" not in st.session_state:
    st.session_state["processed"] = False

if "last_image_hash" not in st.session_state:
    st.session_state["last_image_hash"] = None

# ============================================================
# LOGIN / SIGNUP SCREEN
# ============================================================

# If user not logged in → show login/signup
if not st.session_state["login"]:

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        login()

    with tab2:
        signup()

    # Stop app execution here
    st.stop()



# ============================================================
# MAIN APPLICATION AFTER LOGIN
# ============================================================

# ============================================================
# LOAD USER CONTEXT SAFELY (FIX KPI = 0 ISSUE)
# ============================================================

username = st.session_state.get("user", None)

if username:
    user_csv = f"inspection_data/{username}.csv"
else:
    user_csv = None


st.title("🧱 Tile Defect Detection System")
# ============================================================
# SIDEBAR KPI TOGGLE
# ============================================================
st.sidebar.markdown("## 📊 Production Dashboard")
st.sidebar.markdown("## ⚙️ Dashboard Controls")
show_kpi = st.sidebar.toggle("📈 Show Production KPI", value=True)

# ============================================================
# KPI + DAILY PRODUCTION CHART (MATPLOTLIB)
# ============================================================

if show_kpi and user_csv and os.path.exists(user_csv):


    df = pd.read_csv(user_csv)

    # safe datetime parse
    df["DateTime"] = pd.to_datetime(
    df["Time"],
    format="mixed",
    dayfirst=True,
    errors="coerce"
    )


    df = df.dropna(subset=["DateTime"])

    df["DateTime"] = pd.to_datetime(df["Time"], errors="coerce")

    today = datetime.now().date()
    df_today = df[df["DateTime"].dt.date == today]



    # ---------------------------
    # KPI CALCULATION
    # ---------------------------
    total_tiles = len(df_today)
    defective_tiles = (df_today["Result"] == "DEFECTIVE").sum()
    good_tiles = (df_today["Result"] == "GOOD").sum()
    
    defect_rate = round(
        (defective_tiles / total_tiles) * 100, 2
    ) if total_tiles > 0 else 0.0
    
    

    # ---------------------------
    # KPI DISPLAY
    # ---------------------------
    st.subheader("📊 Today Production KPI Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("🧱 Total Tiles Today", total_tiles)
    col2.metric("❌ Defective Tiles", defective_tiles)
    col3.metric("✅ Good Tiles", good_tiles)
    col4.metric("📉 Defect Rate", f"{defect_rate:.2f}%")

    # ============================================================
    # DAILY PRODUCTION GROUPED BAR CHART
    # ============================================================

    st.subheader("📊 Daily Tile Production (Good vs Defective)")

    # Group data by date
    daily = (
        df.groupby(df["DateTime"].dt.date)
        .agg(
            Good=("Result", lambda x: (x == "GOOD").sum()),
            Defective=("Result", lambda x: (x == "DEFECTIVE").sum())
        )
    )

    # X-axis labels (date-month)
    dates = [d.strftime("%d-%m") for d in daily.index]

    x = np.arange(len(dates))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))

    # GOOD tiles (blue)
    ax.bar(
        x - width/2,
        daily["Good"],
        width,
        label="Good Tiles",
        color="royalblue"
    )

    # DEFECTIVE tiles (red)
    ax.bar(
        x + width/2,
        daily["Defective"],
        width,
        label="Defective Tiles",
        color="red"
    )

    ax.set_xlabel("Date - Month")
    ax.set_ylabel("Number of Tiles")
    ax.set_title("Daily Tile Production Report")

    ax.set_xticks(x)
    ax.set_xticklabels(dates)

    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    st.pyplot(fig)

#-------------------------------------

st.session_state["show_history"] = st.sidebar.toggle(
    "📁 Show Inspection History",
    value=st.session_state["show_history"]
)

st.session_state["show_visual"] = st.sidebar.toggle(
    "📊 Show Visualization",
    value=st.session_state["show_visual"]
)

st.session_state["show_tiles"] = st.sidebar.toggle(
    "🧱 Show All Tiles",
    value=st.session_state["show_tiles"]
)


st.sidebar.success(f"👤 Logged in as: {username}")

# ============================================================
# IMAGE INPUT METHOD
# ============================================================

# Choose input source
mode = st.radio(
    "Select Input Method",
    ["Upload Image", "Camera Capture"]
)




# ---------- Upload Image ----------
if mode == "Upload Image":

    file = st.file_uploader("Upload tile image", ["jpg", "png", "jpeg"])

    if file:
        file_bytes = np.asarray(bytearray(file.read()), dtype=np.uint8)
        st.session_state["image"] = cv2.imdecode(file_bytes, 1)

# ---------- Camera Capture ----------
else:

    cam = st.camera_input("Capture tile image")

    if cam:
        cam_bytes = np.asarray(bytearray(cam.read()), dtype=np.uint8)
        st.session_state["image"] = cv2.imdecode(cam_bytes, 1)

image = st.session_state.get("image", None)
# ============================================================
# IMAGE PROCESSING
# ============================================================
# ============================================================
# IMAGE PROCESSING (HASH SAFE — NO DUPLICATES)
# ============================================================

if image is not None and image.size != 0:

    current_hash = get_image_hash(image)

    if current_hash != st.session_state["last_image_hash"]:

        st.session_state["last_image_hash"] = current_hash

        # -------------------------------
        # INSPECT TILE
        # -------------------------------
        output, crack, spots, defect, result = inspect_tile(image)

        # store for UI
        st.session_state["output"] = output
        st.session_state["crack"] = crack
        st.session_state["spots"] = spots
        st.session_state["defect"] = defect
        st.session_state["result"] = result

        # -------------------------------
        # SAVE IMAGES
        # -------------------------------
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        date_folder = datetime.now().strftime("%d-%m-%Y")

        input_path = f"output_tiles/{username}_input_{timestamp}.jpg"
        output_path = f"output_tiles/{username}_output_{timestamp}.jpg"

        cv2.imwrite(input_path, image)
        cv2.imwrite(output_path, output)

        if result == "DEFECTIVE":
            defect_dir = os.path.join(
                "defective_tiles", username, date_folder
            )
            os.makedirs(defect_dir, exist_ok=True)

            cv2.imwrite(
                os.path.join(defect_dir, f"defective_{timestamp}.jpg"),
                output
            )

        # -------------------------------
        # SAVE CSV
        # -------------------------------
        record = {
        # ISO timestamp → KPI safe forever
        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Crack(mm)": round(crack, 2),
        "Spots": spots,
        "Defect %": round(defect, 2),
        "Result": result
        }


        df_new = pd.DataFrame([record])

        if os.path.exists(user_csv):
            df_old = pd.read_csv(user_csv)
            df = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df = df_new

        df.to_csv(user_csv, index=False)
# ============================================================
# DISPLAY LAST INSPECTION RESULT
# ============================================================

if "result" in st.session_state:

    output = st.session_state["output"]
    crack = st.session_state["crack"]
    spots = st.session_state["spots"]
    defect = st.session_state["defect"]
    result = st.session_state["result"]

    col1, col_mid, col2 = st.columns([5, 0.3, 5])

    with col1:
        st.image(image, channels="BGR", caption="Input Image")

    with col_mid:
        st.markdown(
            "<div style='border-left:4px solid #38bdf8;height:300px;'></div>",
            unsafe_allow_html=True
        )

    with col2:
        st.image(output, channels="BGR", caption="Processed Image")

    st.warning("⚠️ Tiles with fewer than 3 detected spots are classified as GOOD.")
    if result == "DEFECTIVE":
        st.error("❌ DEFECTIVE TILE")
    else:
        st.success("✅ GOOD TILE")
# ============================================================
# INSPECTION DETAILS EXPANDER (SAFE)
# ============================================================

if "result" in st.session_state:

    with st.expander("🔍 View Inspection Details"):

        col_a, col_b = st.columns(2)

        col_a.metric(
            "📏 Crack Length (mm)",
            f"{st.session_state['crack']:.2f}"
        )

        col_a.metric(
            "⚫ Spot Count",
            st.session_state["spots"]
        )

        col_b.metric(
            "🧮 Defect Percentage",
            f"{st.session_state['defect']:.2f}%"
        )

        col_b.metric(
            "🧱 Tile Status",
            st.session_state["result"]
        )


# ============================================================
# INSPECTION HISTORY TABLE
# ============================================================

if st.session_state["show_history"]:

    st.subheader("📁 Inspection History")

    if os.path.exists(user_csv):

        df = pd.read_csv(user_csv)


        # ------------------------------------------------
        # Re-create tile numbering every time
        # ------------------------------------------------
        df.insert(0, "Tile No", range(1, len(df) + 1))

        # ------------------------------------------------
        # Show interactive table with images
        # ------------------------------------------------
        edited_df = st.data_editor(
            df,
            column_config={
                "Input Image": st.column_config.ImageColumn(
                    "Input Image",
                    width="medium"
                ),
                "Output Image": st.column_config.ImageColumn(
                    "Output Image",
                    width="medium"
                )
            },
            hide_index=True,
            use_container_width=True
        )

    else:
        st.info("No inspection data available.")



# =====================================
# VISUALIZATION (ATTRACTIVE MATPLOTLIB)
# =====================================

if st.session_state["show_visual"]:

    if os.path.exists(user_csv):

        df = pd.read_csv(user_csv)
        df["Tile No"] = range(1, len(df) + 1)

        st.subheader("📊 Tile Inspection Analytics Dashboard")

        fig, axs = plt.subplots(2, 2, figsize=(14, 10))

        # -------------------------------------
        # GOOD vs DEFECTIVE (COLORED BAR)
        # -------------------------------------
        counts = df["Result"].value_counts()

        colors = ["#22c55e" if x == "GOOD" else "#ef4444" for x in counts.index]

        axs[0, 0].bar(counts.index, counts.values, color=colors)
        axs[0, 0].set_title("Good vs Defective Tiles", fontweight="bold")
        axs[0, 0].set_xlabel("Category")
        axs[0, 0].set_ylabel("Count")
        axs[0, 0].grid(axis="y", linestyle="--", alpha=0.3)

        # -------------------------------------
        # DEFECT % (GRADIENT BAR)
        # -------------------------------------
        axs[0, 1].bar(
            df["Tile No"],
            df["Defect %"],
            color="#f97316"
        )
        axs[0, 1].set_title("Defect % per Tile", fontweight="bold")
        axs[0, 1].set_xlabel("Tile Number")
        axs[0, 1].set_ylabel("Defect %")
        axs[0, 1].grid(axis="y", linestyle="--", alpha=0.3)

        # -------------------------------------
        # CRACK LENGTH (AREA + LINE)
        # -------------------------------------
        axs[1, 0].plot(
            df["Tile No"],
            df["Crack(mm)"],
            marker="o",
            linewidth=2
        )
        axs[1, 0].fill_between(
            df["Tile No"],
            df["Crack(mm)"],
            alpha=0.3
        )
        axs[1, 0].set_title("Crack Length Trend", fontweight="bold")
        axs[1, 0].set_xlabel("Tile Number")
        axs[1, 0].set_ylabel("Crack Length (mm)")
        axs[1, 0].grid(True, alpha=0.3)

        # -------------------------------------
        # SPOT COUNT (AREA + LINE)
        # -------------------------------------
        axs[1, 1].plot(
            df["Tile No"],
            df["Spots"],
            marker="o",
            linewidth=2
        )
        axs[1, 1].fill_between(
            df["Tile No"],
            df["Spots"],
            alpha=0.3
        )
        axs[1, 1].set_title("Spot Count Trend", fontweight="bold")
        axs[1, 1].set_xlabel("Tile Number")
        axs[1, 1].set_ylabel("Spots")
        axs[1, 1].grid(True, alpha=0.3)

        # spacing
        plt.subplots_adjust(
            left=0.08,
            right=0.97,
            top=0.95,
            bottom=0.08,
            hspace=0.35,
            wspace=0.25
        )

        st.pyplot(fig)

    else:
        st.info("No inspection data available.")

# ============================================================
# ALL TILES GALLERY (INPUT → OUTPUT)
# ============================================================

if st.session_state["show_tiles"]:

    st.subheader("🧱 All Tiles (Input → Output)")

    images = sorted(os.listdir("output_tiles"))

    input_imgs = [i for i in images if i.startswith(username + "_input")]
    output_imgs = [i for i in images if i.startswith(username + "_output")]

    for inp, out in zip(input_imgs, output_imgs):

        col1, col2 = st.columns(2)

        with col1:
            st.image(
                os.path.join("output_tiles", inp),
                caption="Input Tile",
                use_container_width=True
            )

        with col2:
            st.image(
                os.path.join("output_tiles", out),
                caption="Processed Tile",
                use_container_width=True
            )

        st.divider()


# ============================================================
# EXCEL EXPORT
# ============================================================

if user_csv and os.path.exists(user_csv):

    def convert_to_excel(dataframe):
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            dataframe.to_excel(writer, index=False)
        return buffer.getvalue()

    excel_data = convert_to_excel(pd.read_csv(user_csv))

    st.download_button(
        "⬇️ Download Excel Report",
        data=excel_data,
        file_name=f"{username}_inspection_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# ============================================================
# LOGOUT BUTTON
# ============================================================

st.divider()

if st.sidebar.button("🚪 Sign Out"):
    st.session_state["login"] = False
    st.session_state["user"] = ""
    st.session_state["show_history"] = False
    st.session_state["show_visual"] = False
    st.session_state.pop("image", None)
    st.session_state.pop("last_image_hash", None)
    st.session_state.pop("result", None)

    st.rerun()
