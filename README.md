
# APS Tool (Web Version)

This is a Streamlit-based web version of the APS Tool that was originally built as a desktop application using `tkinter`.

## 🔍 Features

- Collects user info and checklist data
- Loads base and matrix metadata from Excel
- Allows Excel report upload and preview
- Prepares for further analysis and PDF export (extendable)
- Ready to deploy on [Render](https://render.com)

---

## 📦 Project Structure

```
aps_web_app/
│
├── app.py                    # Main Streamlit app
├── requirements.txt          # Python dependencies
├── Precision_tables/
│   └── Database_base_matrix.xlsx  # Your metadata Excel (replace the dummy)
```

---

## 🚀 Deployment on Render

### 1. Upload to GitHub
Push this folder as a GitHub repository.

### 2. Deploy on Render
- Go to [Render](https://render.com)
- Click **New + > Web Service**
- Connect your GitHub repo
- Fill in the settings:

| Setting         | Value                 |
|----------------|-----------------------|
| Runtime         | Python 3              |
| Build Command   | `pip install -r requirements.txt` |
| Start Command   | `streamlit run app.py` |

### 3. Access App
Once deployed, open your Render app URL in Chrome or any browser.

---

## 🔧 Customize

- Replace `Precision_tables/Database_base_matrix.xlsx` with your actual metadata file.
- Add report analysis and export logic as per original desktop tool.

---

## 🛠️ Requirements

```
streamlit
pandas
numpy
openpyxl
```

---

## 👨‍💻 Author

Sunil Jadhav — [APS Tool Web Migration]

