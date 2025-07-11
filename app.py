import streamlit as st
import os
import shutil

# --- การตั้งค่าพื้นฐาน ---
BASE_DIR = "file_storage"
CATEGORIES = {
    "modrinth": {"name": "Modrinth Packs (.mrpack)", "path": os.path.join(BASE_DIR, "modrinth_packs"), "icon": "📦"},
    "curseforge": {"name": "CurseForge Packs (.zip)", "path": os.path.join(BASE_DIR, "curseforge_packs"), "icon": "🔥"},
    "other": {"name": "ไฟล์อื่นๆ", "path": os.path.join(BASE_DIR, "other_files"), "icon": "🗂️"}
}

# สร้างโฟลเดอร์หมวดหมู่ทั้งหมดถ้ายังไม่มี
for category in CATEGORIES.values():
    os.makedirs(category["path"], exist_ok=True)


# --- ฟังก์ชันจัดการไฟล์ ---

def display_files_in_category(category_key, is_admin=False):
    """แสดงไฟล์ในหมวดหมู่ที่กำหนด"""
    category = CATEGORIES[category_key]
    st.header(f"{category['icon']} {category['name']}")

    try:
        files = sorted(os.listdir(category['path']))
        if not files:
            st.info("ยังไม่มีไฟล์ในหมวดหมู่นี้")
            return

        for filename in files:
            file_path = os.path.join(category['path'], filename)
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # แปลงเป็น MB

                with open(file_path, "rb") as f:
                    file_bytes = f.read()

                cols = st.columns([0.5, 0.3, 0.2]) if is_admin else st.columns([0.7, 0.3])

                with cols[0]:
                    st.markdown(f"**{filename}**")
                    st.caption(f"ขนาด: {file_size:.2f} MB")

                with cols[1]:
                    st.download_button(
                        label="📥 ดาวน์โหลด",
                        data=file_bytes,
                        file_name=filename,
                        mime="application/octet-stream",
                        key=f"dl_{category_key}_{filename}"
                    )

                if is_admin:
                    with cols[2]:
                        if st.button("🗑️ ลบ", key=f"del_{category_key}_{filename}", type="primary"):
                            # ใช้ session_state เพื่อยืนยันการลบ
                            st.session_state.file_to_delete = {"path": file_path, "name": filename}
                            st.rerun()

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการแสดงไฟล์: {e}")


# --- หน้าเว็บแอปหลัก ---
st.set_page_config(page_title="Minecraft Pack Hub", page_icon="⛏️", layout="wide")

st.title("⛏️ Minecraft Pack & File Hub")
st.markdown("ศูนย์กลางสำหรับดาวน์โหลด Modpacks และไฟล์ต่างๆ ที่เกี่ยวข้อง")

# --- การจัดการสถานะล็อกอินและ Admin ---
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

with st.sidebar:
    st.header("🔐 สำหรับผู้ดูแล")
    if not st.session_state.is_admin:
        password = st.text_input("กรุณาใส่รหัสผ่าน", type="password")
        if st.button("เข้าสู่ระบบ"):
            # ใช้ st.secrets สำหรับการใช้งานจริง
            try:
                correct_password = st.secrets["ADMIN_PASSWORD"]
            except FileNotFoundError:
                # Fallback สำหรับการรันในเครื่อง (Local)
                st.warning("ไม่พบ Secrets, กำลังใช้รหัสผ่านสำรอง (ไม่ปลอดภัย)")
                correct_password = "admin123"

            if password == correct_password:
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("รหัสผ่านไม่ถูกต้อง")

    if st.session_state.is_admin:
        st.success("✔️ ล็อกอินในฐานะผู้ดูแล")

        st.header("⚙️ เมนูผู้ดูแล")

        # --- ส่วนอัปโหลดไฟล์ ---
        with st.expander("⬆️ อัปโหลดไฟล์ใหม่", expanded=True):
            category_options = {key: cat["name"] for key, cat in CATEGORIES.items()}
            chosen_category_key = st.selectbox("เลือกหมวดหมู่ที่จะอัปโหลดไป:", options=list(category_options.keys()),
                                               format_func=lambda key: category_options[key])

            uploaded_files = st.file_uploader("เลือกไฟล์", accept_multiple_files=True, key="uploader")

            if st.button("อัปโหลดไฟล์ที่เลือก"):
                if uploaded_files and chosen_category_key:
                    save_path_dir = CATEGORIES[chosen_category_key]['path']
                    success_count = 0
                    for uploaded_file in uploaded_files:
                        with open(os.path.join(save_path_dir, uploaded_file.name), "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        success_count += 1
                    st.success(f"อัปโหลด {success_count} ไฟล์ไปยัง '{category_options[chosen_category_key]}' สำเร็จ!")
                    # ไม่ต้อง rerun เพราะ uploader จะ trigger rerun เอง
                else:
                    st.warning("กรุณาเลือกไฟล์และหมวดหมู่ก่อนอัปโหลด")

        if st.button("ออกจากระบบผู้ดูแล"):
            st.session_state.is_admin = False
            # ล้าง state ที่ไม่จำเป็น
            if 'file_to_delete' in st.session_state:
                del st.session_state.file_to_delete
            st.rerun()

# --- การยืนยันการลบไฟล์ (Modal-like behavior) ---
if 'file_to_delete' in st.session_state and st.session_state.file_to_delete:
    file_info = st.session_state.file_to_delete
    with st.container():
        st.warning(f"คุณแน่ใจหรือไม่ว่าต้องการลบไฟล์: **{file_info['name']}** ?")
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("✅ ยืนยันการลบ", type="primary"):
                try:
                    os.remove(file_info['path'])
                    st.success(f"ลบไฟล์ '{file_info['name']}' สำเร็จ!")
                    del st.session_state.file_to_delete
                    st.rerun()
                except Exception as e:
                    st.error(f"ไม่สามารถลบไฟล์ได้: {e}")
        with col2:
            if st.button("❌ ยกเลิก"):
                del st.session_state.file_to_delete
                st.rerun()

# --- แสดงผลแท็บหลัก ---
tab1, tab2, tab3 = st.tabs([f"{cat['icon']} {cat['name']}" for cat in CATEGORIES.values()])

with tab1:
    display_files_in_category("modrinth", st.session_state.is_admin)

with tab2:
    display_files_in_category("curseforge", st.session_state.is_admin)

with tab3:
    display_files_in_category("other", st.session_state.is_admin)